"""
Test de on_http_check_origin - Validación dinámica de CORS

Este test demuestra las nuevas características de CORS:
1. Configuración de allowed_origins en YAML
2. Validación dinámica con callback que recibe allowed_origins
3. Combinación de validación estática (YAML) + dinámica (código)
4. Headers CORS configurables desde YAML
"""

from pgql import HTTPServer
from resolvers.gql.objectTypes.user.user import User

def check_origin(origin: str, allowed_origins: list[str]) -> bool:
    """
    Función personalizada para validar orígenes CORS
    
    Args:
        origin: El origin del request (ej: "http://localhost:3000")
        allowed_origins: Lista de orígenes permitidos desde el archivo YAML
    
    Returns:
        True si el origin está permitido, False si no
    """
    print(f"\n{'='*60}")
    print(f"🔍 Validando CORS para origin: {origin}")
    print(f"📋 Orígenes en YAML: {allowed_origins}")
    print(f"{'='*60}")
    
    # Acepta tanto HTTP como HTTPS en localhost
    if (origin.startswith('http://localhost:') or origin.startswith('http://127.0.0.1:') or
        origin.startswith('https://localhost:') or origin.startswith('https://127.0.0.1:')):
        print(f"✅ Origin permitido (localhost en cualquier puerto)")
        return True
    
    if origin in allowed_origins:
        print(f"✅ Origin permitido (encontrado en YAML)")
        return True
    # Rechazar todo lo demás
    print(f"❌ Origin RECHAZADO - No cumple ninguna regla")
    return False

# Crear servidor
server = HTTPServer('etc/http.yml')

# Registrar función de validación CORS
server.on_http_check_origin(check_origin)

# Registrar resolvers
user_resolver = User()
server.gql({'User': user_resolver})

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 SERVIDOR CON VALIDACIÓN CORS AVANZADA")
    print("="*80)
    
    print("\n📋 CONFIGURACIÓN CORS (desde etc/http.yml):")
    print("  • Headers CORS configurables (allow_methods, allow_headers, etc.)")
    print("  • Lista de orígenes permitidos (allowed_origins)")
    print("  • Max-Age para cache de preflight")
    
    print("\n🔒 REGLAS DE VALIDACIÓN:")
    print("  1️⃣  Orígenes definidos en YAML (allowed_origins)")
    print("  2️⃣  Subdominios de .midominio.com")
    print("  3️⃣  Localhost en cualquier puerto HTTP/HTTPS (desarrollo)")
    print("  4️⃣  HTTPS en subdominios de .ejemplo.com")
    
    print("\n" + "="*80)
    print("🧪 PRUEBAS DE VALIDACIÓN CORS")
    print("="*80)
    
    print("\n✅ CASOS QUE DEBEN SER PERMITIDOS:")
    print("\n  1. Origin en lista YAML (localhost:3000):")
    print('     curl -X POST http://localhost:8080/graphql \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -H "Origin: http://localhost:3000" \\')
    print('       -d \'{"query": "{ getUsers { id name } }"}\'')
    
    print("\n  2. Origin en lista YAML (localhost:5173 - Vite):")
    print('     curl -X POST http://localhost:8080/graphql \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -H "Origin: http://localhost:5173" \\')
    print('       -d \'{"query": "{ getUsers { id name } }"}\'')
    
    print("\n  3. Localhost en puerto diferente HTTP (regla dinámica):")
    print('     curl -X POST http://localhost:8080/graphql \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -H "Origin: http://localhost:9999" \\')
    print('       -d \'{"query": "{ getUsers { id name } }"}\'')
    
    print("\n  3b. Localhost en HTTPS (regla dinámica):")
    print('     curl -X POST http://localhost:8080/graphql \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -H "Origin: https://localhost:3001" \\')
    print('       -d \'{"query": "{ getUsers { id name } }"}\'')
    
    print("\n  4. Subdominio de .midominio.com (regla dinámica):")
    print('     curl -X POST http://localhost:8080/graphql \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -H "Origin: https://app.midominio.com" \\')
    print('       -d \'{"query": "{ getUsers { id name } }"}\'')
    
    print("\n  5. HTTPS subdominio de .ejemplo.com (regla dinámica):")
    print('     curl -X POST http://localhost:8080/graphql \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -H "Origin: https://beta.ejemplo.com" \\')
    print('       -d \'{"query": "{ getUsers { id name } }"}\'')
    
    print("\n❌ CASOS QUE DEBEN SER RECHAZADOS (403 Forbidden):")
    print("\n  1. Origin no permitido:")
    print('     curl -X POST http://localhost:8080/graphql \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -H "Origin: http://malicious-site.com" \\')
    print('       -d \'{"query": "{ getUsers { id name } }"}\'')
    
    print("\n  2. HTTP (no HTTPS) en subdominio de ejemplo.com:")
    print('     curl -X POST http://localhost:8080/graphql \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -H "Origin: http://beta.ejemplo.com" \\')
    print('       -d \'{"query": "{ getUsers { id name } }"}\'')
    
    print("\n🔍 VER HEADERS CORS EN RESPUESTA:")
    print('     curl -i -X POST http://localhost:8080/graphql \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -H "Origin: http://localhost:3000" \\')
    print('       -d \'{"query": "{ getUsers { id name } }"}\'')
    
    print("\n⚙️  PREFLIGHT REQUEST (OPTIONS):")
    print('     curl -X OPTIONS http://localhost:8080/graphql \\')
    print('       -H "Origin: http://localhost:3000" \\')
    print('       -H "Access-Control-Request-Method: POST" \\')
    print('       -H "Access-Control-Request-Headers: Content-Type" \\')
    print('       -v')
    
    print("\n" + "="*80)
    print("🎯 NOTA: Observa los logs de validación en la consola cuando hagas requests")
    print("="*80 + "\n")
    
    server.start()
