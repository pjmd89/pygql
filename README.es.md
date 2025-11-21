# pgql

Un framework ligero de servidor GraphQL en Python con mapeo automático de resolvers, introspección de esquemas y soporte integrado para Starlette/Uvicorn.

## Características

- 🚀 **Mapeo Automático de Resolvers**: Mapea métodos de clases Python a campos GraphQL basándose en tipos de retorno
- 📁 **Carga Recursiva de Esquemas**: Organiza tus archivos de esquema `.gql` en directorios anidados
- 🔍 **Introspección Integrada**: Soporte completo de introspección GraphQL listo para usar
- 🎯 **Resolvers Basados en Instancias**: Usa instancias de clases para resolvers con estado e inyección de dependencias
- ⚡ **Soporte Asíncrono**: Construido sobre Starlette y Uvicorn para manejo asíncrono de alto rendimiento
- 🔧 **Configuración YAML**: Configuración simple del servidor basada en YAML
- 📦 **Soporte de Tipos**: Soporte completo para `extend type`, tipos anidados y modificadores de tipos GraphQL
- 🔐 **Sistema de Autorización**: Intercepta llamadas a resolvers con la función `on_authorize`
- 🍪 **Gestión de Sesiones**: Almacén de sesiones integrado con manejo automático de cookies

## Instalación

```bash
pip install pgql
```

## Inicio Rápido

### 1. Define tu Esquema GraphQL

Crea tus archivos de esquema en una estructura de directorios:

```
schema/
├── schema.gql
└── user/
    ├── types.gql
    └── queries.gql
```

**schema/schema.gql:**
```graphql
schema {
    query: Query
}
```

**schema/user/types.gql:**
```graphql
type User {
    id: ID!
    name: String!
    email: String!
}
```

**schema/user/queries.gql:**
```graphql
extend type Query {
    getUser(id: ID!): User!
    getUsers: [User!]!
}
```

### 2. Crea Clases Resolver

```python
# resolvers/user.py
from pgql import ResolverInfo

class User:
    def get_user(self, info: ResolverInfo):
        """
        Resolvers reciben SOLO info (estilo Go)
        - Parent: info.parent
        - Argumentos: info.args (snake_case)
        - Sesión: info.session_id
        
        GraphQL: getUser(userId: ID!)
        Python: info.args.get('user_id')
        """
        user_id = info.args.get('user_id')
        
        # Acceso a sesión y contexto
        if info.session_id:
            print(f"Usuario autenticado: {info.session_id}")
        
        return {
            'id': user_id, 
            'name': 'John Doe', 
            'email': 'john@example.com'
        }
    
    def get_users(self, info: ResolverInfo):
        return [
            {'id': 1, 'name': 'John', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane', 'email': 'jane@example.com'}
        ]
```

> **💡 Nota**: Resolvers reciben **solo `info`** (compatible con Go):
> - `info.parent`: Valor del parent
> - `info.args`: Argumentos (snake_case)
> - `info.operation`: "query"/"mutation"/"subscription"
> - `info.session_id`: ID de sesión
> - `info.type_name`: Tipo GraphQL actual
> - Ver [RESOLVER_INFO.md](RESOLVER_INFO.md) para más detalles

### 3. Configura el Servidor

**config.yml:**
```yaml
http_port: 8080
debug: true
server:
  host: localhost
  routes:
    - mode: gql
      endpoint: /graphql
      schema: schema  # Ruta al directorio de esquemas
```

### 4. Inicia el Servidor

```python
from pgql import HTTPServer
from resolvers.user import User

# Crear instancias de resolvers
user_resolver = User()

# Inicializar servidor
server = HTTPServer('config.yml')

# Mapear resolvers a tipos GraphQL
server.gql({
    'User': user_resolver
})

# Iniciar servidor
server.start()
```

### 5. Consulta tu API

```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ getUsers { id name email } }"}'
```

**Respuesta:**
```json
{
  "data": {
    "getUsers": [
      {"id": "1", "name": "John", "email": "john@example.com"},
      {"id": "2", "name": "Jane", "email": "jane@example.com"}
    ]
  }
}
```

## Cómo Funciona

### Mapeo Automático de Resolvers

pgql mapea automáticamente métodos de resolver a campos GraphQL basándose en **tipos de retorno**:

1. Si `Query.getUser` retorna tipo `User`, pgql busca un método llamado `getUser` en la clase resolver `User`
2. El mapeo funciona recursivamente para tipos anidados (ej: `User.company` → `Company.company`)

