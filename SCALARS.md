# Custom Scalars en pygql

Los **Scalars** son tipos primitivos personalizados en GraphQL que permiten validar y transformar datos en ambas direcciones: desde el cliente hacia tus resolvers (input) y desde tus resolvers hacia el cliente (output).

## 🎯 ¿Qué son los Scalars?

GraphQL incluye scalars básicos: `String`, `Int`, `Float`, `Boolean`, `ID`. Los **custom scalars** te permiten crear tus propios tipos primitivos con lógica de validación y transformación personalizada.

### Casos de uso comunes:
- **Fechas**: `Date`, `DateTime`, `Timestamp`
- **URLs**: Validar formato de URLs
- **Emails**: Validar direcciones de correo
- **JSON**: Objetos JSON arbitrarios
- **UUIDs**: Identificadores únicos
- **Moneda**: Validar formatos monetarios

---

## 🔄 Flujo de datos

### Input (Cliente → Resolver)
```
Cliente envía JSON → assess() normaliza → Resolver recibe Python nativo
{"date": "2025-11-19"} → datetime(2025,11,19) → Tu código usa datetime
```

### Output (Resolver → Cliente)
```
Resolver retorna Python → set() serializa → Cliente recibe JSON
datetime(2025,11,19) → "2025-11-19" → {"date": "2025-11-19"}
```

---

## 📝 Crear un Custom Scalar

### 1. Definir la clase

```python
from pgql import Scalar, ScalarResolved
from datetime import datetime

class DateScalar(Scalar):
    def set(self, value):
        """
        Normaliza valores de OUTPUT (resolver → cliente)
        
        Args:
            value: Valor retornado por el resolver
            
        Returns:
            (valor_serializado, error)
        """
        # Manejar valores None
        if value is None:
            return None, None
        
        # Convertir datetime a string ISO format
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d"), None
        
        # Si ya es string, retornarlo
        return str(value), None
    
    def assess(self, resolved):
        """
        Valida y parsea valores de INPUT (cliente → resolver)
        
        Args:
            resolved: ScalarResolved con:
                - value: Valor de entrada desde GraphQL
                - resolver_name: Nombre del resolver
                - resolved: Objeto padre (si aplica)
                
        Returns:
            (valor_parseado, error)
        """
        # Manejar valores None
        if resolved.value is None:
            return None, None
        
        # Validar y parsear string a datetime
        try:
            if isinstance(resolved.value, str):
                parsed_date = datetime.strptime(resolved.value, "%Y-%m-%d")
                return parsed_date, None
            else:
                return None, ValueError(f"Expected string, got {type(resolved.value)}")
        except ValueError as e:
            return None, ValueError(f"Invalid date format: {resolved.value}")
```

### 2. Definir en el schema

```graphql
# schema.gql
scalar Date

type Event {
    id: ID!
    name: String!
    date: Date!  # Usa el scalar personalizado
}

type Query {
    events(after: Date): [Event]  # Acepta Date como argumento
}
```

### 3. Registrar en el servidor

```python
from pgql import HTTPServer

# Crear servidor
server = HTTPServer("config.yaml")

# Registrar scalar ANTES de gql()
server.scalar("Date", DateScalar())

# Registrar resolvers
server.gql({
    "Query": QueryResolvers()
})

server.start()
```

### 4. Usar en resolvers

```python
from datetime import datetime

class QueryResolvers:
    def events(self, info, after=None):
        """
        after ya viene como datetime gracias a assess()
        """
        print(f"Filtering events after: {after}")  # datetime object
        print(f"Type: {type(after)}")  # <class 'datetime.datetime'>
        
        all_events = [
            {"id": "1", "name": "Conference", "date": datetime(2025, 12, 1)},
            {"id": "2", "name": "Workshop", "date": datetime(2025, 11, 15)},
        ]
        
        if after:
            # Comparar directamente (ambos son datetime)
            return [e for e in all_events if e["date"] > after]
        
        return all_events
        # Los objetos date se serializarán con set() automáticamente
```

---

## 🧪 Ejemplos Completos

### Scalar de URL

```python
from urllib.parse import urlparse

class URLScalar(Scalar):
    def set(self, value):
        if value is None:
            return None, None
        return str(value), None
    
    def assess(self, resolved):
        if resolved.value is None:
            return None, None
        
        try:
            parsed = urlparse(str(resolved.value))
            if not parsed.scheme or not parsed.netloc:
                return None, ValueError(f"Invalid URL: {resolved.value}")
            return str(resolved.value), None
        except Exception as e:
            return None, ValueError(f"URL parsing error: {e}")

# En schema.gql:
# scalar URL
#
# type Website {
#     url: URL!
# }

server.scalar("URL", URLScalar())
```

