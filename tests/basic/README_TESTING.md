# Guía de Pruebas para pygql

Esta guía explica cómo ejecutar las pruebas de **Manejo de Errores**, **Scalars** y **Directivas**.

## 📋 Requisitos Previos

1. **Activar el entorno virtual:**
   ```bash
   source /home/munozp/Proyectos/python/venv/pygql/bin/activate
   ```

2. **Instalar el paquete en modo desarrollo:**
   ```bash
   cd /home/munozp/Proyectos/python/pygql
   pip install -e .
   ```

---

## 🧪 Tests Unitarios (Sin Servidor)

Estos tests se ejecutan rápidamente y no requieren un servidor HTTP.

### 1️⃣ Test de Manejo de Errores

**Qué prueba:**
- Creación de errores con `new_warning()` y `new_fatal()`
- Errores con mensajes y contexto
- Integración con ResolverInfo

**Ejecutar:**
```bash
cd /home/munozp/Proyectos/python/pygql
python tests/basic/test_errors.py
```

**Salida esperada:**
```
======================================================================
TEST 1: Creación básica de errores
======================================================================
✅ Warning creado correctamente
✅ Fatal creado correctamente
...
✅ TODOS LOS TESTS PASARON
```

---

### 2️⃣ Test de Scalars

**Qué prueba:**
- Método `assess()` (input: cliente → resolver)
- Método `set()` (output: resolver → cliente)
- Validación de tipos personalizados (Date, URL, JSON)
- Manejo de errores en scalars

**Ejecutar:**
```bash
cd /home/munozp/Proyectos/python/pygql
python tests/basic/test_scalars.py
```

**Salida esperada:**
```
======================================================================
TEST 1: DateScalar - assess() (input validation)
======================================================================
✅ Fecha válida parseada correctamente
✅ Fecha inválida rechazada con error
...
✅ TODOS LOS TESTS DE SCALARS PASARON
```

---

### 3️⃣ Test de Directivas

**Qué prueba:**
- Método `invoke()` de directivas
- Directivas con argumentos
- Directivas de paginación
- Integración con ResolverInfo

**Ejecutar:**
```bash
cd /home/munozp/Proyectos/python/pygql
python tests/basic/test_directives.py
```

**Salida esperada:**
```
======================================================================
TEST 1: SimpleDirective básica
======================================================================
✅ Directiva ejecutada sin errores
✅ Resultado correcto
...
✅ TODOS LOS TESTS DE DIRECTIVAS PASARON
```

---

## 🌐 Servidores de Prueba (Con HTTP)

Estos tests inician un servidor HTTP real que puedes consultar con `curl`.

### 4️⃣ Servidor con Scalars

**Qué prueba:**
- Scalars en queries reales
- DateScalar, URLScalar, JSONScalar
- Integración completa

**Paso 1: Iniciar servidor**
```bash
cd /home/munozp/Proyectos/python/pygql
source /home/munozp/Proyectos/python/venv/pygql/bin/activate
python tests/basic/run_with_scalars.py
```

**Paso 2: En otra terminal, ejecutar queries**

**Query 1: Obtener todos los eventos**
```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ events { id name date website metadata } }"}'
```

**Salida esperada:**
```json
{
  "data": {
    "events": [
      {
        "id": "1",
        "name": "Python Conference 2025",
        "date": "2025-12-01",
        "website": "https://pycon2025.org",
        "metadata": "{\"location\": \"Madrid\", \"capacity\": 500}"
      },
      ...
    ]
  }
}
```

**Query 2: Filtrar por fecha (usando DateScalar)**
```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ events(after: \"2025-11-16\") { id name date } }"}'
```

**Salida esperada:**
```json
{
  "data": {
    "events": [
      {
        "id": "2",
        "name": "JavaScript Summit 2025",
        "date": "2025-11-17"
      },
      {
        "id": "3",
        "name": "Go Conference 2025",
        "date": "2025-11-20"
      }
    ]
  }
}
```

**Query 3: Error de validación (fecha inválida)**
```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ events(after: \"fecha-invalida\") { id name date } }"}'
```

