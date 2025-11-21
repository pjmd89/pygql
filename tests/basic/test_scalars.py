"""
Unit tests para Custom Scalars
"""

import sys
sys.path.insert(0, '/home/munozp/Proyectos/python/pygql')

# Importar directamente desde el módulo base sin cargar HTTPServer
from pgql.graphql.resolvers.base import Scalar, ScalarResolved
from pgql import new_warning, new_fatal
from datetime import datetime
from urllib.parse import urlparse
import json


# 1. DateScalar
class DateScalar(Scalar):
    def set(self, value):
        if value is None:
            return None, None
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d"), None
        return str(value), None
    
    def assess(self, resolved):
        if resolved.value is None:
            return None, None
        try:
            if isinstance(resolved.value, str):
                return datetime.strptime(resolved.value, "%Y-%m-%d"), None
            return None, new_fatal(f"Expected string, got {type(resolved.value).__name__}")
        except ValueError:
            return None, new_warning(f"Invalid date format: {resolved.value}")


# 2. URLScalar
class URLScalar(Scalar):
    def set(self, value):
        if value is None:
            return None, None
        return str(value), None
    
    def assess(self, resolved):
        if resolved.value is None:
            return None, None
        try:
            url = str(resolved.value)
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return None, new_warning(f"Invalid URL: {url}")
            return url, None
        except Exception as e:
            return None, new_fatal(f"URL parsing error: {e}")


# 3. JSONScalar
class JSONScalar(Scalar):
    def set(self, value):
        if value is None:
            return None, None
        return value, None
    
    def assess(self, resolved):
        if resolved.value is None:
            return None, None
        if isinstance(resolved.value, (dict, list)):
            return resolved.value, None
        if isinstance(resolved.value, str):
            try:
                return json.loads(resolved.value), None
            except json.JSONDecodeError as e:
                return None, new_warning(f"Invalid JSON: {e}")
        return None, new_warning("Expected JSON object or string")


# Tests
def test_date_scalar():
    print("\n🧪 Testing DateScalar...")
    scalar = DateScalar()
    
    # Test 1: assess() con input válido
    print("  Test 1: assess() valid input")
    resolved = ScalarResolved(value="2025-11-19", resolver_name="test")
    result, error = scalar.assess(resolved)
    assert error is None, f"Expected no error, got {error}"
    assert isinstance(result, datetime), f"Expected datetime, got {type(result)}"
    assert result.year == 2025
    assert result.month == 11
    assert result.day == 19
    print("    ✅ PASS: '2025-11-19' → datetime(2025, 11, 19)")
    
    # Test 2: set() con datetime
    print("  Test 2: set() datetime output")
    dt = datetime(2025, 11, 19, 10, 30, 0)
    result, error = scalar.set(dt)
    assert error is None, f"Expected no error, got {error}"
    assert result == "2025-11-19", f"Expected '2025-11-19', got {result}"
    print("    ✅ PASS: datetime(2025, 11, 19) → '2025-11-19'")
    
    # Test 3: assess() con formato inválido
    print("  Test 3: assess() invalid format")
    resolved = ScalarResolved(value="invalid-date", resolver_name="test")
    result, error = scalar.assess(resolved)
    assert result is None, f"Expected None, got {result}"
    assert error is not None, "Expected error"
    from pgql import Warning
    assert isinstance(error, Warning), f"Expected Warning, got {type(error)}"
    print(f"    ✅ PASS: 'invalid-date' → Error: {error}")
    
    # Test 4: set() con None
    print("  Test 4: set() None value")
    result, error = scalar.set(None)
    assert result is None
    assert error is None
    print("    ✅ PASS: None → (None, None)")
    
    # Test 5: assess() con None
    print("  Test 5: assess() None value")
    resolved = ScalarResolved(value=None, resolver_name="test")
    result, error = scalar.assess(resolved)
    assert result is None
    assert error is None
    print("    ✅ PASS: None → (None, None)")
    
    print("  ✅ DateScalar: All tests passed!")


