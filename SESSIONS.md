# Sistema de Sesiones en pgql

## Características

- ✅ Almacenamiento de sesiones en memoria
- ✅ Creación automática de UUIDs para sesiones
- ✅ Soporte para guardar cualquier tipo de dato (variables, objetos, arrays, etc.)
- ✅ Expiración automática de sesiones
- ✅ Seteo automático de cookies en respuestas GraphQL
- ✅ Nombre de cookie configurable desde YAML
- ✅ Integración con sistema de autorización

## Configuración

Agrega el nombre de la cookie en tu archivo `config.yml`:

```yaml
http_port: 8080
cookie_name: session_id  # Nombre personalizable
debug: true
server:
  host: localhost
  routes:
    - mode: gql
      endpoint: /graphql
      schema: schema
```

## API de Sesiones

### 1. Crear una Sesión

```python
from pgql import HTTPServer, Session

server = HTTPServer('config.yml')

# Crear sesión con tiempo de vida de 1 hora (3600 segundos)
session = server.create_session(max_age=3600)

print(session.session_id)  # UUID: "bcbc0611-9f9a-491a-b17b-29fbabab03ec"
```

### 2. Guardar Datos en la Sesión

Puedes guardar **cualquier tipo de dato**:

```python
# Variables simples
session.set('user_id', 123)
session.set('username', 'john_doe')
session.set('authenticated', True)

# Arrays/Listas
session.set('roles', ['admin', 'editor', 'viewer'])
session.set('permissions', ['read', 'write', 'delete'])

# Diccionarios/Objetos
session.set('preferences', {
    'theme': 'dark',
    'language': 'es',
    'notifications': True
})

# Instancias de clases
session.set('user_object', UserModel(id=123, name='John'))

# Cualquier objeto serializable
session.set('cart', ShoppingCart())
```

### 3. Obtener Datos de la Sesión

```python
user_id = session.get('user_id')  # 123
username = session.get('username')  # 'john_doe'
roles = session.get('roles')  # ['admin', 'editor', 'viewer']

# Con valor por defecto
theme = session.get('theme', 'light')  # 'light' si no existe
```

### 4. Recuperar Sesión Existente

```python
# Por ID
session = server.get_session('bcbc0611-9f9a-491a-b17b-29fbabab03ec')

if session:
    print(f"Usuario: {session.get('username')}")
else:
    print("Sesión no encontrada o expirada")
```

### 5. Eliminar Sesión (Logout)

```python
server.delete_session(session_id)
```

### 6. Métodos Adicionales de Session

```python
# Eliminar un dato específico
session.delete('user_id')

# Limpiar todos los datos
session.clear()

# Verificar si expiró
if session.is_expired():
    print("Sesión expirada")
```

## Uso con GraphQL Resolvers

### Ejemplo: Login con Creación de Sesión

```python
from pgql import HTTPServer, AuthorizeInfo

class UserResolver:
    def __init__(self, server: HTTPServer):
        self.server = server
    
    def login(self, parent, info, username: str, password: str):
        """Mutation de login que crea sesión"""
        
        # Validar credenciales
        if self.validate_credentials(username, password):
            # Crear sesión
            session = self.server.create_session(max_age=7200)  # 2 horas
            
            # Guardar datos del usuario en la sesión
            session.set('user_id', 123)
            session.set('username', username)
            session.set('roles', ['admin'])
            session.set('authenticated', True)
            
            # Marcar sesión para setear cookie automáticamente
            info.context['new_session'] = session
            
            return {
                'success': True,
                'message': 'Login exitoso',
                'session_id': session.session_id
            }
        
        return {
            'success': False,
            'message': 'Credenciales inválidas'
        }
    
    def getUser(self, parent, info):
        """Obtener usuario desde la sesión"""
        session = info.context.get('session')
        
        if session and session.get('authenticated'):
            return {
                'id': str(session.get('user_id')),
                'name': session.get('username'),
                'roles': session.get('roles', [])
            }
        
        return None  # Usuario no autenticado
    
    def logout(self, parent, info):
        """Mutation de logout que elimina sesión"""
        session_id = info.context.get('session_id')
        
        if session_id:
            self.server.delete_session(session_id)
            return {'success': True, 'message': 'Logout exitoso'}
        
        return {'success': False, 'message': 'No hay sesión activa'}

# Inicializar servidor
server = HTTPServer('config.yml')
user_resolver = UserResolver(server)

server.gql({
    'User': user_resolver
})

server.start()
```

