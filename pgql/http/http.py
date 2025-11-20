from functools import partial, wraps
from graphql import GraphQLSchema, build_schema, graphql, GraphQLScalarType
from graphql.type.definition import GraphQLObjectType, GraphQLNonNull, GraphQLList
import uvicorn
import re
from pgql.http.config_http_enum import ConfigHTTPEnum
from pgql.resolvers.base import Scalar, ScalarResolved, ResolverInfo
from pgql.directives import Directive
from .config import HTTPConfig, RouteConfig
from .authorize_info import AuthorizeInfo
from .session import SessionStore, Session
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.routing import Route
from typing import Callable, Optional
import glob

def camel_to_snake(name: str) -> str:
    """Convierte camelCase a snake_case"""
    # Insertar _ antes de cada letra mayúscula y convertir a minúsculas
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def get_base_type_name(field_type):
    while isinstance(field_type, (GraphQLNonNull, GraphQLList)):
        if isinstance(field_type, GraphQLNonNull):
            field_type = field_type.of_type
        elif isinstance(field_type, GraphQLList):
            field_type = field_type.of_type
    return getattr(field_type, 'name', None)

def assign_resolvers(
    schema: GraphQLSchema, 
    classes: dict[str, type],
    on_authorize_fn: Optional[Callable[[AuthorizeInfo], bool]] = None,
    request: Optional[Request] = None,
    directives: Optional[dict[str, Directive]] = None
) -> GraphQLSchema:
    """Asigna resolvers a los campos del schema con interceptor de autorización y directivas
    
    Args:
        schema: El schema GraphQL
        classes: Diccionario de resolvers mapeados por nombre de tipo
        on_authorize_fn: Función opcional para autorizar ejecución de resolvers
        request: Request de Starlette para obtener session_id de cookies
        directives: Diccionario de directivas registradas
    """
    
    directives = directives or {}
    
    def create_authorized_resolver(original_resolver, src_type: str, dst_type: str, resolver_name: str, operation: str):
        """Crea un wrapper que intercepta la ejecución del resolver con autorización y directivas"""
        @wraps(original_resolver)
        def authorized_resolver(parent, info, **kwargs):
            # Convertir argumentos de camelCase a snake_case
            snake_kwargs = {camel_to_snake(key): value for key, value in kwargs.items()}
            
            # Obtener session_id del contexto
            session_id = None
            if info.context and isinstance(info.context, dict):
                session_id = info.context.get('session_id')
            
            # ⚡ PASO 1: Procesar directivas ANTES del resolver
            # Las directivas se obtienen del SCHEMA (no de la query)
            directive_results = {}
            
            # Obtener directivas del schema
            if info.parent_type and info.field_name:
                # Acceder al campo en el schema
                field_def = info.parent_type.fields.get(info.field_name)
                if field_def and hasattr(field_def, 'ast_node') and field_def.ast_node:
                    if hasattr(field_def.ast_node, 'directives') and field_def.ast_node.directives:
                        for directive_node in field_def.ast_node.directives:
                            directive_name = directive_node.name.value
                            if directive_name in directives:
                                # Pasar todos los argumentos del field a la directiva
                                # La directiva decide cuáles usar
                                directive_args = kwargs.copy()
                                
                                # Invocar directiva
                                directive_instance = directives[directive_name]
                                result, error = directive_instance.invoke(
                                    directive_args,
                                    dst_type,
                                    resolver_name
                                )
                                
                                if error:
                                    # Si la directiva retorna error, manejarlo
                                    raise Exception(str(error))
                                
                                directive_results[directive_name] = result
            
            # Crear ResolverInfo compatible con Go
            resolver_info = ResolverInfo(
                operation=operation,
                resolver=resolver_name,
                args=snake_kwargs,
                parent=parent,
                type_name=dst_type,
                directives=directive_results,  # ⬅️ Directivas procesadas
                parent_type_name=src_type,
                session_id=session_id,
                context=info.context if info.context else {},
                field_name=resolver_name
            )
            
            # ⚡ PASO 2: Autorización (si está configurada)
            if on_authorize_fn:
                # Crear objeto de autorización
                auth_info = AuthorizeInfo(
                    operation=operation,
                    src_type=src_type,
                    dst_type=dst_type,
                    resolver=resolver_name,
                    session_id=session_id
                )
                
                # Ejecutar función de autorización
                authorized = on_authorize_fn(auth_info)
                
                if not authorized:
                    raise PermissionError(f"No autorizado para ejecutar {dst_type}.{resolver_name}")
            
            # Ejecutar resolver solo con resolver_info (estilo Go)
            # parent está disponible en resolver_info.parent
            return original_resolver(resolver_info, **snake_kwargs)
        
        return authorized_resolver
    
    def assign_type_resolvers(graphql_type: GraphQLObjectType, operation: str):
        if not hasattr(graphql_type, 'fields'):
            return
        
        # Buscar resolver por el tipo padre primero (para root queries/mutations)
        parent_resolver = classes.get(graphql_type.name)
        
        for field_name, field in graphql_type.fields.items():
            return_type_name = get_base_type_name(field.type)
            
            # Convertir el nombre del field de camelCase a snake_case para buscar el método
            method_name = camel_to_snake(field_name)
            
            # Opción 1: Resolver en el objeto del tipo padre (ej: Query.get_users)
            if parent_resolver and hasattr(parent_resolver, method_name):
                method = getattr(parent_resolver, method_name)
                
                authorized_method = create_authorized_resolver(
                    method,
                    graphql_type.name,  # src_type: tipo padre
                    return_type_name,   # dst_type: tipo de retorno
                    field_name,         # resolver: nombre del field
                    operation
                )
                
                field.resolve = authorized_method
                
                resolver_name = parent_resolver.__class__.__name__ if not isinstance(parent_resolver, type) else parent_resolver.__name__
                auth_status = "🔒" if on_authorize_fn else "✅"
                print(f"{auth_status} Asignado {resolver_name}.{method_name} a {graphql_type.name}.{field_name}")
            
            # Opción 2: Resolver en el objeto del tipo de retorno (ej: Company para User.company)
            elif return_type_name and return_type_name in classes:
                resolver_obj = classes[return_type_name]
                if hasattr(resolver_obj, method_name):
                    method = getattr(resolver_obj, method_name)
                    
                    authorized_method = create_authorized_resolver(
                        method,
                        graphql_type.name,  # src_type: tipo padre
                        return_type_name,   # dst_type: tipo de retorno
                        field_name,         # resolver: nombre del field
                        operation
                    )
                    
                    field.resolve = authorized_method
                    
                    resolver_name = resolver_obj.__class__.__name__ if not isinstance(resolver_obj, type) else resolver_obj.__name__
                    auth_status = "🔒" if on_authorize_fn else "✅"
                    print(f"{auth_status} Asignado {resolver_name}.{method_name} a {graphql_type.name}.{field_name}")
    
    # Determinar el tipo de operación basado en el tipo de schema
    if schema.query_type:
        assign_type_resolvers(schema.query_type, 'query')
    
    if schema.mutation_type:
        assign_type_resolvers(schema.mutation_type, 'mutation')
    
    if schema.subscription_type:
        assign_type_resolvers(schema.subscription_type, 'subscription')
    
    # Asignar resolvers para tipos anidados (no son operaciones root)
    for type_name, graphql_type in schema.type_map.items():
        if isinstance(graphql_type, GraphQLObjectType):
            # Skip tipos de operación root ya procesados
            if graphql_type in [schema.query_type, schema.mutation_type, schema.subscription_type]:
                continue
            assign_type_resolvers(graphql_type, 'query')  # Los nested fields se consideran 'query'
    
    return schema

