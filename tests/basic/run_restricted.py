from pgql import HTTPServer, AuthorizeInfo
from resolvers.gql.user.user import User
from resolvers.gql.company.company import Company

# Función de autorización más restrictiva
def on_authorize(auth_info: AuthorizeInfo) -> bool:
    """
    Ejemplo de autorización más restrictiva
    """
    print(f"🔐 Autorizando: {auth_info.operation} -> {auth_info.src_type}.{auth_info.resolver} → {auth_info.dst_type}")
    print(f"   Session ID: {auth_info.session_id}")
    
    # Denegar acceso si no hay session_id
    if not auth_info.session_id:
        print(f"   ❌ DENEGADO: No hay session_id")
        return False
    
    # Denegar acceso a Company.company cuando se invoca desde User para usuarios sin sesión especial
    if auth_info.src_type == "User" and auth_info.resolver == "company" and auth_info.dst_type == "Company":
        if auth_info.session_id != "admin123":
            print(f"   ❌ DENEGADO: Solo admin puede acceder a User.company")
            return False
    
    print(f"   ✅ AUTORIZADO")
    return True

# Crear instancias de los resolvers
user_resolver = User()
company_resolver = Company()

server = HTTPServer('etc/http.yml')

# Registrar función de autorización
server.on_authorize(on_authorize)

# Registrar resolvers
server.gql({
    'User': user_resolver,
    'Company': company_resolver
})

server.start()
