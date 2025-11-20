"""
Tests para el sistema de manejo de errores compatible con Go
"""

import sys
sys.path.insert(0, '/home/munozp/Proyectos/python/pygql')

from pgql import (
    new_warning,
    new_fatal,
    new_error,
    ErrorDescriptor,
    LEVEL_WARNING,
    LEVEL_FATAL,
    get_errors
)
from pgql.errors import Warning, Fatal


def test_warning_creation():
    print("\n🧪 Testing Warning creation...")
    
    # Test 1: new_warning sin extensions
    err = new_warning("Test warning message")
    assert isinstance(err, Warning)
    assert err.error().message == "Test warning message"
    assert err.error_level() == LEVEL_WARNING
    assert err.error().extensions is not None
    assert err.error().extensions["level"] == "warning"
    print("  ✅ PASS: new_warning() works")
    
    # Test 2: new_warning con extensions
    extensions = {"userId": "123", "field": "email"}
    err = new_warning("Invalid email", extensions)
    assert err.error().extensions["userId"] == "123"
    assert err.error().extensions["field"] == "email"
    assert err.error().extensions["level"] == "warning"
    print("  ✅ PASS: new_warning() with extensions works")


def test_fatal_creation():
    print("\n🧪 Testing Fatal creation...")
    
    # Test 1: new_fatal sin extensions
    err = new_fatal("Critical error")
    assert isinstance(err, Fatal)
    assert err.error().message == "Critical error"
    assert err.error_level() == LEVEL_FATAL
    assert err.error().extensions is not None
    assert err.error().extensions["level"] == "fatal"
    print("  ✅ PASS: new_fatal() works")
    
    # Test 2: new_fatal con extensions
    extensions = {"code": "AUTH_ERROR", "severity": "high"}
    err = new_fatal("Authentication failed", extensions)
    assert err.error().extensions["code"] == "AUTH_ERROR"
    assert err.error().extensions["severity"] == "high"
    assert err.error().extensions["level"] == "fatal"
    print("  ✅ PASS: new_fatal() with extensions works")


def test_error_descriptor():
    print("\n🧪 Testing ErrorDescriptor...")
    
    # Test 1: Warning descriptor
    descriptor = ErrorDescriptor(
        message="Field is deprecated",
        code="DEPRECATED",
        level=LEVEL_WARNING
    )
    err = new_error(descriptor)
    assert isinstance(err, Warning)
    assert err.error().message == "Field is deprecated"
    assert err.error().code == "DEPRECATED"
    print("  ✅ PASS: ErrorDescriptor with WARNING level works")
    
    # Test 2: Fatal descriptor
    descriptor = ErrorDescriptor(
        message="Schema validation failed",
        code="SCHEMA_ERROR",
        level=LEVEL_FATAL
    )
    err = new_error(descriptor, {"line": 10, "column": 5})
    assert isinstance(err, Fatal)
    assert err.error().message == "Schema validation failed"
    assert err.error().code == "SCHEMA_ERROR"
    assert err.error().extensions["line"] == 10
    print("  ✅ PASS: ErrorDescriptor with FATAL level works")


def test_error_struct_to_dict():
    print("\n🧪 Testing ErrorStruct.to_dict()...")
    
    # Test con todos los campos
    err = new_fatal("Test error")
    error_dict = err.error().to_dict()
    
    assert "message" in error_dict
    assert error_dict["message"] == "Test error"
    assert "extensions" in error_dict
    assert error_dict["extensions"]["level"] == "fatal"
    print("  ✅ PASS: ErrorStruct.to_dict() works")


def test_error_list():
    print("\n🧪 Testing ErrorList...")
    
    errors = [
        new_warning("Warning 1"),
        new_fatal("Fatal 1"),
        new_warning("Warning 2")
    ]
    
    error_dicts = get_errors(errors)
    
    assert len(error_dicts) == 3
    assert error_dicts[0]["message"] == "Warning 1"
    assert error_dicts[0]["extensions"]["level"] == "warning"
    assert error_dicts[1]["message"] == "Fatal 1"
    assert error_dicts[1]["extensions"]["level"] == "fatal"
    print("  ✅ PASS: get_errors() works")


def test_str_repr():
    print("\n🧪 Testing __str__ and __repr__...")
    
    warning = new_warning("Test warning")
    fatal = new_fatal("Test fatal")
    
    assert str(warning) == "Test warning"
    assert str(fatal) == "Test fatal"
    
    assert "WARNING" in repr(warning)
    assert "FATAL" in repr(fatal)
    print("  ✅ PASS: String representations work")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Error System")
    print("=" * 60)
    
    test_warning_creation()
    test_fatal_creation()
    test_error_descriptor()
    test_error_struct_to_dict()
    test_error_list()
    test_str_repr()
    
    print("\n" + "=" * 60)
    print("✅ All error system tests passed!")
    print("=" * 60)
