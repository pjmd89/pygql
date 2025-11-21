# Manejo de Errores en pygql

Esta guía explica cómo retornar errores correctamente desde tus resolvers GraphQL usando el sistema de errores de `pygql`, compatible con el estándar GraphQL y con la implementación de Go `gogql`.

## Tabla de Contenidos

- [Tipos de Errores](#tipos-de-errores)
- [Métodos de Creación](#métodos-de-creación)
- [Uso en Resolvers](#uso-en-resolvers)
- [Formato de Respuesta](#formato-de-respuesta)
- [Ejemplos Completos](#ejemplos-completos)
- [Mejores Prácticas](#mejores-prácticas)

## Tipos de Errores

`pygql` proporciona dos niveles de error:

### 1. **Warning** (Nivel 0)
- La ejecución **continúa** después del error
- Útil para validaciones no críticas o advertencias
- El campo retorna `null` pero otros campos se ejecutan

### 2. **Fatal** (Nivel 1)
- La ejecución **se detiene** para ese campo
- Útil para errores críticos de validación o lógica de negocio
- El campo retorna `null` y se reporta el error

## Métodos de Creación

### Importaciones Necesarias

```python
from pgql import (
    new_error,      # Crear error genérico (Warning o Fatal)
    new_warning,    # Crear Warning específicamente
    new_fatal,      # Crear Fatal específicamente
    ErrorDescriptor,  # Descriptor con message, code, level
    LEVEL_WARNING,  # Constante para nivel Warning
    LEVEL_FATAL     # Constante para nivel Fatal
)
```

### 1. `new_error()` - Error Genérico

Función flexible que puede crear Warning o Fatal según el nivel especificado.

#### Forma 1: Con ErrorDescriptor

```python
from pgql import new_error, ErrorDescriptor, LEVEL_FATAL

error_descriptor = ErrorDescriptor(
    message="User must be at least 30 years old",
    code="AGE_VALIDATION_FAILED",
    level=LEVEL_FATAL
)

# Con extensions adicionales (opcional)
extensions = {
    'field': 'age',
    'minimumAge': 30,
    'providedAge': 25
}

raise new_error(err=error_descriptor, extensions=extensions)
```

#### Forma 2: Con parámetros directos

```python
from pgql import new_error, LEVEL_FATAL

# Mínimo requerido
raise new_error(
    message="Invalid email format",
    level=LEVEL_FATAL
)

# Con código y extensions
raise new_error(
    message="Invalid email format",
    code="EMAIL_INVALID",
    level=LEVEL_FATAL,
    extensions={'field': 'email', 'pattern': r'^[\w\.-]+@[\w\.-]+\.\w+$'}
)
```

### 2. `new_warning()` - Warning Específico

Siempre crea un error de nivel Warning.

```python
from pgql import new_warning

# Forma simple
raise new_warning(message="This field is deprecated")

# Con extensions
raise new_warning(
    message="This field will be removed in v2.0",
    extensions={'deprecatedSince': '1.5.0', 'removeIn': '2.0.0'}
)

# Con ErrorDescriptor (level se ignora, siempre es Warning)
error_descriptor = ErrorDescriptor(
    message="Rate limit approaching",
    code="RATE_LIMIT_WARNING",
    level=LEVEL_WARNING
)
raise new_warning(err=error_descriptor, extensions={'remaining': 10})
```

### 3. `new_fatal()` - Fatal Específico

Siempre crea un error de nivel Fatal.

```python
from pgql import new_fatal

# Forma simple
raise new_fatal(message="Unauthorized access")

# Con extensions
raise new_fatal(
    message="Insufficient permissions",
    extensions={'required': 'admin', 'current': 'user'}
)

# Con ErrorDescriptor
error_descriptor = ErrorDescriptor(
    message="Database connection failed",
    code="DB_CONNECTION_ERROR",
    level=LEVEL_FATAL
)
raise new_fatal(err=error_descriptor)
```

## Uso en Resolvers

### Ejemplo Básico

```python
from pgql import Resolver, ResolverInfo, new_fatal

class User(Resolver):
    
    def create_user(self, info: ResolverInfo):
        input_data = info.input
        
        # Validación simple
        if not input_data.get('email'):
            raise new_fatal(
                message="Email is required",
                extensions={'field': 'email'}
            )
        
        # Crear usuario...
        return {'id': '1', 'name': input_data['name']}
```

### Ejemplo con Validación de Edad

```python
from datetime import datetime
from pgql import Resolver, ResolverInfo, new_error, ErrorDescriptor, LEVEL_FATAL

class User(Resolver):
    
    def create_user(self, info: ResolverInfo):
        input_data = info.input
        birth_date = input_data.get('age')  # Es un datetime después del scalar
        
        if birth_date:
            # Calcular edad
            today = datetime.now()
            age = today.year - birth_date.year
            if today.month < birth_date.month or \
               (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            
            # Validar edad mínima
            if age < 30:
                error_descriptor = ErrorDescriptor(
                    message="User must be at least 30 years old",
                    code="AGE_VALIDATION_FAILED",
                    level=LEVEL_FATAL
                )
                
                extensions = {
                    'field': 'age',
                    'minimumAge': 30,
                    'providedAge': age,
                    'birthDate': birth_date.strftime('%Y-%m-%d')
                }
                
                raise new_error(err=error_descriptor, extensions=extensions)
        
        # Crear usuario...
        return {
            'id': '3',
            'name': input_data['name'],
            'age': birth_date
        }
```

### Ejemplo con Múltiples Validaciones

```python
from pgql import Resolver, ResolverInfo, new_fatal, new_warning

class Product(Resolver):
    
    def create_product(self, info: ResolverInfo):
        input_data = info.input
        
        # Validación crítica (Fatal)
        if input_data.get('price', 0) <= 0:
            raise new_fatal(
                message="Price must be greater than zero",
                extensions={
                    'field': 'price',
                    'providedValue': input_data.get('price')
                }
            )
        
        # Advertencia no crítica (Warning)
        if input_data.get('stock', 0) < 10:
            raise new_warning(
                message="Low stock level",
                extensions={
                    'field': 'stock',
                    'currentStock': input_data.get('stock'),
                    'recommendedMinimum': 10
                }
            )
        
        # Crear producto...
        return {
            'id': '123',
            'name': input_data['name'],
            'price': input_data['price']
        }
```

## Formato de Respuesta

### Respuesta con Fatal Error

**Request:**
```graphql
mutation {
  createUser(input: { name: "John", age: "2005-01-01", email: "john@test.com" }) {
    id
    name
    age
  }
}
```

**Response:**
```json
{
  "data": null,
  "errors": [
    {
      "message": "User must be at least 30 years old",
      "extensions": {
        "code": "AGE_VALIDATION_FAILED",
        "level": "fatal",
        "field": "age",
        "minimumAge": 30,
        "providedAge": 19,
        "birthDate": "2005-01-01"
      }
    }
  ]
}
```

### Respuesta con Warning

**Request:**
```graphql
mutation {
  createProduct(input: { name: "Widget", price: 10.99, stock: 5 }) {
    id
    name
    price
  }
}
```

**Response:**
```json
{
  "data": {
    "createProduct": {
      "id": "123",
      "name": "Widget",
      "price": 10.99
    }
  },
  "errors": [
    {
      "message": "Low stock level",
      "extensions": {
        "code": "000",
        "level": "warning",
        "field": "stock",
        "currentStock": 5,
        "recommendedMinimum": 10
      }
    }
  ]
}
```

### Respuesta con GraphQL Error Estándar

Si lanzas un error de Python estándar o un `GraphQLError`, se formatea automáticamente:

```python
def get_user(self, info: ResolverInfo):
    raise ValueError("User not found")
```

**Response:**
```json
{
  "data": null,
  "errors": [
    {
      "message": "User not found"
    }
  ]
}
```

## Ejemplos Completos

### Validación de Email

```python
import re
from pgql import Resolver, ResolverInfo, new_fatal

class User(Resolver):
    
    def create_user(self, info: ResolverInfo):
        email = info.input.get('email', '')
        
        # Validar formato de email
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            raise new_fatal(
                message="Invalid email format",
                extensions={
                    'field': 'email',
                    'providedValue': email,
                    'expectedPattern': email_pattern
                }
            )
        
        # Crear usuario...
        return {'id': '1', 'email': email}
```

### Validación con ErrorDescriptor Reutilizable

```python
from pgql import Resolver, ResolverInfo, new_error, ErrorDescriptor, LEVEL_FATAL

# Definir errores reutilizables
ERRORS = {
    'UNAUTHORIZED': ErrorDescriptor(
        message="User is not authorized to perform this action",
        code="UNAUTHORIZED",
        level=LEVEL_FATAL
    ),
    'INSUFFICIENT_FUNDS': ErrorDescriptor(
        message="Insufficient funds for this transaction",
        code="INSUFFICIENT_FUNDS",
        level=LEVEL_FATAL
    )
}

class Transaction(Resolver):
    
    def create_transaction(self, info: ResolverInfo):
        user_id = info.input.get('userId')
        amount = info.input.get('amount')
        
        # Verificar autorización
        if not self._is_authorized(user_id):
            raise new_error(err=ERRORS['UNAUTHORIZED'], extensions={'userId': user_id})
        
        # Verificar fondos
        balance = self._get_balance(user_id)
        if balance < amount:
            raise new_error(
                err=ERRORS['INSUFFICIENT_FUNDS'],
                extensions={
                    'userId': user_id,
                    'requiredAmount': amount,
                    'currentBalance': balance,
                    'deficit': amount - balance
                }
            )
        
        # Crear transacción...
        return {'id': '1', 'amount': amount, 'status': 'completed'}
```

### Validación de Rangos

```python
from pgql import Resolver, ResolverInfo, new_fatal

class Event(Resolver):
    
    def create_event(self, info: ResolverInfo):
        capacity = info.input.get('capacity', 0)
        min_capacity = 10
        max_capacity = 1000
        
        # Validar rango
        if capacity < min_capacity or capacity > max_capacity:
            raise new_fatal(
                message=f"Capacity must be between {min_capacity} and {max_capacity}",
                extensions={
                    'field': 'capacity',
                    'providedValue': capacity,
                    'minAllowed': min_capacity,
                    'maxAllowed': max_capacity
                }
            )
        
        # Crear evento...
        return {'id': '1', 'capacity': capacity}
```

## Mejores Prácticas

### 1. **Usa Códigos de Error Descriptivos**

```python
# ❌ Malo - código genérico
raise new_fatal(message="Validation failed", code="ERROR")

# ✅ Bueno - código específico
raise new_fatal(message="Email already exists", code="EMAIL_ALREADY_EXISTS")
```

### 2. **Proporciona Extensions Útiles**

```python
# ❌ Malo - sin contexto
raise new_fatal(message="Invalid value")

# ✅ Bueno - con contexto completo
raise new_fatal(
    message="Invalid value for field 'age'",
    extensions={
        'field': 'age',
        'providedValue': -5,
        'constraint': 'must be positive integer',
        'minValue': 0
    }
)
```

### 3. **Reutiliza ErrorDescriptors**

```python
# Definir errores comunes una vez
ERROR_DESCRIPTORS = {
    'NOT_FOUND': ErrorDescriptor(
        message="Resource not found",
        code="NOT_FOUND",
        level=LEVEL_FATAL
    ),
    'DUPLICATE': ErrorDescriptor(
        message="Resource already exists",
        code="DUPLICATE_RESOURCE",
        level=LEVEL_FATAL
    )
}

# Usar en múltiples resolvers
raise new_error(
    err=ERROR_DESCRIPTORS['NOT_FOUND'],
    extensions={'resourceType': 'User', 'id': user_id}
)
```

### 4. **Usa Warning para Información No Crítica**

```python
# Warning - ejecución continúa
if stock < 10:
    raise new_warning(
        message="Low stock warning",
        extensions={'currentStock': stock}
    )

# Fatal - ejecución se detiene
if stock <= 0:
    raise new_fatal(
        message="Out of stock",
        extensions={'product': product_id}
    )
```

### 5. **Valida Temprano, Falla Rápido**

```python
def create_user(self, info: ResolverInfo):
    # Validar todas las entradas al inicio
    email = info.input.get('email')
    if not email:
        raise new_fatal(message="Email is required", extensions={'field': 'email'})
    
    age = info.input.get('age')
    if age < 18:
        raise new_fatal(message="Must be 18+", extensions={'field': 'age', 'provided': age})
    
    # Continuar con la lógica de negocio...
```

### 6. **Estructura de Extensions Consistente**

Mantén una estructura consistente en tus extensions:

```python
# Estructura sugerida
extensions = {
    'field': 'nombre_del_campo',           # Campo que causó el error
    'providedValue': valor_recibido,       # Valor que causó el problema
    'constraint': 'descripción_restricción', # Qué restricción se violó
    'additionalInfo': {...}                # Info adicional específica
}
```

### 7. **Documentar Códigos de Error**

Mantén un catálogo de códigos de error en tu proyecto:

```python
# errors/codes.py
"""
Códigos de error de la aplicación:

- EMAIL_INVALID: Formato de email inválido
- EMAIL_ALREADY_EXISTS: El email ya está registrado
- AGE_VALIDATION_FAILED: Edad no cumple requisitos mínimos
- UNAUTHORIZED: Usuario no autorizado para la acción
- INSUFFICIENT_FUNDS: Fondos insuficientes para transacción
- RESOURCE_NOT_FOUND: Recurso solicitado no existe
"""

ERROR_CODES = {
    'EMAIL_INVALID': 'EMAIL_INVALID',
    'EMAIL_EXISTS': 'EMAIL_ALREADY_EXISTS',
    'AGE_INVALID': 'AGE_VALIDATION_FAILED',
    # ... más códigos
}
```

## Compatibilidad con GraphQL Spec

El sistema de errores de `pygql` es totalmente compatible con la especificación GraphQL:
- https://spec.graphql.org/October2021/#sec-Errors

Todos los errores incluyen:
- `message`: Mensaje descriptivo del error
- `extensions`: Información adicional (incluyendo `code` y `level`)
- `path`: (automático) Ruta en la query donde ocurrió el error
- `locations`: (automático) Ubicación en el documento GraphQL

## Compatibilidad con gogql (Go)

Este sistema de errores es compatible con `gogql` (implementación en Go), permitiendo:
- Misma estructura de errores entre Python y Go
- Mismos niveles (Warning/Fatal)
- Mismo formato de respuesta
- Migración sencilla entre implementaciones