### Schema GraphQL Correspondiente

```graphql
type LoginResponse {
    success: Boolean!
    message: String!
    session_id: String
}

type User {
    id: ID!
    name: String!
    roles: [String!]!
}

type Mutation {
    login(username: String!, password: String!): LoginResponse!
    logout: LoginResponse!
}

type Query {
    getUser: User
}
```

## Uso desde el Cliente

### 1. Login (Crear Sesión)

```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { login(username: \"admin\", password: \"secret\") { success message session_id } }"
  }'
```

**Respuesta:**
```json
{
  "data": {
    "login": {
      "success": true,
      "message": "Login exitoso",
      "session_id": "bcbc0611-9f9a-491a-b17b-29fbabab03ec"
    }
  }
}
```

**Cookies recibidas:**
```
Set-Cookie: session_id=bcbc0611-9f9a-491a-b17b-29fbabab03ec; Max-Age=7200; HttpOnly; SameSite=lax
```

### 2. Queries Subsecuentes (Con Sesión)

El navegador/cliente enviará automáticamente la cookie:

```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -H "Cookie: session_id=bcbc0611-9f9a-491a-b17b-29fbabab03ec" \
  -d '{
    "query": "{ getUser { id name roles } }"
  }'
```

**Respuesta:**
```json
{
  "data": {
    "getUser": {
      "id": "123",
      "name": "admin",
      "roles": ["admin"]
    }
  }
}
```

### 3. Logout (Eliminar Sesión)

```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -H "Cookie: session_id=bcbc0611-9f9a-491a-b17b-29fbabab03ec" \
  -d '{
    "query": "mutation { logout { success message } }"
  }'
```

## Integración con Autorización

```python
def on_authorize(auth_info: AuthorizeInfo) -> bool:
    """Autorizar basándose en datos de sesión"""
    
    # Obtener sesión desde el servidor
    session = server.get_session(auth_info.session_id)
    
    if not session:
        return False  # Sin sesión = denegar
    
    # Verificar autenticación
    if not session.get('authenticated'):
        return False
    
    # Verificar roles para operaciones sensibles
    if auth_info.resolver in ['deleteUser', 'updateRoles']:
        roles = session.get('roles', [])
        if 'admin' not in roles:
            return False
    
    return True

server.on_authorize(on_authorize)
```

## Contexto GraphQL

Cada resolver tiene acceso al contexto con información de sesión:

```python
def my_resolver(self, parent, info):
    # session_id: UUID de la sesión (o None)
    session_id = info.context.get('session_id')
    
    # session: Objeto Session completo (o None)
    session = info.context.get('session')
    
    # request: Objeto Request de Starlette
    request = info.context.get('request')
    
    # Para setear nueva sesión (solo en respuesta)
    info.context['new_session'] = session
```

## Características de Seguridad

Las cookies se setean con:
- `HttpOnly=True` - No accesible desde JavaScript (protege contra XSS)
- `SameSite=lax` - Protección contra CSRF
- `Secure=False` - Cambiar a `True` en producción con HTTPS
- `Max-Age` - Tiempo de vida configurable

## Notas Importantes

1. **Almacenamiento en Memoria**: Las sesiones se guardan en memoria del servidor. Se pierden al reiniciar.
2. **Expiración Automática**: Las sesiones expiran después de `max_age` segundos de inactividad.
3. **Cookie Name**: Configurable en `config.yml` con `cookie_name`.
4. **Session ID**: Se genera automáticamente como UUID v4.
5. **Thread-Safe**: No implementado aún. Para producción considera usar Redis o similar.

## Ejemplo Completo

Ver `tests/basic/run_with_sessions.py` para un ejemplo completo funcional.
