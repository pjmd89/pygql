import yaml
from .config_http_enum import ConfigHTTPEnum
class RouteConfig:
    def __init__(self, data: dict):
        mode = data.get("mode", "gql")
        self.mode: ConfigHTTPEnum = ConfigHTTPEnum["MODE_"+mode.upper()]
        self.endpoint: str = data.get("endpoint", "")
        self.path: str = data.get("path", None)  # Opcional, solo para mode: file
        self.schema: str = data.get("schema", None)  # Opcional, solo para mode: gql

class ServerConfig:
    def __init__(self, data: dict):
        self.host: str = data.get("host", "localhost")
        self.routes: list[RouteConfig] = [RouteConfig(route) for route in data.get("routes", [])]

class CORSConfig:
    def __init__(self, data: dict):
        self.enabled: bool = data.get("enabled", True)
        self.allow_credentials: str = data.get("allow_credentials", "true")
        self.allow_methods: str = data.get("allow_methods", "*")
        self.allow_headers: str = data.get("allow_headers", "*")
        self.max_age: str = data.get("max_age", "86400")
        self.allowed_origins: list[str] = data.get("allowed_origins", [])

class HTTPConfig:
    @property
    def http_port(self) -> int:
        return self.__config_data.get("http_port", 8080)
    @property
    def https_port(self) -> int:
        return self.__config_data.get("https_port", 8443)
    @property
    def cookie_name(self) -> str:
        return self.__config_data.get("cookie_name", "session_id")
    @property
    def debug(self) -> bool:
        return self.__config_data.get("debug", False)
    @property
    def server(self) -> ServerConfig:
        """Devuelve un objeto ServerConfig"""
        server_data = self.__config_data.get("server", {})
        return ServerConfig(server_data)
    @property
    def cors(self) -> CORSConfig:
        """Devuelve un objeto CORSConfig"""
        cors_data = self.__config_data.get("cors", {})
        return CORSConfig(cors_data)
    @property
    def config_path(self) -> str:
        return self.__config_path
    
    def __init__(self, config_path: str):
        self.__config_path = config_path
        self.__config_data = yaml.safe_load(open(config_path, 'r'))