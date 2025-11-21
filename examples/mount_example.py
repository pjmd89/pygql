"""
Ejemplo de integración de pygql con FastAPI usando mount()

Este ejemplo muestra cómo combinar pygql GraphQL con una aplicación
FastAPI existente en un único servidor Uvicorn.
"""

from fastapi import FastAPI
from pgql import HTTPServer

# ============================================================================
# 1. Crear aplicación FastAPI
# ============================================================================

fastapi_app = FastAPI(title="My API")

# Datos de ejemplo para FastAPI
users_db = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
    {"id": 3, "name": "Charlie"}
]

@fastapi_app.get("/api/")
async def read_root():
    """Endpoint raíz de FastAPI"""
    return {"message": "Hello from FastAPI!", "version": "1.0"}

@fastapi_app.get("/api/users")
async def get_users():
    """Obtener lista de usuarios"""
    return {"users": users_db}

@fastapi_app.post("/api/users")
async def create_user(name: str):
    """Crear nuevo usuario"""
    new_user = {"id": len(users_db) + 1, "name": name}
    users_db.append(new_user)
    return {"created": True, "user": new_user}

@fastapi_app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Obtener usuario por ID"""
    user = next((u for u in users_db if u["id"] == user_id), None)
    if user:
        return user
    return {"error": "User not found"}, 404

# ============================================================================
# 2. Crear resolver GraphQL simple
# ============================================================================

class UserResolver:
    """Resolver simple para GraphQL"""
    
    def getUsers(self, parent, info):
        """Query: getUsers"""
        return [
            {"id": "1", "name": "John Doe", "email": "john@example.com"},
            {"id": "2", "name": "Jane Smith", "email": "jane@example.com"}
        ]
    
    def getUser(self, parent, info):
        """Query: getUser (sin argumentos por simplicidad)"""
        return {"id": "1", "name": "John Doe", "email": "john@example.com"}

# ============================================================================
# 3. Configurar pygql y montar FastAPI
# ============================================================================

# Crear servidor pygql (asegúrate de tener config.yml configurado)
server = HTTPServer('etc/http.yml')

# Registrar resolvers GraphQL
user_resolver = UserResolver()
server.gql({'User': user_resolver})

# Montar la aplicación FastAPI en /api
server.mount("/api", fastapi_app, name="fastapi")

# ============================================================================
# 4. Iniciar servidor único
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🚀 Servidor híbrido pygql + FastAPI iniciado")
    print("="*60)
    print("\nEndpoints disponibles:")
    print("  GraphQL:")
    print("    POST http://localhost:8080/graphql")
    print("\n  FastAPI:")
    print("    GET  http://localhost:8080/api/")
    print("    GET  http://localhost:8080/api/users")
    print("    POST http://localhost:8080/api/users?name=David")
    print("    GET  http://localhost:8080/api/users/1")
    print("\nPruebas:")
    print("  # GraphQL")
    print('  curl -X POST http://localhost:8080/graphql -H "Content-Type: application/json" -d \'{"query": "{ getUsers { id name email } }"}\'')
    print("\n  # FastAPI")
    print('  curl http://localhost:8080/api/')
    print('  curl http://localhost:8080/api/users')
    print('  curl -X POST "http://localhost:8080/api/users?name=David"')
    print('  curl http://localhost:8080/api/users/1')
    print("="*60 + "\n")
    
    server.start()
