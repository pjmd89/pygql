# pgql

A lightweight Python GraphQL server framework with automatic resolver mapping, schema introspection, and built-in support for Starlette/Uvicorn.

## Features

- 🚀 **Automatic Resolver Mapping**: Map Python class methods to GraphQL fields based on return types
- 📁 **Recursive Schema Loading**: Organize your `.gql` schema files in nested directories
- 🔍 **Built-in Introspection**: Full GraphQL introspection support out of the box
- 🎯 **Instance-based Resolvers**: Use class instances for stateful resolvers with dependency injection
- ⚡ **Async Support**: Built on Starlette and Uvicorn for high-performance async handling
- 🔧 **YAML Configuration**: Simple YAML-based server configuration
- 📦 **Type Support**: Full support for `extend type`, nested types, and GraphQL type modifiers
- 🔐 **Authorization System**: Intercept resolver calls with `on_authorize` function
- 🍪 **Session Management**: Built-in session store with automatic cookie handling
- 🔗 **FastAPI Integration**: Mount FastAPI apps alongside GraphQL in a single Uvicorn instance

## Installation

```bash
pip install pgql
```

## Quick Start

### 1. Define Your GraphQL Schema

Create your schema files in a directory structure:

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

### 2. Create Resolver Classes

```python
# resolvers/user.py
class User:
    def getUser(self, parent, info, id):
        # Your logic here
        return {'id': id, 'name': 'John Doe', 'email': 'john@example.com'}
    
    def getUsers(self, parent, info):
        return [
            {'id': 1, 'name': 'John', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane', 'email': 'jane@example.com'}
        ]
```

### 3. Configure Server

**config.yml:**
```yaml
http_port: 8080
debug: true
server:
  host: localhost
  routes:
    - mode: gql
      endpoint: /graphql
      schema: schema  # Path to schema directory
```

### 4. Start Server

```python
from pgql import HTTPServer
from resolvers.user import User

# Create resolver instances
user_resolver = User()

# Initialize server
server = HTTPServer('config.yml')

# Map resolvers to GraphQL types
server.gql({
    'User': user_resolver
})

# Start server
server.start()
```

### 5. Query Your API

```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ getUsers { id name email } }"}'
```

**Response:**
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

## How It Works

### Automatic Resolver Mapping

pgql automatically maps resolver methods to GraphQL fields based on **return types**:

1. If `Query.getUser` returns type `User`, pgql looks for a method named `getUser` in the `User` resolver class
2. The mapping works recursively for nested types (e.g., `User.company` → `Company.company`)

**Example:**

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
        # parent contains the User object
        company_id = parent['id']
        return {'id': company_id, 'name': 'Acme Corp'}

# Register both resolvers
server.gql({
    'User': User(),
    'Company': Company()
})
```

### Resolver Arguments

All resolver methods receive:
- `self`: The resolver instance (for stateful resolvers)
- `parent`: The parent object from the previous resolver
- `info`: GraphQL execution info (field name, context, variables, etc.)
- `**kwargs`: Field arguments from the query

```python
def getUser(self, parent, info, id):
    # id comes from query arguments
    return fetch_user(id)
```

## Introspection

pgql supports full GraphQL introspection out of the box:

```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { queryType { name } } }"}'
```

This works with tools like:
- GraphiQL
- GraphQL Playground
- Apollo Studio
- Postman

## Advanced Usage

### Authorization Interceptor

pgql allows you to intercept every resolver call to implement authorization logic using `on_authorize`:

```python
from pgql import HTTPServer, AuthorizeInfo

def on_authorize(auth_info: AuthorizeInfo) -> bool:
    """
    Intercept every resolver call for authorization
    
    Args:
        auth_info.operation: 'query', 'mutation', or 'subscription'
        auth_info.src_type: Parent GraphQL type invoking the resolver (e.g., 'User' for User.company)
        auth_info.dst_type: GraphQL type being executed (e.g., 'Company' for User.company)
        auth_info.resolver: Field/resolver name (e.g., 'getUser', 'company')
        auth_info.session_id: Session ID from cookie (None if not present)
    
    Returns:
        True to allow execution, False to deny
    """
    # Deny access if no session
    if not auth_info.session_id:
        return False
    
    # Restrict specific field access based on parent type
    if auth_info.src_type == "User" and auth_info.resolver == "company":
        return auth_info.session_id == "admin123"  # Only admin can access User.company
    
    return True

server = HTTPServer('config.yml')
server.on_authorize(on_authorize)  # Register authorization function
server.gql({...})
```

**Session Management:**

pgql extracts `session_id` from cookies automatically. Set the cookie in your client:

```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -H "Cookie: session_id=abc123" \
  -d '{"query": "{ getUsers { id } }"}'
```

**Authorization Flow Example:**

When querying `{ getUser { id company { name } } }`:
1. First call: `Query.getUser → User` (src_type='Query', dst_type='User', resolver='getUser')
2. Second call: `User.company → Company` (src_type='User', dst_type='Company', resolver='company')

**Note:** The `on_authorize` function is optional. If not set, all resolvers execute without authorization checks.

### Session Management

pgql includes a built-in session store for managing user sessions:

```python
from pgql import HTTPServer, Session

server = HTTPServer('config.yml')

# Create a new session
session = server.create_session(max_age=3600)  # 1 hour

# Store any data in the session
session.set('user_id', 123)
session.set('username', 'john')
session.set('roles', ['admin', 'user'])
session.set('preferences', {'theme': 'dark'})

