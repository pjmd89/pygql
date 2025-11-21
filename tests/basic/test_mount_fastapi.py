"""
Test de mount() - Integración pygql + FastAPI
"""
from fastapi import FastAPI
from pgql import HTTPServer

# Crear aplicación FastAPI
fastapi_app = FastAPI(title="FastAPI App")

@fastapi_app.get("/")
def root():
    return {"message": "Hello from FastAPI!"}

@fastapi_app.get("/users")
def get_users():
    return {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"}
        ]
    }

@fastapi_app.post("/users")
def create_user(name: str):
    return {"id": 4, "name": name, "created": True}

# Crear servidor pygql
server = HTTPServer('etc/http.yml')

# Importar y crear resolvers
from resolvers.gql.objectTypes.user.user import User
from resolvers.gql.objectTypes.company.company import Company
from resolvers.gql.scalars.date import DateScalar

user_resolver = User()
company_resolver = Company()

# Registrar scalar y resolvers
server.scalar("Date", DateScalar())
server.gql({
    'User': user_resolver,
    'Company': company_resolver
})

# Montar FastAPI en /api
server.mount("/api", fastapi_app, name="fastapi")

# Mensaje de ayuda
print("\n" + "="*60)
print("🚀 Servidor híbrido pygql + FastAPI iniciado")
print("="*60)
print("\nEndpoints disponibles:")
print("  GraphQL:")
print("    POST http://localhost:8080/graphql")
print("\n  FastAPI:")
print("    GET  http://localhost:8080/api/")
print("    GET  http://localhost:8080/api/users")
print("    POST http://localhost:8080/api/users?name=David")
print("\nPruebas:")
print("  # GraphQL")
print('  curl -X POST http://localhost:8080/graphql -H "Content-Type: application/json" -d \'{"query": "{ getUser(id: \\"1\\") { id name email } }"}\'')
print('  curl -X POST http://localhost:8080/graphql -H "Content-Type: application/json" -d \'{"query": "{ getUsers { id name } }"}\'')
print("\n  # FastAPI")
print('  curl http://localhost:8080/api/')
print('  curl http://localhost:8080/api/users')
print('  curl -X POST "http://localhost:8080/api/users?name=David"')
print("="*60 + "\n")

if __name__ == '__main__':
    server.start()
