"""
pgql - A Python GraphQL package
"""

__version__ = "0.5.1"

from .http.http import HTTPServer
from .http.authorize_info import AuthorizeInfo
from .http.session import Session
from .resolvers.base import Scalar, ScalarResolved, ResolverInfo
from .directives import Directive, DirectiveList
from .errors import (
    GQLError,
    ErrorStruct,
    GQLErrorLocation,
    ExtensionError,
    ErrorLevel,
    ErrorList,
    Warning,
    Fatal,
    ErrorDescriptor,
    new_error,
    new_warning,
    new_fatal,
    get_errors,
    LEVEL_WARNING,
    LEVEL_FATAL
)

__all__ = [
    "HTTPServer",
    "AuthorizeInfo",
    "Session",
    "Scalar",
    "ScalarResolved",
    "ResolverInfo",
    "Directive",
    "DirectiveList",
    "GQLError",
    "ErrorStruct",
    "GQLErrorLocation",
    "ExtensionError",
    "ErrorLevel",
    "ErrorList",
    "Warning",
    "Fatal",
    "ErrorDescriptor",
    "new_error",
    "new_warning",
    "new_fatal",
    "get_errors",
    "LEVEL_WARNING",
    "LEVEL_FATAL"
]