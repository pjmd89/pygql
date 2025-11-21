"""
Prueba de flexibilidad de las funciones de error
"""

import sys
sys.path.insert(0, '/home/munozp/Proyectos/python/pygql')

from pgql import (
    new_error,
    new_warning,
    new_fatal,
    ErrorDescriptor,
    LEVEL_WARNING,
    LEVEL_FATAL
)

print("=" * 60)
print("Testing Error Flexibility")
print("=" * 60)

# 1. new_fatal con solo mensaje
print("\n1️⃣  new_fatal con solo mensaje:")
err = new_fatal(message="Critical error occurred")
print(f"   Message: {err.error().message}")
print(f"   Code: {err.error().code}")
print(f"   Extensions: {err.error().extensions}")

# 2. new_fatal con mensaje y extensions
print("\n2️⃣  new_fatal con mensaje y extensions:")
err = new_fatal(
    message="Database connection failed",
    extensions={'host': 'localhost', 'port': 5432}
)
print(f"   Message: {err.error().message}")
print(f"   Extensions: {err.error().extensions}")

# 3. new_fatal con ErrorDescriptor
print("\n3️⃣  new_fatal con ErrorDescriptor:")
descriptor = ErrorDescriptor(
    message="User must be at least 30 years old",
    code="AGE_VALIDATION_FAILED",
    level=LEVEL_FATAL
)
err = new_fatal(err=descriptor)
print(f"   Message: {err.error().message}")
print(f"   Code: {err.error().code}")
print(f"   Extensions: {err.error().extensions}")

# 4. new_fatal con ErrorDescriptor + extensions adicionales
print("\n4️⃣  new_fatal con ErrorDescriptor + extensions:")
err = new_fatal(
    err=descriptor,
    extensions={'minimumAge': 30, 'providedAge': 25}
)
print(f"   Message: {err.error().message}")
print(f"   Code: {err.error().code}")
print(f"   Extensions: {err.error().extensions}")

# 5. new_warning con solo mensaje
print("\n5️⃣  new_warning con solo mensaje:")
err = new_warning(message="Field is deprecated")
print(f"   Message: {err.error().message}")
print(f"   Level: {err.error_level()}")
print(f"   Extensions: {err.error().extensions}")

# 6. new_error con mensaje y level
print("\n6️⃣  new_error con mensaje y level:")
err = new_error(
    message="Custom error",
    code="CUSTOM_001",
    level=LEVEL_FATAL
)
print(f"   Message: {err.error().message}")
print(f"   Code: {err.error().code}")
print(f"   Level: {err.error_level()}")

# 7. new_error con ErrorDescriptor
print("\n7️⃣  new_error con ErrorDescriptor:")
descriptor = ErrorDescriptor(
    message="Schema validation failed",
    code="SCHEMA_ERROR",
    level=LEVEL_WARNING
)
err = new_error(err=descriptor)
print(f"   Message: {err.error().message}")
print(f"   Code: {err.error().code}")
print(f"   Level: {err.error_level()}")

print("\n" + "=" * 60)
print("✅ All flexibility tests passed!")
print("=" * 60)
