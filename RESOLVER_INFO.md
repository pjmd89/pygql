# ResolverInfo - Estructura de Información para Resolvers

`ResolverInfo` es la estructura que todos los resolvers reciben como parámetro `info`, compatible con la implementación de Go (`gogql`).

## 🎯 Propósito

`ResolverInfo` centraliza toda la información del contexto de ejecución de un resolver:
- ✅ **Argumentos** en `info.args` (snake_case)
- ✅ **Operación** (query/mutation/subscription)
- ✅ **Tipos GraphQL** (actual y padre)
- ✅ **Sesión** (session_id)
- ✅ **Contexto completo** (request, etc.)

## 📐 Estructura

```python
@dataclass
class ResolverInfo:
    operation: str              # "query", "mutation", "subscription"
    resolver: str               # Nombre del campo (camelCase del schema)
    args: Dict[str, Any]       # Argumentos (snake_case)
    parent: Any                # Valor del parent/source
    type_name: str             # Tipo GraphQL actual
    parent_type_name: Optional[str] = None   # Tipo GraphQL del padre
    session_id: Optional[str] = None         # ID de sesión
    context: Optional[Dict[str, Any]] = None # Contexto completo
    field_name: Optional[str] = None         # Nombre original del campo
```

## 🔄 Comparación con Go

### Go (gogql)

```go
type ResolverInfo struct {
    Operation         string
    Resolver          string
    Args              Args  // map[string]interface{}
    Parent            Parent
    Directives        DirectiveList
    TypeName          string
    ParentTypeName    *string
    SubscriptionValue interface{}
    SessionID         string
    RestInfo          *RestInfo
}

// Uso:
func (o *User) Resolver(info resolvers.ResolverInfo) (DataReturn, error) {
    userID := info.Args["userId"]
    return getUser(userID), nil
}
```

### Python (pygql)

```python
from pgql import ResolverInfo

class User:
    def get_user(self, info: ResolverInfo):
        """Resolver que usa ResolverInfo (estilo Go - solo info)"""
        # Acceder parent desde info
        parent = info.parent
        
        # Acceder argumentos
        user_id = info.args.get('user_id')  # Convertido de userId
        
        # Verificar sesión
        if not info.session_id:
            raise PermissionError("Authentication required")
        
        # Usar información de operación
        print(f"Operation: {info.operation}")
        print(f"Type: {info.type_name}")
        
        return {'id': user_id, 'name': 'John'}
```

## 📝 Firma de Resolvers

### Antes (con **kwargs)

```python
def get_user(self, parent, info, user_id: int):
    """
    ❌ Problema:
    - Argumentos como parámetros separados
    - Difícil ver qué argumentos están disponibles
    - No compatible con Go
    """
    return {'id': user_id, 'name': 'John'}
```

### Ahora (con ResolverInfo - estilo Go)

```python
from pgql import ResolverInfo

def get_user(self, info: ResolverInfo):
    """
    ✅ Ventajas:
    - Solo un parámetro (como en Go)
    - Parent en info.parent
    - Argumentos en info.args (centralizados)
    - Compatible con Go
    - Acceso a toda la información del contexto
    """
    user_id = info.args.get('user_id')
    return {'id': user_id, 'name': 'John'}
```

## 🔍 Campos Detallados

### operation: str

Tipo de operación GraphQL:
- `"query"` - Consulta de lectura
- `"mutation"` - Modificación de datos
- `"subscription"` - Suscripción en tiempo real

```python
def my_resolver(self, info: ResolverInfo):
    if info.operation == "mutation":
        # Lógica para mutaciones
        pass
```

### resolver: str

Nombre del campo en el schema (camelCase original):

```graphql
type Query {
    getUser(userId: ID!): User
    getAllUsers: [User]
}
```

```python
# Para getUser:
info.resolver == "getUser"

# Para getAllUsers:
info.resolver == "getAllUsers"
```

### args: Dict[str, Any]

Diccionario con los argumentos del campo, **convertidos a snake_case**:

