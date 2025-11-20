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
