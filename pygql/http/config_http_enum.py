from enum import Enum

class ConfigHTTPEnum(int, Enum):
    MODE_GQL = 0
    MODE_FILE = 1
    MODE_REST = 2
    MODE_WEBSOCKET = 3