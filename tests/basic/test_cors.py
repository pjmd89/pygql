"""
Test de on_http_check_origin - Validación dinámica de CORS
"""

from pgql import HTTPServer
from resolvers.gql.objectTypes.user.user import User

# Lista blanca de orígenes permitidos
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://miapp.com",
    "https://app.ejemplo.com"
]

def check_origin(origin: str) -> bool:
    """
    Función personalizada para validar orígenes CORS
    
    Args:
        origin: El origin del request (ej: "http://localhost:3000")
    
    Returns:
        True si el origin está permitido, False si no
    """
    print(f"🔍 Validando origin: {origin}")
    
    # Permitir origins en la lista blanca
    is_allowed = origin in ALLOWED_ORIGINS
    
    if is_allowed:
        print(f"✅ Origin permitido: {origin}")
    else:
        print(f"❌ Origin rechazado: {origin}")
    
    return is_allowed

# Crear servidor
server = HTTPServer('etc/http.yml')

# Registrar función de validación CORS
server.on_http_check_origin(check_origin)

# Registrar resolvers
user_resolver = User()
server.gql({'User': user_resolver})

if __name__ == "__main__":
    print("="*60)
    print("🚀 Servidor con validación CORS iniciado")
    print("="*60)
    print("\nOrígenes permitidos:")
    for origin in ALLOWED_ORIGINS:
        print(f"  ✅ {origin}")
    print("\n" + "="*60)
    print("\nPruebas:")
    print("\n  # Desde origin permitido (localhost:3000)")
    print('  curl -H "Origin: http://localhost:3000" http://localhost:8080/graphql')
    print("\n  # Desde origin NO permitido")
    print('  curl -H "Origin: http://malicious-site.com" http://localhost:8080/graphql')
    print("\n  # GraphQL query desde origin permitido")
    print('  curl -X POST http://localhost:8080/graphql \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -H "Origin: http://localhost:3000" \\')
    print('    -d \'{"query": "{ getUsers { id name } }"}\'')
    print("\n" + "="*60 + "\n")
    
    server.start()
