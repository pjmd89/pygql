from pgql import HTTPServer, AuthorizeInfo
from resolvers.gql.objectTypes.user.user import User
from resolvers.gql.objectTypes.company.company import Company
from resolvers.gql.scalars.date import DateScalar
# Función de autorización (opcional)
def on_authorize(auth_info: AuthorizeInfo) -> bool:
    print(f"🔐 Autorizando: {auth_info.operation} -> {auth_info.src_type}.{auth_info.resolver} → {auth_info.dst_type}")
    print(f"   Session ID: {auth_info.session_id}")
    
    print(f"   ✅ AUTORIZADO")
    return True

# Crear instancias de los resolvers
user_resolver = User()
company_resolver = Company()

server = HTTPServer('etc/http.yml')

# Registrar función de autorización (opcional - comentar para desactivar)
server.on_authorize(on_authorize)

server.scalar("Date", DateScalar())
# Registrar resolvers
server.gql({
    'User': user_resolver,
    'Company': company_resolver
})

server.start()