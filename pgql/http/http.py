from graphql import GraphQLSchema, build_schema, graphql, GraphQLScalarType
from graphql.type.definition import GraphQLObjectType, GraphQLNonNull, GraphQLList, GraphQLInputObjectType
import uvicorn
import glob
import contextvars
from typing import Callable, Optional

from pgql.http.config_http_enum import ConfigHTTPEnum
from pgql.graphql.resolvers.base import Scalar, ScalarResolved
from pgql.graphql.directives import Directive
from pgql.graphql import GraphQLExecutor
from .config import HTTPConfig, RouteConfig
from .authorize_info import AuthorizeInfo
from .session import SessionStore, Session
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response, FileResponse
from starlette.requests import Request
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
import os

# Cache para evitar doble ejecución de assess() durante validación y ejecución
_scalar_cache: contextvars.ContextVar[dict] = contextvars.ContextVar('scalar_cache', default=None)

class HTTPServer:
    def __init__(self, configPath: str):
        self.__httpConfig = HTTPConfig(configPath)
        self.__app: Starlette = None
        self.__routes: list[Route] = []
        self.__mounts: list[Mount] = []  # Para montar aplicaciones ASGI adicionales
        self.__schemas: dict[str, GraphQLSchema] = {}
        self.__file_base_dir: str = ""  # Directorio base para archivos estáticos
        self.__on_authorize: Optional[Callable[[AuthorizeInfo], bool]] = None
        self.__on_http_check_origin: Optional[Callable[[str], bool]] = None  # Callback para validar orígenes CORS
        self.__resolvers: dict[str, type] = {}
        self.__session_store = SessionStore()  # Almacén de sesiones
        self.__scalars: dict[str, Scalar] = {}  # Registro de custom scalars
        self.__directives: dict[str, 'Directive'] = {}  # Registro de custom directives
        self.__executor: Optional[GraphQLExecutor] = None  # Ejecutor de GraphQL

        for route in self.__httpConfig.server.routes:
            match route.mode:
                case ConfigHTTPEnum.MODE_GQL:
                    schema = self.__load_schema(route.schema)
                    self.__schemas[route.endpoint] = schema
                    self.__routes.append(Route(route.endpoint, self.__gql_request_handler, methods=['POST']))
                case ConfigHTTPEnum.MODE_FILE:
                    self.__file_base_dir = route.path
                    # Añadir {path:path} para capturar cualquier archivo bajo el endpoint
                    file_route = f"{route.endpoint}/{{path:path}}"
                    self.__routes.append(Route(file_route, self.__file_handler, methods=['GET']))
                # case ConfigHTTPEnum.MODE_REST:
                #     async def rest_handler(request):
                #         return await self.rest_handler(request)
                #     self.__routes.append(Route(route.endpoint, rest_handler))

    async def __gql_request_handler(self, request: Request):
        """Handler de instancia para requests GraphQL"""
        return await self.__class__.gql_handler(
            self.__schemas,
            request,
            self.__session_store,
            self.__httpConfig.cookie_name
        )
    
    def __load_schema(self, schema_path: str) -> GraphQLSchema:
        schema_parts = []
        for file_path in glob.glob(schema_path + '/**/*.gql', recursive=True):
            with open(file_path, 'r') as f:
                schema_parts.append(f.read())

        full_schema = '\n'.join(schema_parts)
        schema = build_schema(full_schema)
        
        # Registrar custom scalars en el schema
        for scalar_name, scalar_instance in self.__scalars.items():
            if scalar_name in schema.type_map:
                # Crear wrapper para integrar con graphql-core
                def make_serialize(scalar_obj):
                    def serialize(value):
                        result, error = scalar_obj.set(value)
                        if error:
                            raise error
                        return result
                    return serialize
                
                def make_parse_value(scalar_obj):
                    def parse_value(value):
                        resolved = ScalarResolved(
                            value=value,
                            resolver_name='',
                            resolved=None
                        )
                        result, error = scalar_obj.assess(resolved)
                        if error:
                            raise error
                        return result
                    return parse_value
                
                def make_parse_literal(scalar_obj):
                    def parse_literal(ast, variable_values=None):
                        # Extraer valor del AST node
                        value = getattr(ast, 'value', None)
                        
                        # Obtener cache de ContextVar
                        cache = _scalar_cache.get()
                        if cache is None:
                            cache = {}
                            _scalar_cache.set(cache)
                        
                        # Crear cache key único por scalar + valor
                        cache_key = (scalar_obj.__class__.__name__, value)
                        
                        # Si ya fue procesado, retornar resultado cacheado
                        if cache_key in cache:
                            return cache[cache_key]
                        
                        # Cache miss - ejecutar assess()
                        resolved = ScalarResolved(
                            value=value,
                            resolver_name='',
                            resolved=None
                        )
                        result, error = scalar_obj.assess(resolved)
                        if error:
                            raise error
                        
                        # Guardar en cache
                        cache[cache_key] = result
                        return result
                    return parse_literal
                
                # Crear el nuevo scalar type
                new_scalar_type = GraphQLScalarType(
                    name=scalar_name,
                    serialize=make_serialize(scalar_instance),
                    parse_value=make_parse_value(scalar_instance),
                    parse_literal=make_parse_literal(scalar_instance)
                )
                
                # Guardar referencia al scalar viejo
                old_scalar_type = schema.type_map[scalar_name]
                
                # Reemplazar el scalar en el schema
                schema.type_map[scalar_name] = new_scalar_type
                
                # CRÍTICO: Actualizar todas las referencias a este scalar en los campos
                for type_name, graphql_type in schema.type_map.items():
                    # Actualizar GraphQLObjectType (Query, Mutation, Types)
                    if isinstance(graphql_type, GraphQLObjectType) and hasattr(graphql_type, 'fields'):
                        for field_name, field in graphql_type.fields.items():
                            # Reemplazar scalar en el tipo de retorno del campo
                            field.type = self._replace_scalar_in_type(field.type, scalar_name, new_scalar_type)
                            
                            # NO actualizar argumentos aquí - los InputObjectTypes se actualizan abajo
                            # Esto previene la doble ejecución de assess()
                    
                    # Actualizar GraphQLInputObjectType (inputs como UserInput, EventInput)
                    # Esto maneja los campos DENTRO de los input types
                    if isinstance(graphql_type, GraphQLInputObjectType) and hasattr(graphql_type, 'fields'):
                        for field_name, field in graphql_type.fields.items():
                            field.type = self._replace_scalar_in_type(field.type, scalar_name, new_scalar_type)
        
        return schema
    
    def _replace_scalar_in_type(self, field_type, scalar_name, new_scalar_type):
        """Reemplaza recursivamente un scalar en un tipo (manejando NonNull y List)"""
        if isinstance(field_type, GraphQLNonNull):
            return GraphQLNonNull(self._replace_scalar_in_type(field_type.of_type, scalar_name, new_scalar_type))
        elif isinstance(field_type, GraphQLList):
            return GraphQLList(self._replace_scalar_in_type(field_type.of_type, scalar_name, new_scalar_type))
        elif hasattr(field_type, 'name') and field_type.name == scalar_name:
            return new_scalar_type
        else:
            return field_type

    def gql(self, resolvers: dict[str, type]):
        """Registra resolvers para los schemas GraphQL"""
        self.__resolvers = resolvers
        
        # Crear ejecutor GraphQL con autorización y directivas
        self.__executor = GraphQLExecutor(
            on_authorize_fn=self.__on_authorize,
            directives=self.__directives
        )
        
        # Re-cargar schemas para aplicar scalars y directives registrados
        for route in self.__httpConfig.server.routes:
            if route.mode == ConfigHTTPEnum.MODE_GQL:
                schema = self.__load_schema(route.schema)
                schema = self.__executor.assign_resolvers(schema, resolvers)
                self.__schemas[route.endpoint] = schema
    
    def on_authorize(self, authorize_fn: Callable[[AuthorizeInfo], bool]):
        """Registra función de autorización para interceptar resolvers
        
        Args:
            authorize_fn: Función que recibe AuthorizeInfo y retorna True si autorizado
        
        Example:
            def my_authorize(auth_info: AuthorizeInfo) -> bool:
                print(f"Checking {auth_info.dst_type}.{auth_info.resolver}")
                return auth_info.session_id is not None
            
            server.on_authorize(my_authorize)
        """
        self.__on_authorize = authorize_fn
        
        # Re-crear ejecutor con nueva función de autorización
        if self.__resolvers:
            self.__executor = GraphQLExecutor(
                on_authorize_fn=self.__on_authorize,
                directives=self.__directives
            )
            
            # Re-asignar resolvers con nuevo ejecutor
            for endpoint, schema in self.__schemas.items():
                self.__schemas[endpoint] = self.__executor.assign_resolvers(schema, self.__resolvers)
    
    def on_http_check_origin(self, check_origin_fn: Callable[[str, list[str]], bool]):
        """Registra función para validar orígenes CORS dinámicamente
        
        Args:
            check_origin_fn: Función que recibe el origin (string) y allowed_origins (list) 
                           y retorna True si está permitido
        
        Example:
            def my_check_origin(origin: str, allowed_origins: list[str]) -> bool:
                # Validar contra la lista del YAML
                if origin in allowed_origins:
                    return True
                # Validación adicional: permitir subdominios
                if origin.endswith('.midominio.com'):
                    return True
                # Validación basada en patrón o base de datos
                return is_origin_in_database(origin)
            
            server.on_http_check_origin(my_check_origin)
            
        Note:
            - allowed_origins proviene del archivo YAML (cors.allowed_origins)
            - Si allowed_origins está vacío en el YAML, se recibe una lista vacía []
            - El callback tiene prioridad sobre la validación simple de allowed_origins
        """
        self.__on_http_check_origin = check_origin_fn
    
    def scalar(self, name: str, scalar_instance: Scalar):
        """Registra un scalar personalizado
        
        Args:
            name: Nombre del scalar (debe coincidir con 'scalar X' en schema.gql)
            scalar_instance: Instancia de una clase que hereda de Scalar
        
        Example:
            from pgql import HTTPServer, Scalar, ScalarResolved
            from datetime import datetime
            
            class DateScalar(Scalar):
                def set(self, value):
                    if value is None:
                        return None, None
                    if isinstance(value, datetime):
                        return value.strftime("%Y-%m-%d"), None
                    return str(value), None
                
                def assess(self, resolved):
                    if resolved.value is None:
                        return None, None
                    try:
                        return datetime.strptime(resolved.value, "%Y-%m-%d"), None
                    except ValueError as e:
                        return None, e
            
            server = HTTPServer("config.yaml")
            server.scalar("Date", DateScalar())
            
        Note:
            Debe llamarse ANTES de gql() para que los scalars estén registrados
            al momento de cargar el schema.
        """
        print(f"✅ Scalar '{name}' registrado (tipo: {scalar_instance.__class__.__name__})")
        self.__scalars[name] = scalar_instance
    
    def directive(self, name: str, directive_instance: Directive):
        """Registra una directiva personalizada
        
        Args:
            name: Nombre de la directiva (sin @) que se usa en el schema
            directive_instance: Instancia de una clase que hereda de Directive
        
        Example:
            from pgql import HTTPServer, Directive
            
            class PaginateDirective(Directive):
                def invoke(self, args, type_name, field_name):
                    page = args.get('page', 1)
                    split = args.get('split', 10)
                    return {
                        'page': page,
                        'split': split,
                        'skip': (page - 1) * split,
                        'limit': split
                    }, None
            
            server = HTTPServer("config.yaml")
            server.directive("paginate", PaginateDirective())
            
            # En schema.gql:
            # type Query {
            #   users(page: Int, split: Int): [User] @paginate
            # }
            
            # En resolver:
            # def users(self, info: ResolverInfo):
            #     paginate = info.directives.get('paginate')
            #     if paginate:
            #         skip = paginate['skip']
            #         limit = paginate['limit']
        
        Note:
            Las directivas se ejecutan ANTES del resolver.
            Los resultados están disponibles en info.directives[nombre_directiva].
        """
        self.__directives[name] = directive_instance
    
    def create_session(self, max_age: int = 3600) -> Session:
        """Crea una nueva sesión y retorna el objeto Session
        
        Args:
            max_age: Tiempo de vida de la sesión en segundos (default: 3600 = 1 hora)
        
        Returns:
            Session: Objeto de sesión donde puedes guardar datos con session.set(key, value)
        
        Example:
            session = server.create_session(max_age=7200)
            session.set('user_id', 123)
            session.set('username', 'john')
            session.set('roles', ['admin', 'user'])
            print(session.session_id)  # UUID de la sesión
        """
        return self.__session_store.create(max_age)
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Obtiene una sesión existente por su ID
        
        Args:
            session_id: ID de la sesión a obtener
        
        Returns:
            Session o None si no existe o expiró
        
        Example:
            session = server.get_session('uuid-here')
            if session:
                user_id = session.get('user_id')
        """
        return self.__session_store.get(session_id)
    
    def delete_session(self, session_id: str):
        """Elimina una sesión (útil para logout)
        
        Args:
            session_id: ID de la sesión a eliminar
        """
        self.__session_store.delete(session_id)

    def file(self, route: RouteConfig):
        pass

    def rest(self, route: RouteConfig):
        pass

    def mount(self, path: str, app, name: str = None):
        """Monta una aplicación ASGI (como FastAPI) en una ruta específica
        
        Args:
            path: Ruta base donde se montará la aplicación (ej: "/api", "/v1")
            app: Aplicación ASGI (FastAPI, Starlette, etc.)
            name: Nombre opcional para el mount
        
        Example:
            from fastapi import FastAPI
            from pgql import HTTPServer
            
            # Tu aplicación FastAPI existente
            fastapi_app = FastAPI()
            
            @fastapi_app.get("/users")
            def get_users():
                return {"users": ["Alice", "Bob"]}
            
            # Servidor pygql
            server = HTTPServer('config.yml')
            server.scalar("Date", DateScalar())
            server.gql({"Query": Query, "Mutation": Mutation})
            
            # Montar FastAPI en /api
            server.mount("/api", fastapi_app, name="fastapi")
            
            # Ahora tienes:
            # - /graphql -> pygql GraphQL
            # - /api/users -> FastAPI endpoint
            
            server.start()  # Un solo uvicorn corriendo ambas apps
        
        Note:
            Debe llamarse ANTES de start() para que las rutas se registren correctamente.
            La aplicación montada tendrá acceso a todas las sub-rutas bajo el path especificado.
        """
        mount = Mount(path, app=app, name=name)
        self.__mounts.append(mount)
        print(f"🔗 Montada aplicación '{name or 'unnamed'}' en {path}")

    def start(self):
        # Combinar routes y mounts
        all_routes = self.__routes + self.__mounts
        
        # Crear app Starlette
        self.__app = Starlette(routes=all_routes, debug=self.__httpConfig.debug)
        
        # Obtener configuración de CORS
        cors_config = self.__httpConfig.cors
        
        # Crear función de validación de origin combinando config y callback
        def check_origin_combined(origin: str) -> bool:
            # Si hay callback personalizado, usarlo (pasándole allowed_origins del config)
            if self.__on_http_check_origin:
                return self.__on_http_check_origin(origin, cors_config.allowed_origins)
            # Si hay lista de orígenes permitidos en config, validar contra ella
            if cors_config.allowed_origins:
                return origin in cors_config.allowed_origins
            # Por defecto permite todos
            return True
        
        # Añadir middleware CORS con validación dinámica
        @self.__app.middleware("http")
        async def cors_middleware(request: Request, call_next):
            # Si CORS no está habilitado, procesar sin headers CORS
            if not cors_config.enabled:
                return await call_next(request)
            
            # Obtener el origin del request
            origin = request.headers.get("origin", "")
            
            # Si no hay origin o está permitido, procesar request
            if not origin or check_origin_combined(origin):
                response = await call_next(request)
                
                # Añadir headers CORS si hay origin
                if origin:
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Allow-Credentials"] = cors_config.allow_credentials
                    response.headers["Access-Control-Allow-Methods"] = cors_config.allow_methods
                    response.headers["Access-Control-Allow-Headers"] = cors_config.allow_headers
                
                return response
            else:
                # Origin no permitido
                return JSONResponse(
                    {"error": "Origin not allowed"},
                    status_code=403,
                    headers={"Content-Type": "application/json"}
                )
        
        # Manejar preflight requests (OPTIONS)
        @self.__app.middleware("http")
        async def cors_preflight_middleware(request: Request, call_next):
            if request.method == "OPTIONS":
                # Si CORS no está habilitado, dejar pasar la request normalmente
                if not cors_config.enabled:
                    return await call_next(request)
                
                origin = request.headers.get("origin", "")
                
                if not origin or check_origin_combined(origin):
                    return Response(
                        status_code=200,
                        headers={
                            "Access-Control-Allow-Origin": origin if origin else "*",
                            "Access-Control-Allow-Methods": cors_config.allow_methods,
                            "Access-Control-Allow-Headers": cors_config.allow_headers,
                            "Access-Control-Allow-Credentials": cors_config.allow_credentials,
                            "Access-Control-Max-Age": cors_config.max_age
                        }
                    )
                else:
                    return JSONResponse({"error": "Origin not allowed"}, status_code=403)
            
            return await call_next(request)
        
        uvicorn.run(self.__app, host=self.__httpConfig.server.host, port=self.__httpConfig.http_port)

    @staticmethod
    async def gql_handler(schemas, request: Request, session_store=None, cookie_name='session_id'):
        """Maneja peticiones GraphQL"""
        try:
            # Inicializar cache de scalars para esta request
            _scalar_cache.set({})
            
            data = await request.json()
            query = data.get("query")
            variables = data.get("variables", {})
            operation_name = data.get("operationName")
            
            # Obtener schema para esta ruta
            schema = schemas.get(request.url.path)
            if not schema:
                return JSONResponse({"errors": [{"message": "Schema not found"}]}, status_code=404)
            
            # Extraer session_id de cookies y obtener sesión
            session_id = request.cookies.get(cookie_name)
            session = None
            if session_store and session_id:
                session = session_store.get(session_id)
            
            # Crear contexto con session_id, session y una función para crear nuevas sesiones
            context = {
                'session': session,  # Objeto Session o None
                'request': request,
                'new_session': None  # Se usará para setear nueva sesión en la respuesta
            }
            
            result = await graphql(
                schema,
                query,
                variable_values=variables,
                operation_name=operation_name,
                context_value=context
            )
            
            response_data = {"data": result.data}
            if result.errors:
                formatted_errors = []
                for error in result.errors:
                    # Verificar si es un error de pgql (Fatal/Warning)
                    original_error = getattr(error, 'original_error', None)
                    
                    if original_error and hasattr(original_error, 'error'):
                        # Es un error de pgql (Fatal o Warning)
                        error_struct = original_error.error()
                        error_dict = error_struct.to_dict()
                        
                        # Agregar path y locations desde el GraphQLError si existen
                        if hasattr(error, 'path') and error.path:
                            error_dict["path"] = error.path
                        if hasattr(error, 'locations') and error.locations:
                            error_dict["locations"] = [{"line": loc.line, "column": loc.column} for loc in error.locations]
                    else:
                        # Es un GraphQLError estándar
                        error_dict = {
                            "message": error.message,
                        }
                        if hasattr(error, 'path') and error.path:
                            error_dict["path"] = error.path
                        if hasattr(error, 'locations') and error.locations:
                            error_dict["locations"] = [{"line": loc.line, "column": loc.column} for loc in error.locations]
                        if hasattr(error, 'extensions') and error.extensions:
                            error_dict["extensions"] = error.extensions
                    
                    formatted_errors.append(error_dict)
                response_data["errors"] = formatted_errors
            
            json_response = JSONResponse(response_data)
            
            # Si se creó una nueva sesión en el contexto, setear la cookie
            if context.get('new_session'):
                new_session = context['new_session']
                json_response.set_cookie(
                    key=cookie_name,
                    value=new_session.session_id,
                    max_age=new_session.max_age,
                    httponly=True,
                    secure=False,  # Cambiar a True en producción con HTTPS
                    samesite='lax'
                )
            
            return json_response
        except Exception as e:
            return JSONResponse({"errors": [str(e)]}, status_code=400)

    async def __file_handler(self, request: Request):
        """Sirve archivos estáticos desde el directorio configurado"""
        file_path = request.path_params.get("path", "")
        full_path = os.path.join(self.__file_base_dir, file_path)
        # Seguridad: evitar path traversal (ej: ../../../etc/passwd)
        #full_path = os.path.normpath(full_path)
        #base_dir_abs = os.path.abspath(base_dir)
        #full_path_abs = os.path.abspath(full_path)
        # Verificar si el archivo existe
        # Verificar si el archivo existe
        if not os.path.isfile(full_path):
            return JSONResponse({"error": "File not found"}, status_code=404)
        # Servir el archivo
        return FileResponse(full_path)

    async def rest_handler(self, request: Request):
        return Response("REST handler not implemented", status_code=501)
    
    def not_found_handler(self, request: Request):
        pass
