from pgql import HTTPServer, AuthorizeInfo, Session
from resolvers.gql.user.user import User
from resolvers.gql.company.company import Company

# Función de autorización que usa sesiones
def on_authorize(auth_info: AuthorizeInfo) -> bool:
    """Autorización basada en sesiones"""
    print(f"🔐 Autorizando: {auth_info.src_type}.{auth_info.resolver} → {auth_info.dst_type}")
    
    # Si hay sesión, obtener datos
    if auth_info.session_id:
        print(f"   Session ID: {auth_info.session_id}")
        # Aquí podrías validar la sesión con el session store
    else:
        print(f"   Sin sesión")
    
    # Permitir todo por ahora (implementa tu lógica aquí)
    return True

# Crear instancias de los resolvers
user_resolver = User()
company_resolver = Company()

# Crear servidor
server = HTTPServer('etc/http.yml')
server.on_authorize(on_authorize)

# Ejemplo: Modificar un resolver para crear sesiones
# Necesitamos acceso al servidor en los resolvers
class UserWithSession(User):
    def __init__(self, server: HTTPServer):
        super().__init__()
        self.server = server
    
    def login(self, parent, info, username: str, password: str):
        """Resolver de login que crea una sesión"""
        # Validar credenciales (simplificado)
        if username == "admin" and password == "secret":
            # Crear nueva sesión
            session = self.server.create_session(max_age=3600)
            
            # Guardar datos en la sesión
            session.set('user_id', 1)
            session.set('username', username)
            session.set('roles', ['admin', 'user'])
            session.set('authenticated', True)
            
            # Marcar la sesión para que se setee la cookie
            info.context['new_session'] = session
            
            print(f"✅ Login exitoso. Session ID: {session.session_id}")
            
            return {
                'success': True,
                'message': 'Login exitoso',
                'session_id': session.session_id
            }
        
        return {
            'success': False,
            'message': 'Credenciales inválidas'
        }
    
    def get_user(self, parent, info):
        """Obtener usuario desde la sesión"""
        session = info.context.get('session')
        
        if session:
            user_id = session.get('user_id')
            username = session.get('username')
            roles = session.get('roles', [])
            
            return {
                'id': str(user_id),
                'name': username,
                'email': f'{username}@example.com',
                'authenticated': True,
                'roles': roles
            }
        
        # Usuario sin sesión
        return {
            'id': '0',
            'name': 'Guest',
            'email': 'guest@example.com',
            'authenticated': False
        }

# Usar resolver con sesiones
user_resolver_with_session = UserWithSession(server)

# Registrar resolvers
server.gql({
    'User': user_resolver_with_session,
    'Company': Company()
})

print("\n" + "="*60)
print("🚀 Servidor con soporte de sesiones iniciado")
print("="*60)
print("\nEjemplos de uso:")
print("\n1. Login (crear sesión):")
print('   mutation { login(username: "admin", password: "secret") { success message session_id } }')
print("\n2. Obtener usuario (usando sesión):")
print('   { getUser { id name email } }')
print("\n3. El servidor seteará automáticamente la cookie en la respuesta del login")
print("="*60 + "\n")

server.start()
