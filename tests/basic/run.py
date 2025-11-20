from pgql import HTTPServer, AuthorizeInfo
from resolvers.gql.user.user import User
from resolvers.gql.company.company import Company

# Función de autorización (opcional)
def on_authorize(auth_info: AuthorizeInfo) -> bool:
    """
    Intercepta cada llamada a un resolver para verificar autorización
    
    Args:
        auth_info: Información sobre la operación siendo ejecutada
        
    Returns:
        True si el resolver debe ejecutarse, False si se debe denegar
    """
    print(f"🔐 Autorizando: {auth_info.operation} -> {auth_info.src_type}.{auth_info.resolver} → {auth_info.dst_type}")
    print(f"   Session ID: {auth_info.session_id}")
    
    # Ejemplo: Denegar acceso si no hay session_id
    # if not auth_info.session_id:
    #     print(f"   ❌ DENEGADO: No hay session_id")
    #     return False
    
    # Ejemplo: Denegar acceso cuando se invoca company desde User
    # if auth_info.src_type == "User" and auth_info.resolver == "company":
    #     print(f"   ❌ DENEGADO: No tiene acceso a User.company")
    #     return False
    
    print(f"   ✅ AUTORIZADO")
    return True

# Crear instancias de los resolvers
user_resolver = User()
company_resolver = Company()

server = HTTPServer('etc/http.yml')

# Registrar función de autorización (opcional - comentar para desactivar)
server.on_authorize(on_authorize)

# Registrar resolvers
server.gql({
    'User': user_resolver,
    'Company': company_resolver
})

server.start()