from functools import partial
from graphql import GraphQLSchema, build_schema, graphql
from graphql.type.definition import GraphQLObjectType, GraphQLNonNull, GraphQLList
import uvicorn
from pgql.http.config_http_enum import ConfigHTTPEnum
from .config import HTTPConfig, RouteConfig
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.routing import Route
import glob

def get_base_type_name(field_type):
    while isinstance(field_type, (GraphQLNonNull, GraphQLList)):
        if isinstance(field_type, GraphQLNonNull):
            field_type = field_type.of_type
        elif isinstance(field_type, GraphQLList):
            field_type = field_type.of_type
    return getattr(field_type, 'name', None)

def assign_resolvers(schema: GraphQLSchema, classes: dict[str, type]) -> GraphQLSchema:
    def assign_type_resolvers(graphql_type: GraphQLObjectType):
        if not hasattr(graphql_type, 'fields'):
            return
        
        for field_name, field in graphql_type.fields.items():
            return_type_name = get_base_type_name(field.type)
            
            if return_type_name and return_type_name in classes:
                resolver_obj = classes[return_type_name]
                if hasattr(resolver_obj, field_name):
                    method = getattr(resolver_obj, field_name)
                    field.resolve = method
                    # Obtener el nombre de la clase (funciona para instancias y clases)
                    resolver_name = resolver_obj.__class__.__name__ if not isinstance(resolver_obj, type) else resolver_obj.__name__
                    print(f"✅ Asignado {resolver_name}.{field_name} a {graphql_type.name}.{field_name}")
    
    for type_name, graphql_type in schema.type_map.items():
        if isinstance(graphql_type, GraphQLObjectType):
            assign_type_resolvers(graphql_type)
    
    return schema

class HTTPServer:
    def __init__(self, configPath: str):
        self.__httpConfig = HTTPConfig(configPath)
        self.__app: Starlette = None
        self.__routes: list[Route] = []
        self.__schemas: dict[str, GraphQLSchema] = {}

        for route in self.__httpConfig.server.routes:
            match route.mode:
                case ConfigHTTPEnum.MODE_GQL:
                    schema = self.__load_schema(route.schema)
                    self.__schemas[route.endpoint] = schema
                    async def handler(request):
                        return await self.__class__.gql_handler(self.__schemas, request)
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
        for endpoint, schema in self.__schemas.items():
            schema = assign_resolvers(schema, resolvers)
            self.__schemas[endpoint] = schema

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
    async def gql_handler(schemas, request: Request):
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
            
            result = await graphql(
                schema,
                query,
                variable_values=variables,
                operation_name=operation_name,
            )
            
            response = {"data": result.data}
            if result.errors:
                response["errors"] = [str(error) for error in result.errors]
            
            return JSONResponse(response)
        except Exception as e:
            return JSONResponse({"errors": [str(e)]}, status_code=400)

    async def file_handler(self, request: Request):
        pass

    async def rest_handler(self, request: Request):
        pass
    
    def not_found_handler(self, request: Request):
        pass
