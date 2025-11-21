# pygql Examples

This directory contains example implementations demonstrating various features of pygql.

## Examples

### mount_example.py

Demonstrates how to integrate pygql with FastAPI using the `mount()` method, allowing you to run both frameworks in a single Uvicorn instance.

**What it shows:**
- Creating a FastAPI application with REST endpoints
- Setting up pygql GraphQL server
- Mounting FastAPI on a specific path (`/api`)
- Running both in a single server

**To run:**

```bash
cd examples
python mount_example.py
```

**Test endpoints:**

```bash
# Test FastAPI endpoints
curl http://localhost:8080/api/
curl http://localhost:8080/api/users
curl -X POST "http://localhost:8080/api/users?name=David"
curl http://localhost:8080/api/users/1

# Test GraphQL endpoint
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ getUsers { id name email } }"}'
```

**Key code:**

```python
from fastapi import FastAPI
from pgql import HTTPServer

# Create FastAPI app
fastapi_app = FastAPI()

# Create pygql server
server = HTTPServer('config.yml')
server.gql({'User': UserResolver()})

# Mount FastAPI on /api
server.mount("/api", fastapi_app, name="fastapi")

# Start single server
server.start()
```

### cors_example.py

Demonstrates dynamic CORS origin validation using the `on_http_check_origin` callback, allowing you to control which domains can access your GraphQL API.

**What it shows:**
- Dynamic CORS origin validation with whitelist
- Using `on_http_check_origin` callback (similar to `on_authorize`)
- Automatic CORS headers injection
- Preflight OPTIONS request handling
- Default permissive behavior

**To run:**

```bash
cd examples
python cors_example.py
```

**Test CORS validation:**

```bash
# Allowed origin - returns 200 with CORS headers
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"query": "{ getUsers { id name email } }"}'

# Blocked origin - returns 403
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -H "Origin: http://malicious-site.com" \
  -d '{"query": "{ getUsers { id name email } }"}'

# View CORS headers
curl -I -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -H "Origin: https://myapp.com"

# Test preflight request
curl -X OPTIONS http://localhost:8080/graphql \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"
```

**Key code:**

```python
from pgql import HTTPServer

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://myapp.com"
]

def check_origin(origin: str) -> bool:
    """Validate CORS origin"""
    return origin in ALLOWED_ORIGINS

server = HTTPServer('config.yml')
server.on_http_check_origin(check_origin)  # Register CORS validator
server.gql({'User': UserResolver()})
server.start()
```

## Requirements

Some examples require additional dependencies:

```bash
pip install fastapi  # For mount_example.py
```

## Structure

Each example is self-contained and includes:
- Complete working code
- Comments explaining key concepts
- Test commands to verify functionality
- Expected output examples

## Contributing

Have a good example to share? Submit a pull request!
