# Configuración de CORS

El servidor HTTP de pygql soporta configuración de CORS (Cross-Origin Resource Sharing) a través del archivo de configuración YAML.

## Configuración en archivo .yml

Agrega la sección `cors` en tu archivo de configuración:

```yaml
http_port: 8080
debug: true
cookie_name: session_id

# Configuración de CORS
cors:
  enabled: true                    # true para habilitar CORS, false para deshabilitar
  allow_credentials: "true"        # "true" o "false" (como string)
  allow_methods: "*"               # "*" o lista específica como "GET, POST, PUT"
  allow_headers: "*"               # "*" o headers específicos como "Content-Type, Authorization"
  max_age: "86400"                 # Tiempo en segundos que el navegador cachea la respuesta preflight
  # Lista de orígenes permitidos (opcional)
  allowed_origins:
    - "http://localhost:3000"
    - "http://localhost:5173"
    - "https://miapp.com"

server:
  host: localhost
  routes:
    - mode: gql
      endpoint: /graphql
      schema: schema
```

## Opciones de Configuración

### `enabled`
- **Tipo**: `boolean`
- **Default**: `true`
- **Descripción**: Habilita o deshabilita completamente el middleware CORS.

### `allow_credentials`
- **Tipo**: `string`
- **Default**: `"true"`
- **Descripción**: Controla el header `Access-Control-Allow-Credentials`. Debe ser `"true"` o `"false"` como string.

### `allow_methods`
- **Tipo**: `string`
- **Default**: `"*"`
- **Descripción**: Controla el header `Access-Control-Allow-Methods`. Puede ser:
  - `"*"` para permitir todos los métodos
  - Lista específica como `"GET, POST, PUT, DELETE"`

### `allow_headers`
- **Tipo**: `string`
- **Default**: `"*"`
- **Descripción**: Controla el header `Access-Control-Allow-Headers`. Puede ser:
  - `"*"` para permitir todos los headers
  - Lista específica como `"Content-Type, Authorization, X-Custom-Header"`

### `max_age`
- **Tipo**: `string`
- **Default**: `"86400"` (24 horas)
- **Descripción**: Controla el header `Access-Control-Max-Age`. Define cuánto tiempo (en segundos) el navegador cachea la respuesta preflight.

### `allowed_origins`
- **Tipo**: `array[string]`
- **Default**: `[]` (lista vacía = permite todos)
- **Descripción**: Lista de orígenes permitidos. Si está vacía o no se define, permite todos los orígenes. Si se define, solo permite los orígenes en la lista.
- **Ejemplo**:
  ```yaml
  allowed_origins:
    - "http://localhost:3000"
    - "https://miapp.com"
  ```

## Validación Dinámica de Orígenes

Existen dos formas de validar orígenes:

### 1. Configuración Estática (archivo YAML)

Define la lista de orígenes permitidos directamente en el archivo de configuración:

```yaml
cors:
  enabled: true
  allowed_origins:
    - "http://localhost:3000"
    - "https://miapp.com"
    - "https://app.midominio.com"
```

### 2. Validación Dinámica (código Python)

Usa el método `on_http_check_origin` para validación programática compleja:

```python
from pgql import HTTPServer

server = HTTPServer('config.yml')

# Validar orígenes dinámicamente (ejemplo: validación compleja)
def check_origin(origin: str, allowed_origins: list[str]) -> bool:
    # Primero validar contra la lista del YAML
    if origin in allowed_origins:
        return True
    
    # Validación adicional: permitir todos los subdominios
    if origin.endswith('.midominio.com'):
        return True
    
    # Validación basada en base de datos
    if is_origin_in_database(origin):
        return True
    
    return False

server.on_http_check_origin(check_origin)
```

**Prioridad de validación:**
1. Si se define `on_http_check_origin()` en el código, **siempre se usa primero**
   - Recibe el `origin` de la request y `allowed_origins` del archivo YAML
   - Puedes combinar ambas fuentes de validación en tu lógica personalizada
2. Si no hay callback, se valida contra `allowed_origins` del archivo YAML
3. Si `allowed_origins` está vacío y no hay callback, **permite todos los orígenes**

## Ejemplos de Configuración

### Desarrollo (permisivo)
```yaml
cors:
  enabled: true
  allow_credentials: "true"
  allow_methods: "*"
  allow_headers: "*"
  max_age: "3600"
```

### Producción (restrictivo con lista de orígenes)
```yaml
cors:
  enabled: true
  allow_credentials: "true"
  allow_methods: "GET, POST, PUT, DELETE"
  allow_headers: "Content-Type, Authorization"
  max_age: "86400"
  allowed_origins:
    - "https://miapp.com"
    - "https://app.miapp.com"
```

### Deshabilitar CORS
```yaml
cors:
  enabled: false
```

## Valores por Defecto

Si la sección `cors` no está presente en el archivo de configuración, se usarán los siguientes valores por defecto:

- `enabled`: `true`
- `allow_credentials`: `"true"`
- `allow_methods`: `"*"`
- `allow_headers`: `"*"`
- `max_age`: `"86400"`
- `allowed_origins`: `[]` (lista vacía = permite todos los orígenes)

Esto garantiza compatibilidad con configuraciones existentes que no especifican CORS.

## Comportamiento

- Si `enabled: false`, el middleware CORS **no se aplica** y las requests se procesan normalmente sin headers CORS.
- Si `enabled: true` y un origen no está permitido, la respuesta será 403 (Forbidden).
- Los headers CORS solo se agregan si hay un header `Origin` en la request.
- Las requests preflight (OPTIONS) se manejan automáticamente cuando CORS está habilitado.

### Validación de Orígenes - Orden de Prioridad:
1. **Callback `on_http_check_origin()`**: Si está definido en el código, se usa primero
2. **Lista `allowed_origins`**: Si no hay callback, se valida contra la lista del YAML
3. **Permite todos**: Si no hay callback ni lista, permite todos los orígenes
