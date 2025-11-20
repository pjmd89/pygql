from pgql import HTTPServer, Session

# Crear servidor
server = HTTPServer('etc/http.yml')

# Ejemplo 1: Crear una sesión manualmente
print("\n" + "="*60)
print("Ejemplo 1: Crear sesión manualmente")
print("="*60)

session = server.create_session(max_age=3600)
print(f"Session ID: {session.session_id}")

# Guardar datos en la sesión
session.set('user_id', 123)
session.set('username', 'john_doe')
session.set('roles', ['admin', 'editor'])
session.set('preferences', {'theme': 'dark', 'language': 'es'})

print(f"Datos guardados en sesión:")
print(f"  - user_id: {session.get('user_id')}")
print(f"  - username: {session.get('username')}")
print(f"  - roles: {session.get('roles')}")
print(f"  - preferences: {session.get('preferences')}")

# Ejemplo 2: Recuperar sesión existente
print("\n" + "="*60)
print("Ejemplo 2: Recuperar sesión por ID")
print("="*60)

retrieved_session = server.get_session(session.session_id)
if retrieved_session:
    print(f"Sesión recuperada: {retrieved_session.session_id}")
    print(f"Username: {retrieved_session.get('username')}")
    print(f"Roles: {retrieved_session.get('roles')}")
else:
    print("Sesión no encontrada")

# Ejemplo 3: Modificar datos de sesión
print("\n" + "="*60)
print("Ejemplo 3: Modificar datos de sesión")
print("="*60)

retrieved_session.set('last_login', '2025-11-19 10:30:00')
retrieved_session.set('login_count', 5)
print(f"Nuevo dato agregado - last_login: {retrieved_session.get('last_login')}")
print(f"Nuevo dato agregado - login_count: {retrieved_session.get('login_count')}")

# Ejemplo 4: Eliminar sesión
print("\n" + "="*60)
print("Ejemplo 4: Eliminar sesión")
print("="*60)

server.delete_session(session.session_id)
print(f"Sesión eliminada: {session.session_id}")

# Intentar recuperar sesión eliminada
deleted_session = server.get_session(session.session_id)
print(f"Intentar recuperar sesión eliminada: {deleted_session}")  # None

print("\n" + "="*60)
print("✅ Ejemplos completados")
print("="*60 + "\n")
