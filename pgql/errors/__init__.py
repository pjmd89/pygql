"""
GraphQL error handling compatible with Go's definitionError package.
"""

from .definition_error import (
    GQLError,
    ErrorStruct,
    GQLErrorLocation,
    ExtensionError,
    ErrorLevel,
    ErrorList,
    ErrorDescriptor,
    Warning,
    Fatal,
    new_error,
    new_warning,
    new_fatal,
    get_errors,
    LEVEL_WARNING,
    LEVEL_FATAL
)

__all__ = [
    'GQLError',
    'ErrorStruct',
    'GQLErrorLocation',
    'ExtensionError',
    'ErrorLevel',
    'ErrorList',
    'ErrorDescriptor',
    'Warning',
    'Fatal',
    'new_error',
    'new_warning',
    'new_fatal',
    'get_errors',
    'LEVEL_WARNING',
    'LEVEL_FATAL'
]
