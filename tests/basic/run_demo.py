from pgql import HTTPServer, AuthorizeInfo
from resolvers.gql.user.user import User
from resolvers.gql.company.company import Company

# Función de demostración que muestra todos los campos
def on_authorize(auth_info: AuthorizeInfo) -> bool:
    """Muestra todos los campos de AuthorizeInfo"""
    print(f"\n{'='*60}")
    print(f"🔐 Interceptando resolver:")
    print(f"   Operation : {auth_info.operation}")
    print(f"   Src Type  : {auth_info.src_type}")
    print(f"   Dst Type  : {auth_info.dst_type}")
    print(f"   Resolver  : {auth_info.resolver}")
    print(f"   Session ID: {auth_info.session_id}")
    print(f"   Path      : {auth_info.src_type}.{auth_info.resolver} → {auth_info.dst_type}")
    print(f"{'='*60}")
    
    return True

# Crear instancias de los resolvers
user_resolver = User()
company_resolver = Company()

server = HTTPServer('etc/http.yml')
server.on_authorize(on_authorize)
server.gql({
    'User': user_resolver,
    'Company': company_resolver
})

print("\n📌 Servidor iniciado. Ejecuta queries para ver el interceptor en acción.")
print("   Ejemplo: { getUser { id name company { id name } } }\n")

server.start()