class HTTPServer:
    def __init__(self, configPath: str):
        self.__httpConfig = HTTPConfig(configPath)
        self.__app: Starlette = None
        self.__routes: list[Route] = []
        self.__schemas: dict[str, GraphQLSchema] = {}
        self.__on_authorize: Optional[Callable[[AuthorizeInfo], bool]] = None
        self.__resolvers: dict[str, type] = {}
        self.__session_store = SessionStore()  # Almacén de sesiones
        self.__scalars: dict[str, Scalar] = {}  # Registro de custom scalars
        self.__directives: dict[str, 'Directive'] = {}  # Registro de custom directives

        for route in self.__httpConfig.server.routes:
            match route.mode:
                case ConfigHTTPEnum.MODE_GQL:
                    schema = self.__load_schema(route.schema)
                    self.__schemas[route.endpoint] = schema
                    async def handler(request):
                        return await self.__class__.gql_handler(
                            self.__schemas, 
                            request, 
                            self.__on_authorize,
                            self.__resolvers,
                            self.__session_store,
                            self.__httpConfig.cookie_name
                        )
                    self.__routes.append(Route(route.endpoint, handler, methods=['POST']))
                # case ConfigHTTPEnum.MODE_FILE:
                #     async def file_handler(request):
                #         return await self.file_handler(request)
                #     self.__routes.append(Route(route.endpoint, file_handler))
                # case ConfigHTTPEnum.MODE_REST:
                #     async def rest_handler(request):
                #         return await self.rest_handler(request)
                #     self.__routes.append(Route(route.endpoint, rest_handler))

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
                        resolved = ScalarResolved(
                            value=value,
                            resolver_name='',
                            resolved=None
                        )
                        result, error = scalar_obj.assess(resolved)
                        if error:
                            raise error
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
                print(f"      ✅ Scalar '{scalar_name}' reemplazado en type_map")
                
                # CRÍTICO: Actualizar todas las referencias a este scalar en los campos
                for type_name, graphql_type in schema.type_map.items():
                    if isinstance(graphql_type, GraphQLObjectType) and hasattr(graphql_type, 'fields'):
                        for field_name, field in graphql_type.fields.items():
                            # Reemplazar scalar en el tipo del campo (manejando NonNull y List)
                            field.type = self._replace_scalar_in_type(field.type, scalar_name, new_scalar_type)
                            
                            # También actualizar argumentos del campo
                            if hasattr(field, 'args') and field.args:
                                for arg_name, arg in field.args.items():
                                    arg.type = self._replace_scalar_in_type(arg.type, scalar_name, new_scalar_type)
        
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
        # Re-cargar schemas para aplicar scalars y directives registrados
        for route in self.__httpConfig.server.routes:
            if route.mode == ConfigHTTPEnum.MODE_GQL:
                schema = self.__load_schema(route.schema)
                schema = assign_resolvers(
                    schema, 
                    resolvers, 
                    self.__on_authorize,
                    directives=self.__directives  # ⬅️ Pasar directivas
                )
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
        # Re-asignar resolvers con la nueva función de autorización
        if self.__resolvers:
            for endpoint, schema in self.__schemas.items():
                schema = assign_resolvers(
                    schema, 
                    self.__resolvers, 
                    self.__on_authorize,
                    directives=self.__directives  # ⬅️ Pasar directivas
                )
                self.__schemas[endpoint] = schema
    
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

    async def file_handler(self, request: Request):
        return Response("File handler not implemented", status_code=501)

    async def rest_handler(self, request: Request):
        return Response("REST handler not implemented", status_code=501)

    def start(self):
        self.__app = Starlette(routes=self.__routes, debug=self.__httpConfig.debug)
        uvicorn.run(self.__app, host=self.__httpConfig.server.host, port=self.__httpConfig.http_port)

    @staticmethod
    async def gql_handler(schemas, request: Request, on_authorize_fn=None, resolvers=None, session_store=None, cookie_name='session_id'):
        """Maneja peticiones GraphQL"""
        try:
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
                'session_id': session_id,
                'session': session,  # Objeto Session o None
                'request': request,
                'new_session': None  # Se usará para setear nueva sesión en la respuesta
            }
            
            # Re-asignar resolvers con el request actual para cada petición
            # Esto permite que el wrapper de autorización tenga acceso al session_id
            if resolvers and on_authorize_fn:
                schema = assign_resolvers(schema, resolvers, on_authorize_fn, request)
            
            result = await graphql(
                schema,
                query,
                variable_values=variables,
                operation_name=operation_name,
                context_value=context
            )
            
            response_data = {"data": result.data}
            if result.errors:
                response_data["errors"] = [str(error) for error in result.errors]
            
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

    async def file_handler(self, request: Request):
        pass

    async def rest_handler(self, request: Request):
        pass
    
    def not_found_handler(self, request: Request):
        pass