```graphql
query {
    getUser(userId: "123", includeProfile: true)
}
```

```python
def get_user(self, info: ResolverInfo):
    user_id = info.args.get('user_id')          # De userId
    include_profile = info.args.get('include_profile')  # De includeProfile
    
    # Con valores por defecto
    page = info.args.get('page', 1)
    limit = info.args.get('limit', 10)
```

### parent: Any

Valor del objeto padre. Útil en resolvers de campos anidados:

```graphql
type User {
    id: ID!
    name: String!
    company: Company  # parent será el objeto User
}

type Company {
    id: ID!
    name: String!
}
```

```python
class Company:
    def company(self, info: ResolverInfo):
        """Resolver de relación User → Company"""
        # parent es el objeto User
        parent = info.parent
        user_id = parent.get('id')
        return get_company_for_user(user_id)
```

### type_name: str

Nombre del tipo GraphQL que está siendo resuelto:

```python
def get_user(self, info: ResolverInfo):
    # info.type_name == "User"
    print(f"Resolviendo tipo: {info.type_name}")
```

### parent_type_name: Optional[str]

Nombre del tipo GraphQL padre:

```graphql
type Query {
    getUser: User  # parent_type_name = "Query"
}

type User {
    company: Company  # parent_type_name = "User"
}
```

```python
def company(self, info: ResolverInfo):
    print(f"Llamado desde: {info.parent_type_name}")
    # Output: "Llamado desde: User"
```

### session_id: Optional[str]

ID de la sesión actual (si existe):

```python
def get_profile(self, info: ResolverInfo):
    if not info.session_id:
        raise PermissionError("Authentication required")
    
    # Obtener datos de la sesión
    session = get_session(info.session_id)
    user_id = session.get('user_id')
    
    return get_user_profile(user_id)
```

### context: Optional[Dict[str, Any]]

Contexto completo de GraphQL, incluye:
- `session_id`: ID de sesión
- `request`: Objeto Request de Starlette (si disponible)
- Cualquier otro dato inyectado

```python
def my_resolver(self, info: ResolverInfo):
    # Acceder al request completo
    request = info.context.get('request')
    if request:
        user_agent = request.headers.get('user-agent')
    
    # Acceder a sesión completa
    session = info.context.get('session')
    if session:
        roles = session.get('roles', [])
```

## 🎨 Ejemplos Completos

### Ejemplo 1: Query Simple

```graphql
type Query {
    getUser(userId: ID!): User
}
```

```python
from pgql import ResolverInfo

class Query:
    def get_user(self, info: ResolverInfo):
        user_id = info.args.get('user_id')
        
        print(f"Operation: {info.operation}")      # "query"
        print(f"Resolver: {info.resolver}")        # "getUser"
        print(f"Type: {info.type_name}")           # "User"
        print(f"Parent Type: {info.parent_type_name}")  # "Query"
        print(f"Parent: {info.parent}")            # None (root query)
        
        return {
            'id': user_id,
            'name': 'John Doe',
            'email': 'john@example.com'
        }
```

### Ejemplo 2: Mutation con Autenticación

```graphql
type Mutation {
    updateProfile(
        firstName: String!
        lastName: String!
        emailAddress: String
    ): User
}
```

```python
from pgql import ResolverInfo

class Mutation:
    def update_profile(self, info: ResolverInfo):
        # Verificar autenticación
        if not info.session_id:
            raise PermissionError("Must be authenticated")
        
        # Obtener argumentos (ya en snake_case)
        first_name = info.args.get('first_name')
        last_name = info.args.get('last_name')
        email_address = info.args.get('email_address')
        
        # Obtener usuario de la sesión
        session = info.context.get('session')
        user_id = session.get('user_id')
        
        # Actualizar perfil
        return update_user(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email_address=email_address
        )

```python
from pgql import ResolverInfo