def test_url_scalar():
    print("\n🧪 Testing URLScalar...")
    scalar = URLScalar()
    
    # Test 1: assess() URL válida
    print("  Test 1: assess() valid URL")
    resolved = ScalarResolved(value="https://example.com", resolver_name="test")
    result, error = scalar.assess(resolved)
    assert error is None, f"Expected no error, got {error}"
    assert result == "https://example.com"
    print("    ✅ PASS: 'https://example.com' → valid")
    
    # Test 2: assess() URL con path
    print("  Test 2: assess() URL with path")
    resolved = ScalarResolved(value="https://example.com/path/to/page", resolver_name="test")
    result, error = scalar.assess(resolved)
    assert error is None
    assert result == "https://example.com/path/to/page"
    print("    ✅ PASS: URL with path → valid")
    
    # Test 3: assess() URL inválida (sin scheme)
    print("  Test 3: assess() invalid URL (no scheme)")
    resolved = ScalarResolved(value="example.com", resolver_name="test")
    result, error = scalar.assess(resolved)
    assert result is None
    assert error is not None
    print(f"    ✅ PASS: 'example.com' → Error: {error}")
    
    # Test 4: assess() URL inválida (solo scheme)
    print("  Test 4: assess() invalid URL (only scheme)")
    resolved = ScalarResolved(value="http://", resolver_name="test")
    result, error = scalar.assess(resolved)
    assert result is None
    assert error is not None
    print(f"    ✅ PASS: 'http://' → Error: {error}")
    
    # Test 5: set() URL
    print("  Test 5: set() URL")
    result, error = scalar.set("https://example.com")
    assert error is None
    assert result == "https://example.com"
    print("    ✅ PASS: set() returns string")
    
    print("  ✅ URLScalar: All tests passed!")


def test_json_scalar():
    print("\n🧪 Testing JSONScalar...")
    scalar = JSONScalar()
    
    # Test 1: assess() dict
    print("  Test 1: assess() dict object")
    resolved = ScalarResolved(value={"key": "value"}, resolver_name="test")
    result, error = scalar.assess(resolved)
    assert error is None
    assert result == {"key": "value"}
    print("    ✅ PASS: dict → dict")
    
    # Test 2: assess() list
    print("  Test 2: assess() list object")
    resolved = ScalarResolved(value=[1, 2, 3], resolver_name="test")
    result, error = scalar.assess(resolved)
    assert error is None
    assert result == [1, 2, 3]
    print("    ✅ PASS: list → list")
    
    # Test 3: assess() JSON string
    print("  Test 3: assess() JSON string")
    resolved = ScalarResolved(value='{"name": "John", "age": 30}', resolver_name="test")
    result, error = scalar.assess(resolved)
    assert error is None
    assert result == {"name": "John", "age": 30}
    print("    ✅ PASS: JSON string → dict")
    
    # Test 4: assess() invalid JSON string
    print("  Test 4: assess() invalid JSON")
    resolved = ScalarResolved(value='{invalid json}', resolver_name="test")
    result, error = scalar.assess(resolved)
    assert result is None
    assert error is not None
    print(f"    ✅ PASS: invalid JSON → Error: {error}")
    
    # Test 5: set() dict
    print("  Test 5: set() dict")
    result, error = scalar.set({"foo": "bar"})
    assert error is None
    assert result == {"foo": "bar"}
    print("    ✅ PASS: set() returns object")
    
    print("  ✅ JSONScalar: All tests passed!")


def test_scalar_resolved():
    print("\n🧪 Testing ScalarResolved dataclass...")
    
    # Test 1: Crear instancia
    print("  Test 1: Create instance")
    resolved = ScalarResolved(
        value="test_value",
        resolver_name="test_resolver",
        resolved={"parent": "data"}
    )
    assert resolved.value == "test_value"
    assert resolved.resolver_name == "test_resolver"
    assert resolved.resolved == {"parent": "data"}
    print("    ✅ PASS: ScalarResolved instance created")
    
    # Test 2: Default value para resolved
    print("  Test 2: Default resolved value")
    resolved = ScalarResolved(
        value="test",
        resolver_name="resolver"
    )
    assert resolved.resolved is None
    print("    ✅ PASS: resolved defaults to None")
    
    print("  ✅ ScalarResolved: All tests passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Running Custom Scalar Unit Tests")
    print("=" * 60)
    
    try:
        test_scalar_resolved()
        test_date_scalar()
        test_url_scalar()
        test_json_scalar()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
