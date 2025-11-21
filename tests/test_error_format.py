#!/usr/bin/env python3
"""
Script para probar el formato de error de GraphQL con extensiones
"""

from graphql import GraphQLError

# Simular el error que se lanza en create_user
try:
    extensions = {
        'code': 'AGE_VALIDATION_FAILED',
        'field': 'age',
        'minimumAge': 30,
        'providedAge': 0,
        'birthDate': '2025-10-10'
    }
    raise GraphQLError(
        message="User must be at least 30 years old",
        extensions=extensions
    )
except GraphQLError as error:
    # Simular el formato que ahora usamos en http.py
    error_dict = {
        "message": error.message,
    }
    if hasattr(error, 'path') and error.path:
        error_dict["path"] = error.path
    if hasattr(error, 'locations') and error.locations:
        error_dict["locations"] = [{"line": loc.line, "column": loc.column} for loc in error.locations]
    if hasattr(error, 'extensions') and error.extensions:
        error_dict["extensions"] = error.extensions
    
    print("✅ Error formateado correctamente:")
    import json
    print(json.dumps(error_dict, indent=2))
    
    print("\n❌ Error formateado incorrectamente (con str()):")
    print(str(error))