### Scalar de JSON

```python
import json

class JSONScalar(Scalar):
    def set(self, value):
        """Serializar objetos Python a JSON string"""
        if value is None:
            return None, None
        
        try:
            # Retornar el objeto tal cual (graphql-core lo serializará)
            return value, None
        except Exception as e:
            return None, e
    
    def assess(self, resolved):
        """Parsear JSON desde string o retornar objeto"""
        if resolved.value is None:
            return None, None
        
        # Si ya es dict/list, retornarlo
        if isinstance(resolved.value, (dict, list)):
            return resolved.value, None
        
        # Si es string, parsearlo
        if isinstance(resolved.value, str):
            try:
                return json.loads(resolved.value), None
            except json.JSONDecodeError as e:
                return None, ValueError(f"Invalid JSON: {e}")
        
        return None, ValueError("Expected JSON object or string")

# En schema.gql:
# scalar JSON
#
# type Config {
#     metadata: JSON
# }

server.scalar("JSON", JSONScalar())
```

### Scalar de Email

```python
import re

class EmailScalar(Scalar):
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def set(self, value):
        if value is None:
            return None, None
        return str(value).lower(), None
    
    def assess(self, resolved):
        if resolved.value is None:
            return None, None
        
        email = str(resolved.value).lower()
        
        if not self.EMAIL_REGEX.match(email):
            return None, ValueError(f"Invalid email format: {resolved.value}")
        
        return email, None

# En schema.gql:
# scalar Email
#
# type User {
#     email: Email!
# }

server.scalar("Email", EmailScalar())
```

---

## 📋 Uso desde el Cliente

### Con variables
```graphql
query GetEvents($afterDate: Date) {
    events(after: $afterDate) {
        id
        name
        date
    }
}

# Variables:
{
    "afterDate": "2025-11-15"
}
```

### Con valores literales
```graphql
query {
    events(after: "2025-11-15") {
        id
        name
        date
    }
}
```

---

## ⚠️ Manejo de Errores

### En assess() (input)
```python
def assess(self, resolved):
    if resolved.value is None:
        return None, None
    
    try:
        # Validación
        if not valid(resolved.value):
            return None, ValueError("Invalid input")
        
        # Parsing
        result = parse(resolved.value)
        return result, None
    except Exception as e:
        # Retornar error, GraphQL lo mostrará al cliente
        return None, e
```

### En set() (output)
```python
def set(self, value):
    if value is None:
        return None, None
    
    try:
        # Serialización
        serialized = serialize(value)
        return serialized, None
    except Exception as e:
        # Retornar error, GraphQL abortará la query
        return None, e
```

---

## 🎓 Buenas Prácticas

### 1. Acepta múltiples tipos en assess()
```python
def assess(self, resolved):
    value = resolved.value
    
    # Acepta int, float, string
    if isinstance(value, (int, float)):
        return int(value), None
    elif isinstance(value, str):
        return int(value), None
    else:
        return None, ValueError("Expected number")
```

### 2. Normaliza en set()
```python
def set(self, value):
    # Asegura formato consistente
    if isinstance(value, datetime):
        return value.isoformat(), None
    return str(value), None
```

### 3. Valida exhaustivamente
```python
def assess(self, resolved):
    if resolved.value is None:
        return None, None
    
    # Validar tipo
    if not isinstance(resolved.value, str):
        return None, ValueError("Expected string")
    
    # Validar formato
    if len(resolved.value) < 3:
        return None, ValueError("Too short")
    
    # Validar contenido
    if not resolved.value.isalpha():
        return None, ValueError("Must be alphabetic")
    
    return resolved.value.upper(), None
```

### 4. Mensajes de error claros
```python
def assess(self, resolved):
    try:
        return parse(resolved.value), None
    except ValueError:
        return None, ValueError(
            f"Invalid format for {resolved.resolver_name}: "
            f"expected YYYY-MM-DD, got {resolved.value}"
        )
```

---

## 🔗 Integración con graphql-core

pgql integra los custom scalars con `graphql-core` automáticamente:

- **`set()`** se mapea a `serialize` de GraphQLScalarType
- **`assess()`** se mapea a `parse_value` y `parse_literal`

El método `scalar()` del HTTPServer:
1. Registra tu instancia de Scalar
2. Crea un GraphQLScalarType wrapper
3. Lo inyecta en el schema en el type_map
4. Intercepta todas las operaciones de ese scalar