**Ejemplo:**

```graphql
type User {
    id: ID!
    company: Company!
}

type Company {
    id: ID!
    name: String!
}

type Query {
    getUser: User!
}
```

```python
class User:
    def getUser(self, parent, info):
        return {'id': 1, 'company': {'id': 1}}

class Company:
    def company(self, parent, info):
        # parent contiene el objeto User
        company_id = parent['id']
        return {'id': company_id, 'name': 'Acme Corp'}

# Registrar ambos resolvers
server.gql({
    'User': User(),
    'Company': Company()
})
```

### Argumentos de Resolvers

Todos los métodos resolver reciben:
- `self`: La instancia del resolver (para resolvers con estado)
- `parent`: El objeto padre del resolver anterior
- `info`: Información de ejecución GraphQL (nombre del campo, contexto, variables, etc.)
- `**kwargs`: Argumentos del campo desde la query

```python
def getUser(self, parent, info, id):
    # id viene de los argumentos de la query
    return fetch_user(id)
```

## Introspección

pgql soporta introspección completa de GraphQL lista para usar:

```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { queryType { name } } }"}'
```

Esto funciona con herramientas como:
- GraphiQL
- GraphQL Playground
- Apollo Studio
- Postman

## Uso Avanzado

### Interceptor de Autorización

pgql te permite interceptar cada llamada a resolver para implementar lógica de autorización usando `on_authorize`:

```python
from pgql import HTTPServer, AuthorizeInfo

def on_authorize(auth_info: AuthorizeInfo) -> bool:
    """
    Intercepta cada llamada a resolver para autorización
    
    Args:
        auth_info.operation: 'query', 'mutation' o 'subscription'
        auth_info.src_type: Tipo GraphQL padre que invoca el resolver (ej: 'User' para User.company)
        auth_info.dst_type: Tipo GraphQL siendo ejecutado (ej: 'Company' para User.company)
        auth_info.resolver: Nombre del campo/resolver (ej: 'getUser', 'company')
        auth_info.session_id: ID de sesión desde cookie (None si no está presente)
    
    Returns:
        True para permitir ejecución, False para denegar
    """
    # Denegar acceso si no hay sesión
    if not auth_info.session_id:
        return False
    
    # Restringir acceso a campos específicos basándose en el tipo padre
    if auth_info.src_type == "User" and auth_info.resolver == "company":
        return auth_info.session_id == "admin123"  # Solo admin puede acceder a User.company
    
    return True

server = HTTPServer('config.yml')
server.on_authorize(on_authorize)  # Registrar función de autorización
server.gql({...})
```

**Gestión de Sesiones:**

pgql extrae `session_id` de las cookies automáticamente. Establece la cookie en tu cliente:

```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -H "Cookie: session_id=abc123" \
  -d '{"query": "{ getUsers { id } }"}'
```

**Ejemplo de Flujo de Autorización:**

Al consultar `{ getUser { id company { name } } }`:
1. Primera llamada: `Query.getUser → User` (src_type='Query', dst_type='User', resolver='getUser')
2. Segunda llamada: `User.company → Company` (src_type='User', dst_type='Company', resolver='company')

**Nota:** La función `on_authorize` es opcional. Si no se configura, todos los resolvers se ejecutan sin verificaciones de autorización.

### Gestión de Sesiones

pgql incluye un almacén de sesiones integrado para gestionar sesiones de usuario:

```python
from pgql import HTTPServer, Session

server = HTTPServer('config.yml')

# Crear una nueva sesión
session = server.create_session(max_age=3600)  # 1 hora

# Almacenar cualquier dato en la sesión
session.set('user_id', 123)
session.set('username', 'john')
session.set('roles', ['admin', 'user'])
session.set('preferences', {'theme': 'dark'})

# Recuperar sesión
session = server.get_session(session_id)
user_id = session.get('user_id')

# Eliminar sesión (logout)
server.delete_session(session_id)
```

**Usando Sesiones en Resolvers:**

```python
class UserResolver:
    def __init__(self, server):
        self.server = server
    
    def login(self, parent, info, username, password):
        # Crear sesión en login exitoso
        session = self.server.create_session(max_age=7200)
        session.set('user_id', 123)
        session.set('authenticated', True)
        
        # Marcar sesión para establecer cookie en la respuesta
        info.context['new_session'] = session
        
        return {'success': True, 'session_id': session.session_id}
    
    def getUser(self, parent, info):
        # Acceder a datos de sesión
        session = info.context.get('session')
        if session and session.get('authenticated'):
            return {'id': session.get('user_id'), 'name': 'John'}
        return None
```

