from functools import partial, wraps
from graphql import GraphQLSchema, build_schema, graphql
from graphql.type.definition import GraphQLObjectType, GraphQLNonNull, GraphQLList
import uvicorn
from pgql.http.config_http_enum import ConfigHTTPEnum
from .config import HTTPConfig, RouteConfig
from .authorize_info import AuthorizeInfo
from .session import SessionStore, Session
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.routing import Route
from typing import Callable, Optional
import glob

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
    request: Optional[Request] = None
) -> GraphQLSchema:
    """Asigna resolvers a los campos del schema con interceptor de autorización opcional
    
    Args:
        schema: El schema GraphQL
        classes: Diccionario de resolvers mapeados por nombre de tipo
        on_authorize_fn: Función opcional para autorizar ejecución de resolvers
        request: Request de Starlette para obtener session_id de cookies
    """
    
    def create_authorized_resolver(original_resolver, src_type: str, dst_type: str, resolver_name: str, operation: str):
        """Crea un wrapper que intercepta la ejecución del resolver con autorización"""
        @wraps(original_resolver)
        def authorized_resolver(parent, info, **kwargs):
            # Si hay función de autorización, ejecutarla
            if on_authorize_fn:
                # Obtener session_id del contexto
                session_id = None
                if info.context and isinstance(info.context, dict):
                    session_id = info.context.get('session_id')
                
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
            
            # Si está autorizado o no hay función de autorización, ejecutar resolver
            return original_resolver(parent, info, **kwargs)
        
        return authorized_resolver
    
    def assign_type_resolvers(graphql_type: GraphQLObjectType, operation: str):
        if not hasattr(graphql_type, 'fields'):
            return
        
        for field_name, field in graphql_type.fields.items():
            return_type_name = get_base_type_name(field.type)
            
            if return_type_name and return_type_name in classes:
                resolver_obj = classes[return_type_name]
                if hasattr(resolver_obj, field_name):
                    method = getattr(resolver_obj, field_name)
                    
                    # Wrappear el resolver con autorización
                    # src_type es el tipo GraphQL que contiene el field (ej: User para User.company)
                    # dst_type es el tipo de retorno del field (ej: Company para User.company)
                    authorized_method = create_authorized_resolver(
                        method,
                        graphql_type.name,  # src_type: tipo padre
                        return_type_name,   # dst_type: tipo de retorno
                        field_name,         # resolver: nombre del field
                        operation
                    )
                    
                    field.resolve = authorized_method
                    
                    # Obtener el nombre de la clase (funciona para instancias y clases)
                    resolver_name = resolver_obj.__class__.__name__ if not isinstance(resolver_obj, type) else resolver_obj.__name__
                    auth_status = "🔒" if on_authorize_fn else "✅"
                    print(f"{auth_status} Asignado {resolver_name}.{field_name} a {graphql_type.name}.{field_name}")
    
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
        return build_schema(full_schema)

    def gql(self, resolvers: dict[str, type]):
        """Registra resolvers para los schemas GraphQL"""
        self.__resolvers = resolvers
        for endpoint, schema in self.__schemas.items():
            schema = assign_resolvers(schema, resolvers, self.__on_authorize)
            self.__schemas[endpoint] = schema
    
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
                schema = assign_resolvers(schema, self.__resolvers, self.__on_authorize)
                self.__schemas[endpoint] = schema
    
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