# Retrieve session
session = server.get_session(session_id)
user_id = session.get('user_id')

# Delete session (logout)
server.delete_session(session_id)
```

**Using Sessions in Resolvers:**

```python
class UserResolver:
    def __init__(self, server):
        self.server = server
    
    def login(self, parent, info, username, password):
        # Create session on successful login
        session = self.server.create_session(max_age=7200)
        session.set('user_id', 123)
        session.set('authenticated', True)
        
        # Mark session to set cookie in response
        info.context['new_session'] = session
        
        return {'success': True, 'session_id': session.session_id}
    
    def getUser(self, parent, info):
        # Access session data
        session = info.context.get('session')
        if session and session.get('authenticated'):
            return {'id': session.get('user_id'), 'name': 'John'}
        return None
```

**Configure cookie name in YAML:**

```yaml
http_port: 8080
cookie_name: my_session_id  # Custom cookie name
server:
  host: localhost
  routes:
    - mode: gql
      endpoint: /graphql
      schema: schema
```

For complete session documentation, see [SESSIONS.md](SESSIONS.md).

**Note:** The `on_authorize` function is optional. If not set, all resolvers execute without authorization checks.

### Error Handling

pgql provides a structured error system compatible with GraphQL spec and Go's `gogql`:

```python
from pgql import new_error, new_fatal, new_warning, ErrorDescriptor, LEVEL_FATAL

class User:
    def create_user(self, parent, info):
        input_data = info.input
        
        # Simple fatal error
        if not input_data.get('email'):
            raise new_fatal(
                message="Email is required",
                extensions={'field': 'email'}
            )
        
        # Error with ErrorDescriptor
        if input_data.get('age', 0) < 18:
            error_descriptor = ErrorDescriptor(
                message="User must be at least 18 years old",
                code="AGE_VALIDATION_FAILED",
                level=LEVEL_FATAL
            )
            raise new_error(
                err=error_descriptor,
                extensions={'field': 'age', 'minimumAge': 18}
            )
        
        # Warning (non-critical)
        if input_data.get('age', 0) > 100:
            raise new_warning(
                message="Unusual age detected",
                extensions={'field': 'age', 'value': input_data['age']}
            )
        
        return {'id': '1', 'name': input_data['name']}
```

**Error Response Format:**

```json
{
  "data": null,
  "errors": [
    {
      "message": "User must be at least 18 years old",
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

**Error Types:**
- `new_fatal()`: Critical error, stops execution (returns null for field)
- `new_warning()`: Non-critical warning, execution continues
- `new_error()`: Generic error (Warning or Fatal based on level)

For complete error handling guide, see [ERROR_HANDLING.md](ERROR_HANDLING.md).

### Nested Schema Organization

Organize your schemas by domain:

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

pgql recursively loads all `.gql` files.

### Multiple Routes

Configure multiple GraphQL endpoints:

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

### Integration with FastAPI

pgql can be integrated with existing FastAPI applications using the `mount()` method, allowing you to run both frameworks in a single Uvicorn instance:

```python
from fastapi import FastAPI
from pgql import HTTPServer
from resolvers.user import User

# Create your FastAPI app
fastapi_app = FastAPI(title="My API")

@fastapi_app.get("/api/")
async def read_root():
    return {"message": "Hello from FastAPI!"}

@fastapi_app.get("/api/users")
async def get_users():
    return {"users": [{"id": 1, "name": "Alice"}]}

# Create pygql server
server = HTTPServer('config.yml')
server.gql({'User': User()})

# Mount FastAPI app on /api path
server.mount("/api", fastapi_app, name="fastapi")

# Start single uvicorn server with both apps
server.start()
```

**Available endpoints:**

- `POST http://localhost:8080/graphql` - pygql GraphQL endpoint
- `GET http://localhost:8080/api/` - FastAPI endpoints
- `GET http://localhost:8080/api/users` - FastAPI endpoints

**Key benefits:**

- **Single Uvicorn instance**: No need to manage multiple servers
- **Shared configuration**: Use pygql's YAML config for both
- **Easy migration**: Add GraphQL to existing FastAPI projects without refactoring
- **ASGI compatible**: Works with any ASGI application (FastAPI, Quart, Starlette apps, etc.)

**Method signature:**

```python
def mount(self, path: str, app, name: str = None):
    """
    Mount an ASGI application (like FastAPI) on a specific path
    
    Args:
        path: URL prefix for the mounted app (e.g., "/api")
        app: ASGI application instance (FastAPI, etc.)
        name: Optional name for the mount point
    """
```

## Documentation

For detailed guides on specific features:

- **[Error Handling](ERROR_HANDLING.md)** - Complete guide on how to return and handle errors
- **[Sessions](SESSIONS.md)** - Session management and cookie handling
- **[Authorization](AUTHORIZATION.md)** - Authorization system with `on_authorize`
- **[Scalars](SCALARS.md)** - Custom scalar types implementation
- **[Naming Conventions](NAMING_CONVENTIONS.md)** - camelCase/snake_case conversion
- **[Resolver Info](RESOLVER_INFO.md)** - ResolverInfo object reference

## Requirements

- Python >= 3.8
- graphql-core >= 3.2.0
- starlette >= 0.27.0
- uvicorn >= 0.23.0
- pyyaml >= 6.0

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- [GitHub Repository](https://github.com/pjmd89/pygql)
- [Issue Tracker](https://github.com/pjmd89/pygql/issues)
- [PyPI Package](https://pypi.org/project/pgql/)
