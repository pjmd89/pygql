"""
GraphQL error definitions compatible with Go's definitionError package.

Provides error types and constructors for GraphQL operations, matching
the Go implementation's error levels (WARNING and FATAL).
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import IntEnum


class ErrorLevel(IntEnum):
    """Error severity levels, compatible with Go"""
    LEVEL_WARNING = 0  # Warning, execution continues
    LEVEL_FATAL = 1    # Fatal error, execution stops


# Constants for easier access
LEVEL_WARNING = ErrorLevel.LEVEL_WARNING
LEVEL_FATAL = ErrorLevel.LEVEL_FATAL


# Type aliases to match Go's naming
ExtensionError = Dict[str, Any]


@dataclass
class GQLErrorLocation:
    """Location in GraphQL document where error occurred"""
    line: int
    column: int
    
    def to_dict(self) -> Dict[str, int]:
        return {"line": self.line, "column": self.column}


@dataclass
class ErrorStruct:
    """
    GraphQL error structure compatible with Go.
    
    Matches the GraphQL spec error format:
    https://spec.graphql.org/October2021/#sec-Errors
    """
    message: str
    code: str = "000"
    locations: Optional[List[GQLErrorLocation]] = None
    path: Optional[List[Any]] = None
    extensions: Optional[ExtensionError] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to GraphQL spec error format"""
        result: Dict[str, Any] = {"message": self.message}
        
        if self.locations:
            result["locations"] = [loc.to_dict() for loc in self.locations]
        
        if self.path:
            result["path"] = self.path
        
        if self.extensions:
            result["extensions"] = self.extensions
        
        return result


class GQLError:
    """
    Base class for GraphQL errors, compatible with Go's GQLError interface.
    
    Go interface:
        type GQLError interface {
            Error() ErrorStruct
            ErrorLevel() errorLevel
        }
    """
    
    def __init__(self, error_struct: ErrorStruct, level: ErrorLevel):
        self._error_struct = error_struct
        self._level = level
    
    def error(self) -> ErrorStruct:
        """Returns the error structure (matches Go's Error() method)"""
        return self._error_struct
    
    def error_level(self) -> ErrorLevel:
        """Returns the error level (matches Go's ErrorLevel() method)"""
        return self._level
    
    def __str__(self) -> str:
        return self._error_struct.message
    
    def __repr__(self) -> str:
        level_name = "WARNING" if self._level == LEVEL_WARNING else "FATAL"
        return f"{level_name}: {self._error_struct.message}"


class Warning(GQLError):
    """
    Warning error - execution continues.
    Compatible with Go's Warning struct.
    """
    
    def __init__(self, error_struct: ErrorStruct):
        super().__init__(error_struct, LEVEL_WARNING)


class Fatal(GQLError):
    """
    Fatal error - execution stops.
    Compatible with Go's Fatal struct.
    """
    
    def __init__(self, error_struct: ErrorStruct):
        super().__init__(error_struct, LEVEL_FATAL)


# Type alias for error lists
ErrorList = List[GQLError]


def _set_extension(
    extensions: Optional[ExtensionError],
    err_level: ErrorLevel,
    code: str
) -> ExtensionError:
    """
    Set extension metadata for error.
    Matches Go's setExtension() function.
    """
    if extensions is None:
        extensions = {}
    
    if "code" not in extensions:
        extensions["code"] = code
    
    level_name = "warning" if err_level == LEVEL_WARNING else "fatal"
    extensions["level"] = level_name
    
    return extensions


@dataclass
class ErrorDescriptor:
    """Describes an error with message, code and level"""
    message: str
    code: str
    level: ErrorLevel


def new_error(
    err: ErrorDescriptor,
    extensions: Optional[ExtensionError] = None
) -> GQLError:
    """
    Create a new error (Warning or Fatal) based on descriptor.
    Matches Go's NewError() function.
    """
    extensions = _set_extension(extensions, err.level, err.code)
    
    error_struct = ErrorStruct(
        message=err.message,
        code=err.code,
        extensions=extensions
    )
    
    if err.level == LEVEL_FATAL:
        return Fatal(error_struct)
    else:
        return Warning(error_struct)


def new_warning(
    message: str,
    extensions: Optional[ExtensionError] = None
) -> Warning:
    """
    Create a new Warning error.
    Matches Go's NewWarning() function.
    """
    extensions = _set_extension(extensions, LEVEL_WARNING, "000")
    
    error_struct = ErrorStruct(
        message=message,
        code="000",
        extensions=extensions
    )
    
    return Warning(error_struct)


def new_fatal(
    message: str,
    extensions: Optional[ExtensionError] = None
) -> Fatal:
    """
    Create a new Fatal error.
    Matches Go's NewFatal() function.
    """
    extensions = _set_extension(extensions, LEVEL_FATAL, "000")
    
    error_struct = ErrorStruct(
        message=message,
        code="000",
        extensions=extensions
    )
    
    return Fatal(error_struct)


def get_errors(error_list: ErrorList) -> List[Dict[str, Any]]:
    """
    Convert error list to GraphQL spec format.
    Matches Go's ErrorList.GetErrors() method.
    """
    if not error_list:
        return []
    
    return [err.error().to_dict() for err in error_list]