class Mutation:
    def update_profile(self, info: ResolverInfo):
        # Verificar autenticación
        if not info.session_id:
            raise PermissionError("Must be authenticated")
        
        # Obtener argumentos (ya en snake_case)
        first_name = info.args.get('first_name')
        last_name = info.args.get('last_name')
        email_address = info.args.get('email_address')
        
        # Obtener usuario de la sesión
        session = info.context.get('session')
        user_id = session.get('user_id')
        
        # Actualizar perfil
        return update_user(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email_address=email_address
        )
```

### Ejemplo 3: Resolver de Relación

```graphql
type User {
    id: ID!
    name: String!
    company: Company
}

type Company {
    id: ID!
    name: String!
}
```

```python
from pgql import ResolverInfo

class Company:
    def company(self, info: ResolverInfo):
        """Resolver User.company"""
        # Acceder al parent desde info
        parent = info.parent
        user_id = parent.get('id')
        
        print(f"Resolviendo company para user_id={user_id}")
        print(f"Parent type: {info.parent_type_name}")  # "User"
        print(f"Current type: {info.type_name}")        # "Company"
        
        # Obtener company del usuario
        company_id = get_user_company_id(user_id)
        return get_company(company_id)
```

### Ejemplo 4: Paginación

```graphql
type Query {
    searchUsers(
        query: String!
        page: Int = 1
        pageSize: Int = 10
    ): UserPage
}
```

```python
from pgql import ResolverInfo

class Query:
    def search_users(self, info: ResolverInfo):
        # Argumentos con valores por defecto
        query = info.args.get('query')
        page = info.args.get('page', 1)
        page_size = info.args.get('page_size', 10)
        
        # Calcular offset
        offset = (page - 1) * page_size
        
        # Buscar usuarios
        users = search_users_db(
            query=query,
            limit=page_size,
            offset=offset
        )
        
        return {
            'users': users,
            'page': page,
            'page_size': page_size,
            'total': count_users_db(query)
        }
```

## 🔒 Integración con Autorización

`ResolverInfo` se complementa con `AuthorizeInfo` para autorización:

```python
from pgql import HTTPServer, AuthorizeInfo, ResolverInfo

def on_authorize(auth_info: AuthorizeInfo) -> bool:
    """Intercepta ANTES de ejecutar el resolver"""
    print(f"Autorizando: {auth_info.src_type}.{auth_info.resolver}")
    
    if not auth_info.session_id:
        return False  # Denegar sin sesión
    
    return True

class User:
    def get_user(self, info: ResolverInfo):
        """Se ejecuta DESPUÉS de on_authorize"""
        # Si llegamos aquí, ya estamos autorizados
        user_id = info.args.get('user_id')
        return {'id': user_id, 'name': 'John'}

# Configurar servidor
server = HTTPServer('etc/http.yml')
server.on_authorize(on_authorize)
server.gql({'User': User()})
```

## 🆚 Ventajas sobre **kwargs

| Aspecto | **kwargs | ResolverInfo |
|---------|----------|--------------|
| **Descubrimiento** | Difícil ver argumentos disponibles | `info.args.keys()` |
| **Metadata** | Solo argumentos | Operación, tipos, sesión, contexto |
| **Compatibilidad** | Python-only | Compatible con Go |
| **Type hints** | Parámetros individuales | Un solo objeto tipado |
| **Evolución** | Cambiar firma del método | Solo usar nuevos campos de info |

## 📚 Resumen

✅ **ResolverInfo centraliza toda la información del resolver**

✅ **Compatible con la implementación de Go**

✅ **Argumentos siempre en snake_case** (conversión automática)

✅ **Firma consistente (estilo Go)**: `(self, info: ResolverInfo)` - acceder a parent con `info.parent`

✅ **Fácil acceso a sesión y contexto**

✅ **No más **kwargs individuales**

## 🔗 Ver También

- [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md) - Conversión camelCase ↔ snake_case
- [SESSIONS.md](SESSIONS.md) - Manejo de sesiones
- [AUTHORIZATION.md](AUTHORIZATION.md) - Interceptor de autorización
