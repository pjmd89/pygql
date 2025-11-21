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


class GQLError(Exception):
    """
    Base class for GraphQL errors, compatible with Go's GQLError interface.
    Now inherits from Exception to be raisable in Python.
    
    Go interface:
        type GQLError interface {
            Error() ErrorStruct
            ErrorLevel() errorLevel
        }
    """
    
    def __init__(self, error_struct: ErrorStruct, level: ErrorLevel):
        super().__init__(error_struct.message)
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
    err: Optional[ErrorDescriptor] = None,
    extensions: Optional[ExtensionError] = None,
    message: Optional[str] = None,
    code: Optional[str] = None,
    level: Optional[ErrorLevel] = None
) -> GQLError:
    """
    Create a new error (Warning or Fatal).
    
    Flexible usage:
    1. With ErrorDescriptor: new_error(err=descriptor, extensions={...})
    2. With message only: new_error(message="Error", level=LEVEL_FATAL)
    3. With all params: new_error(message="Error", code="CODE", level=LEVEL_FATAL, extensions={...})
    
    Matches Go's NewError() function.
    """
    # Si se pasa ErrorDescriptor, usarlo
    if err is not None:
        final_message = err.message
        final_code = err.code
        final_level = err.level
    # Si no, usar los parámetros individuales
    else:
        if message is None:
            raise ValueError("Either 'err' or 'message' must be provided")
        final_message = message
        final_code = code or "000"
        final_level = level or LEVEL_WARNING
    
    extensions = _set_extension(extensions, final_level, final_code)
    
    error_struct = ErrorStruct(
        message=final_message,
        code=final_code,
        extensions=extensions
    )
    
    if final_level == LEVEL_FATAL:
        return Fatal(error_struct)
    else:
        return Warning(error_struct)


def new_warning(
    message: Optional[str] = None,
    extensions: Optional[ExtensionError] = None,
    err: Optional[ErrorDescriptor] = None
) -> Warning:
    """
    Create a new Warning error.
    
    Usage:
    1. new_warning(message="Warning text")
    2. new_warning(message="Warning", extensions={...})
    3. new_warning(err=descriptor, extensions={...})
    
    Matches Go's NewWarning() function.
    """
    if err is not None:
        return new_error(err=err, extensions=extensions, level=LEVEL_WARNING)
    
    if message is None:
        raise ValueError("Either 'err' or 'message' must be provided")
    
    return new_error(message=message, extensions=extensions, level=LEVEL_WARNING)


def new_fatal(
    message: Optional[str] = None,
    extensions: Optional[ExtensionError] = None,
    err: Optional[ErrorDescriptor] = None
) -> Fatal:
    """
    Create a new Fatal error.
    
    Usage:
    1. new_fatal(message="Fatal error")
    2. new_fatal(message="Fatal", extensions={...})
    3. new_fatal(err=descriptor, extensions={...})
    
    Matches Go's NewFatal() function.
    """
    if err is not None:
        return new_error(err=err, extensions=extensions, level=LEVEL_FATAL)
    
    if message is None:
        raise ValueError("Either 'err' or 'message' must be provided")
    
    return new_error(message=message, extensions=extensions, level=LEVEL_FATAL)


def get_errors(error_list: ErrorList) -> List[Dict[str, Any]]:
    """
    Convert error list to GraphQL spec format.
    Matches Go's ErrorList.GetErrors() method.
    """
    if not error_list:
        return []
    
    return [err.error().to_dict() for err in error_list]
