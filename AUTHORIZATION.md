# Sistema de Autorización en pgql

## Implementación

El sistema de autorización `on_authorize` permite interceptar cada llamada a un resolver para verificar permisos antes de su ejecución.

## Archivos Modificados

1. **`pgql/http/authorize_info.py`** (nuevo)
   - Dataclass `AuthorizeInfo` con información de autorización
   - Campos: `operation`, `src_type`, `dst_type`, `resolver`, `session_id`

2. **`pgql/http/http.py`**
   - Modificado `assign_resolvers()` para soportar wrapper de autorización
   - Añadido parámetro `on_authorize_fn` opcional
   - Wrapper `create_authorized_resolver()` intercepta cada resolver
   - Detecta el tipo de operación (query/mutation/subscription)
   - Captura `src_type` (tipo GraphQL padre) y `dst_type` (tipo de retorno)
   - Extrae `session_id` de `info.context`
   - Lanza `PermissionError` si se deniega acceso

3. **`HTTPServer` class**
   - Nuevo método `on_authorize(authorize_fn)` para registrar función de autorización
   - Almacena función en `self.__on_authorize`
   - Pasa función a `assign_resolvers()`
   - Extrae `session_id` de cookies: `request.cookies.get('session_id')`
   - Pasa `session_id` en el contexto GraphQL

4. **`pgql/__init__.py`**
   - Exporta `AuthorizeInfo` para uso en aplicaciones

## Uso

### Ejemplo Básico

```python
from pgql import HTTPServer, AuthorizeInfo

def on_authorize(auth_info: AuthorizeInfo) -> bool:
    print(f"Operation: {auth_info.operation}")      # 'query', 'mutation', 'subscription'
    print(f"Src Type: {auth_info.src_type}")        # 'Query', 'User', etc. (tipo padre)
    print(f"Dst Type: {auth_info.dst_type}")        # 'User', 'Company', etc. (tipo de retorno)
    print(f"Resolver: {auth_info.resolver}")        # 'getUser', 'company', etc.
    print(f"Session: {auth_info.session_id}")       # 'abc123' or None
    
    return True  # o False para denegar

server = HTTPServer('config.yml')
server.on_authorize(on_authorize)  # Registrar función (opcional)
server.gql({...})
server.start()
```

### Ejemplo con Restricciones

```python
def on_authorize(auth_info: AuthorizeInfo) -> bool:
    # Denegar si no hay sesión
    if not auth_info.session_id:
        return False
    
    # Permitir solo admin para acceder a User.company
    if auth_info.src_type == "User" and auth_info.resolver == "company":
        return auth_info.session_id == "admin123"
    
    return True
```

### Ejemplo con Query Completa

Para la query `{ getUser { id name company { id name } } }`:

1. Primera llamada: `Query.getUser → User`
   - `src_type='Query'`, `dst_type='User'`, `resolver='getUser'`
   
2. Segunda llamada: `User.company → Company`
   - `src_type='User'`, `dst_type='Company'`, `resolver='company'`

### Enviar session_id desde Cliente

```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -H "Cookie: session_id=abc123" \
  -d '{"query": "{ getUsers { id name } }"}'
```

## Comportamiento

- **Si `on_authorize` NO está configurado**: Todos los resolvers se ejecutan sin restricciones (✅ emoji en logs)
- **Si `on_authorize` está configurado**: Cada resolver muestra 🔒 emoji y se intercepta antes de ejecutarse
- **Si retorna `False`**: Se lanza `PermissionError` con mensaje "No autorizado para ejecutar {Type}.{resolver}"
- **Si retorna `True`**: El resolver se ejecuta normalmente

## Flujo de Ejecución

1. Cliente envía query GraphQL con cookie `session_id`
2. `gql_handler()` extrae `session_id` de `request.cookies`
3. Se crea contexto con `{'session_id': session_id, 'request': request}`
4. GraphQL ejecuta query y llama a resolver
5. Wrapper `authorized_resolver()` intercepta llamada
6. Extrae `session_id` de `info.context`
7. Crea `AuthorizeInfo` con datos de operación
8. Llama a `on_authorize(auth_info)`
9. Si retorna `True`: ejecuta resolver original
10. Si retorna `False`: lanza `PermissionError`

## Tests Realizados

✅ Query sin `session_id` → Denegado cuando se requiere
✅ Query con `session_id` válido → Autorizado
✅ Nested field sin permisos → Denegado específicamente
✅ Nested field con permisos admin → Autorizado
✅ Función `on_authorize` opcional → Funciona sin ella

## Convenciones Python

- Nombre de función: `on_authorize` (snake_case)
- Nombre de clase: `AuthorizeInfo` (PascalCase)
- Campos: `operation`, `src_type`, `dst_type`, `resolver`, `session_id` (snake_case)

## Ejemplos de src_type y dst_type

### Ejemplo 1: Query Root
```graphql
type Query {
    getUser: User!
}
```
Al ejecutar `{ getUser { id } }`:
- `src_type='Query'`, `dst_type='User'`, `resolver='getUser'`

### Ejemplo 2: Nested Field
```graphql
type User {
    id: ID!
    company: Company!
}

type Company {
    id: ID!
    name: String!
}
```
Al ejecutar `{ getUser { company { name } } }`:
- Primera llamada: `src_type='Query'`, `dst_type='User'`, `resolver='getUser'`
- Segunda llamada: `src_type='User'`, `dst_type='Company'`, `resolver='company'`

### Ejemplo 3: Restricción Basada en Padre
```python
def on_authorize(auth_info: AuthorizeInfo) -> bool:
    # Permitir acceso a Company solo cuando se invoca desde Query
    # Denegar cuando se invoca desde User (User.company)
    if auth_info.dst_type == "Company" and auth_info.src_type == "User":
        return False
    return True
```