---

## 📦 Orden de Operaciones

```python
server = HTTPServer("config.yaml")

# 1. Registrar scalars primero
server.scalar("Date", DateScalar())
server.scalar("URL", URLScalar())

# 2. Luego registrar resolvers
server.gql({"Query": QueryResolvers()})

# 3. Iniciar servidor
server.start()
```

**Importante**: Los scalars deben registrarse **antes** de `gql()` para que estén disponibles cuando se cargue el schema.

---

## 🧪 Testing

```python
# test_scalars.py
from datetime import datetime
from pgql import ScalarResolved

def test_date_scalar():
    scalar = DateScalar()
    
    # Test assess (input)
    resolved = ScalarResolved(value="2025-11-19", resolver_name="test")
    result, error = scalar.assess(resolved)
    
    assert error is None
    assert isinstance(result, datetime)
    assert result.year == 2025
    assert result.month == 11
    assert result.day == 19
    
    # Test set (output)
    dt = datetime(2025, 11, 19)
    result, error = scalar.set(dt)
    
    assert error is None
    assert result == "2025-11-19"
    
    # Test error handling
    resolved = ScalarResolved(value="invalid", resolver_name="test")
    result, error = scalar.assess(resolved)
    
    assert result is None
    assert error is not None
```

---

## 📚 Referencia Rápida

### Estructura de Scalar

```python
class MyScalar(Scalar):
    def set(self, value) -> tuple[Any, Optional[Exception]]:
        """Output: Resolver → Cliente"""
        pass
    
    def assess(self, resolved: ScalarResolved) -> tuple[Any, Optional[Exception]]:
        """Input: Cliente → Resolver"""
        pass
```

### ScalarResolved

```python
@dataclass
class ScalarResolved:
    value: Any           # Valor de entrada desde GraphQL
    resolver_name: str   # Nombre del resolver actual
    resolved: Any        # Objeto padre (si existe)
```

### Retorno de métodos

Ambos métodos retornan: `(valor, error)`

- **Éxito**: `(valor_procesado, None)`
- **Error**: `(None, Exception("mensaje"))`
- **Null**: `(None, None)`

---

## 💡 Ejemplos y Testing

### Archivos de Ejemplo

El proyecto incluye ejemplos completos en `tests/basic/`:

- **`run_with_scalars.py`**: Servidor HTTP completo con Date, URL y JSON scalars
- **`test_scalars.py`**: Suite de tests unitarios
- **`schema_scalars/`**: Schema GraphQL modular
  - `scalars.gql`: Declaración de custom scalars
  - `types.gql`: Tipos que usan los scalars
  - `queries.gql`: Queries con argumentos de tipo scalar
  - `schema.gql`: Schema principal que importa todo
- **`config_scalars.yml`**: Configuración del servidor

### Ejecutar Tests Unitarios

```bash
python tests/basic/test_scalars.py
```

Ejecuta tests de:
- ✅ ScalarResolved dataclass
- ✅ DateScalar (validación y serialización)
- ✅ URLScalar (validación de URLs)
- ✅ JSONScalar (parsing y serialización)

### Ejecutar Servidor de Ejemplo

```bash
python tests/basic/run_with_scalars.py
```

Inicia servidor en `http://localhost:8080/graphql` con:
- 🗓️ **Date**: Convierte `datetime` ↔ `"YYYY-MM-DD"`
- 🔗 **URL**: Valida URLs con esquema completo
- 📦 **JSON**: Serializa objetos Python ↔ JSON

### Queries de Prueba

**Obtener todos los eventos:**
```graphql
query {
  events {
    id
    name
    date        # Date scalar → "2025-12-01"
    website     # URL scalar → "https://example.com"
    metadata    # JSON scalar → {"location": "Madrid"}
  }
}
```

**Filtrar por fecha:**
```graphql
query {
  events(after: "2025-11-16") {  # String → datetime automático
    id
    name
    date
  }
}
```

**Con variables:**
```graphql
query GetEvents($afterDate: Date) {
  events(after: $afterDate) {
    id
    name
    date
  }
}

# Variables:
{
  "afterDate": "2025-11-16"
}
```

**Ejemplo con curl:**
```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ events { id name date } }"}'
```

---

## 🤝 Contribuir

¿Creaste un scalar útil? ¡Compártelo en los issues del repositorio!

Scalars comunes que la comunidad podría necesitar:
- PhoneNumber
- CreditCard
- PostalCode
- Color (hex)
- Duration
- Coordinate (lat/long)