**Configurar nombre de cookie en YAML:**

```yaml
http_port: 8080
cookie_name: my_session_id  # Nombre de cookie personalizado
server:
  host: localhost
  routes:
    - mode: gql
      endpoint: /graphql
      schema: schema
```

Para documentación completa de sesiones, ver [SESSIONS.md](SESSIONS.md).

**Nota:** La función `on_authorize` es opcional. Si no se configura, todos los resolvers se ejecutan sin verificaciones de autorización.

### Manejo de Errores

pgql proporciona un sistema estructurado de errores compatible con la especificación GraphQL y con `gogql` de Go:

```python
from pgql import new_error, new_fatal, new_warning, ErrorDescriptor, LEVEL_FATAL

class User:
    def create_user(self, parent, info):
        input_data = info.input
        
        # Error fatal simple
        if not input_data.get('email'):
            raise new_fatal(
                message="El email es requerido",
                extensions={'field': 'email'}
            )
        
        # Error con ErrorDescriptor
        if input_data.get('age', 0) < 18:
            error_descriptor = ErrorDescriptor(
                message="El usuario debe tener al menos 18 años",
                code="AGE_VALIDATION_FAILED",
                level=LEVEL_FATAL
            )
            raise new_error(
                err=error_descriptor,
                extensions={'field': 'age', 'minimumAge': 18}
            )
        
        # Warning (no crítico)
        if input_data.get('age', 0) > 100:
            raise new_warning(
                message="Edad inusual detectada",
                extensions={'field': 'age', 'value': input_data['age']}
            )
        
        return {'id': '1', 'name': input_data['name']}
```

**Formato de Respuesta de Error:**

```json
{
  "data": null,
  "errors": [
    {
      "message": "El usuario debe tener al menos 18 años",
      "extensions": {
        "code": "AGE_VALIDATION_FAILED",
        "level": "fatal",
        "field": "age",
        "minimumAge": 18
      }
    }
  ]
}
```

**Tipos de Errores:**
- `new_fatal()`: Error crítico, detiene la ejecución (retorna null para el campo)
- `new_warning()`: Advertencia no crítica, la ejecución continúa
- `new_error()`: Error genérico (Warning o Fatal según el nivel)

Para la guía completa de manejo de errores, ver [ERROR_HANDLING.md](ERROR_HANDLING.md).

### Organización Anidada de Esquemas

Organiza tus esquemas por dominio:

```
schema/
├── schema.gql
├── user/
│   ├── types.gql
│   ├── queries.gql
│   ├── mutations.gql
│   └── inputs.gql
└── company/
    ├── types.gql
    └── queries.gql
```

pgql carga recursivamente todos los archivos `.gql`.

### Múltiples Rutas

Configura múltiples endpoints GraphQL:

```yaml
server:
  routes:
    - mode: gql
      endpoint: /graphql
      schema: schema
    - mode: gql
      endpoint: /admin/graphql
      schema: admin_schema
```

## 📚 Documentación Adicional

- **[ERROR_HANDLING.md](ERROR_HANDLING.md)** - Guía completa sobre manejo y retorno de errores
- **[SESSIONS.md](SESSIONS.md)** - Manejo de sesiones y cookies
- **[AUTHORIZATION.md](AUTHORIZATION.md)** - Interceptor de autorización
- **[SCALARS.md](SCALARS.md)** - Custom Scalars (Date, URL, JSON, etc.)
- **[NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md)** - Convenciones de nombres camelCase ↔ snake_case
- **[RESOLVER_INFO.md](RESOLVER_INFO.md)** - Estructura `ResolverInfo` para resolvers (compatible con Go)

## Requisitos

- Python >= 3.8
- graphql-core >= 3.2.0
- starlette >= 0.27.0
- uvicorn >= 0.23.0
- pyyaml >= 6.0

## Licencia

MIT

## Contribuir

¡Las contribuciones son bienvenidas! Por favor, siéntete libre de enviar un Pull Request.

## Enlaces

- [Repositorio GitHub](https://github.com/pjmd89/pygql)
- [Rastreador de Issues](https://github.com/pjmd89/pygql/issues)
- [Paquete PyPI](https://pypi.org/project/pgql/)
