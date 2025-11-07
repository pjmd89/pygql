import uvicorn
from pygql.http.config_http_enum import ConfigHTTPEnum
from .config import HTTPConfig, RouteConfig
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.routing import Route
import glob
from graphql import GraphQLSchema, build_schema

class HTTPServer:
    def __init__(self, configPath: str):
        self.__httpConfig = HTTPConfig(configPath)
        self.__app: Starlette = None
        self.__routes: list[Route] = []

        for route in self.__httpConfig.server.routes:
            match route.mode:
                case ConfigHTTPEnum.MODE_GQL:
                    self.__routes.append(Route(route.endpoint, self.gql_handler))
                case ConfigHTTPEnum.MODE_FILE:
                    self.__routes.append(Route(route.endpoint, self.file_handler))
                case ConfigHTTPEnum.MODE_REST:
                    self.__routes.append(Route(route.endpoint, self.rest_handler))

    def load_schema(self, schema_path: str) -> GraphQLSchema:
        schema_parts = []
        for file_path in glob.glob(schema_path + '/*.gql'):
            with open(file_path, 'r') as f:
                schema_parts.append(f.read())

        full_schema = '\n'.join(schema_parts)
        return build_schema(full_schema)

    def gql(self, route: RouteConfig):
        pass

    def file(self, route: RouteConfig):
        pass

    def rest(self, route: RouteConfig):
        pass

    def start(self):
        self.__app = Starlette(routes=self.__routes, debug=self.__httpConfig.debug)
        uvicorn.run(self.__app, host=self.__httpConfig.server.host, port=self.__httpConfig.http_port)

    async def gql_handler(self, request: Request):
        pass

    async def file_handler(self, request: Request):
        pass

    async def rest_handler(self, request: Request):
        pass
    
    def not_found_handler(self, request: Request):
        pass
