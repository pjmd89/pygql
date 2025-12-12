"""
Ejemplo de validación CORS dinámica con on_http_check_origin

Este ejemplo muestra cómo implementar validación de orígenes CORS
usando el callback on_http_check_origin, que recibe los orígenes
permitidos desde el archivo de configuración YAML.

Características:
- Validación dinámica de orígenes
- Combina allowed_origins del YAML con lógica personalizada
- Permite subdominios y patrones adicionales
- Logging de validaciones
"""

from pgql import HTTPServer

def check_origin(origin: str, allowed_origins: list[str]) -> bool:
    """
    Valida si un origen está permitido para acceder al API GraphQL
    
    Args:
        origin: El header Origin de la petición HTTP (ej: "http://localhost:3000")
        allowed_origins: Lista de orígenes permitidos desde el archivo YAML (cors.allowed_origins)
    
    Returns:
        True si el origen está permitido, False para bloquearlo (retorna 403)
    
    Nota:
        - allowed_origins proviene del archivo YAML
        - Puedes combinar la validación de YAML con lógica adicional
        - Si no registras esta función, solo se usa allowed_origins del YAML
    """
    print(f"🔍 Validando origin: {origin}")
    print(f"📋 Orígenes permitidos en YAML: {allowed_origins}")
    
    # 1. Validar contra la lista del YAML
    if origin in allowed_origins:
        print(f"✅ Origin permitido (en YAML): {origin}")
        return True
    
    # 2. Lógica adicional: permitir subdominios
    if origin.endswith('.midominio.com'):
        print(f"✅ Origin permitido (subdominio): {origin}")
        return True
    
    # 3. Lógica adicional: permitir localhost con cualquier puerto (HTTP/HTTPS)
    if (origin.startswith('http://localhost:') or origin.startswith('http://127.0.0.1:') or
        origin.startswith('https://localhost:') or origin.startswith('https://127.0.0.1:')):
        print(f"✅ Origin permitido (localhost): {origin}")
        return True
    
    print(f"❌ Origin rechazado: {origin}")
    return False


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
    print("\n📋 Configuración CORS:")
    print("  - Orígenes del YAML: definidos en config_cors_example.yml")
    print("  - Validación adicional: subdominios y localhost")
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
    print('  -H "Origin: http://localhost:5173"')
    print("\n# Petición preflight (OPTIONS):")
    print('curl -X OPTIONS http://localhost:8080/graphql \\')
    print('  -H "Origin: http://localhost:3000" \\')
    print('  -H "Access-Control-Request-Method: POST"')
    print("=" * 60)
    print()
    
    # Iniciar servidor
    server.start()
