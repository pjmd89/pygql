"""
Ejemplo de validación CORS dinámica con on_http_check_origin

Este ejemplo muestra cómo implementar validación de orígenes CORS
usando el callback on_http_check_origin, similar al patrón on_authorize.

Características:
- Validación dinámica de orígenes
- Lista blanca de dominios permitidos
- Comportamiento permisivo por defecto
- Logging de validaciones
"""

from pgql import HTTPServer

# Lista de orígenes permitidos (whitelist)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite
    "https://myapp.com",
    "https://app.example.com"
]

def check_origin(origin: str) -> bool:
    """
    Valida si un origen está permitido para acceder al API GraphQL
    
    Args:
        origin: El header Origin de la petición HTTP (ej: "http://localhost:3000")
    
    Returns:
        True si el origen está permitido, False para bloquearlo (retorna 403)
    
    Nota:
        Por defecto, si no registras esta función, todos los orígenes 
        están permitidos (comportamiento permisivo).
    """
    print(f"🔍 Validando origin: {origin}")
    
    is_allowed = origin in ALLOWED_ORIGINS
    
    if is_allowed:
        print(f"✅ Origin permitido: {origin}")
    else:
        print(f"❌ Origin rechazado: {origin}")
    
    return is_allowed


# Resolvers de ejemplo
class User:
    def get_users(self, parent, info):
        """Resolver para Query.getUsers"""
        return [
            {'id': '1', 'name': 'Jose', 'email': 'jose@example.com'},
            {'id': '2', 'name': 'Mario', 'email': 'mario@example.com'}
        ]
    
    def get_user(self, parent, info, id):
        """Resolver para Query.getUser"""
        users = {
            '1': {'id': '1', 'name': 'Jose', 'email': 'jose@example.com'},
            '2': {'id': '2', 'name': 'Mario', 'email': 'mario@example.com'}
        }
        return users.get(id)


if __name__ == '__main__':
    # Crear servidor HTTP
    server = HTTPServer('etc/http.yml')
    
    # Registrar validador CORS
    server.on_http_check_origin(check_origin)
    
    # Registrar resolvers
    user_resolver = User()
    server.gql({'User': user_resolver})
    
    print("=" * 60)
    print("🚀 Servidor GraphQL con validación CORS iniciado")
    print("=" * 60)
    print("\nEndpoint GraphQL:")
    print("  POST http://localhost:8080/graphql")
    print("\nOrígenes permitidos:")
    for origin in ALLOWED_ORIGINS:
        print(f"  ✅ {origin}")
    print("\n🧪 Pruebas:")
    print("\n# Origen permitido (retorna 200 con headers CORS):")
    print('curl -X POST http://localhost:8080/graphql \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -H "Origin: http://localhost:3000" \\')
    print('  -d \'{"query": "{ getUsers { id name email } }"}\'')
    print("\n# Origen bloqueado (retorna 403):")
    print('curl -X POST http://localhost:8080/graphql \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -H "Origin: http://malicious-site.com" \\')
    print('  -d \'{"query": "{ getUsers { id name email } }"}\'')
    print("\n# Ver headers CORS en respuesta:")
    print('curl -I -X POST http://localhost:8080/graphql \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -H "Origin: https://myapp.com"')
    print("\n# Petición preflight (OPTIONS):")
    print('curl -X OPTIONS http://localhost:8080/graphql \\')
    print('  -H "Origin: http://localhost:3000" \\')
    print('  -H "Access-Control-Request-Method: POST"')
    print("=" * 60)
    print()
    
    # Iniciar servidor
    server.start()