**Salida esperada:**
```json
{
  "data": null,
  "errors": [
    "time data 'fecha-invalida' does not match format '%Y-%m-%d'"
  ]
}
```

**Detener servidor:**
```bash
# En la terminal donde corre el servidor: Ctrl+C
# O desde otra terminal:
pkill -f "run_with_scalars.py"
```

---

### 5️⃣ Servidor con Directivas

**Qué prueba:**
- Directivas @paginate
- Directivas @uppercase
- Directivas en schema (FIELD_DEFINITION)
- Directivas en query (FIELD)
- Named operations

**Paso 1: Iniciar servidor**
```bash
cd /home/munozp/Proyectos/python/pygql
source /home/munozp/Proyectos/python/venv/pygql/bin/activate
python tests/basic/run_with_directives.py
```

**Paso 2: En otra terminal, ejecutar queries**

**Query 1: Paginación (directiva en schema)**
```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users(page: 2, split: 3) { data { id name } page total } }"}'
```

**Salida esperada:**
```json
{
  "data": {
    "users": {
      "data": [
        {"id": "4", "name": "User 4"},
        {"id": "5", "name": "User 5"},
        {"id": "6", "name": "User 6"}
      ],
      "page": 2,
      "total": 10
    }
  }
}
```

**Query 2: Directiva en query (inline)**
```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ allUsers @paginate(page: 1, split: 5) { id name } }"}'
```

**Query 3: Named operation con directiva**
```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query GetUsers { users(page: 1, split: 5) { data { id name } page total } }"}'
```

**Query 4: Directiva @uppercase**
```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ message }"}'
```

**Salida esperada:**
```json
{
  "data": {
    "message": "HELLO WORLD"
  }
}
```

**Detener servidor:**
```bash
pkill -f "run_with_directives.py"
```

---

## 📊 Resumen de Comandos Rápidos

### Tests unitarios (ejecutar todos)
```bash
cd /home/munozp/Proyectos/python/pygql
source /home/munozp/Proyectos/python/venv/pygql/bin/activate

# Test de errores
python tests/basic/test_errors.py

# Test de scalars
python tests/basic/test_scalars.py

# Test de directivas
python tests/basic/test_directives.py
```

### Servidores de prueba
```bash
# Terminal 1: Iniciar servidor
source /home/munozp/Proyectos/python/venv/pygql/bin/activate
cd /home/munozp/Proyectos/python/pygql

# Servidor con scalars
python tests/basic/run_with_scalars.py

# O servidor con directivas
python tests/basic/run_with_directives.py

# Terminal 2: Ejecutar queries
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ ... }"}'
```

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'pgql'"
**Solución:**
```bash
cd /home/munozp/Proyectos/python/pygql
source /home/munozp/Proyectos/python/venv/pygql/bin/activate
pip install -e .
```

### Error: "Address already in use"
**Solución:** El servidor ya está corriendo. Detenerlo:
```bash
pkill -f "run_with_scalars.py"
pkill -f "run_with_directives.py"
```

### Error: "command not found: curl"
**Solución:** Instalar curl:
```bash
sudo apt-get install curl  # Ubuntu/Debian
```

O usar Python:
```bash
python -c "import requests; print(requests.post('http://localhost:8080/graphql', json={'query': '{ ... }'}).json())"
```

---

## 📝 Notas

- Los tests unitarios son **independientes** - puedes ejecutarlos en cualquier orden
- Los servidores HTTP ocupan el puerto **8080** - solo uno puede correr a la vez
- Usa `Ctrl+C` para detener los servidores
- Los logs del servidor muestran el orden de ejecución de directivas y resolvers
- Todos los tests están en `/home/munozp/Proyectos/python/pygql/tests/basic/`

---

## ✅ Checklist de Pruebas

- [ ] `test_errors.py` - Manejo de errores
- [ ] `test_scalars.py` - Scalars (assess/set)
- [ ] `test_directives.py` - Directivas (invoke)
- [ ] `run_with_scalars.py` + queries - Scalars en HTTP
- [ ] `run_with_directives.py` + queries - Directivas en HTTP
