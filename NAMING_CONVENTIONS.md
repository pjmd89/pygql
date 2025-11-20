# Conversión Automática: camelCase ↔ snake_case

pygql convierte automáticamente entre las convenciones de nombres de GraphQL (camelCase) y Python (snake_case).

## 🎯 ¿Por qué?

- **GraphQL** usa `camelCase` por convención: `getUser`, `firstName`, `userId`
- **Python** usa `snake_case` por convención (PEP 8): `get_user`, `first_name`, `user_id`

El framework convierte automáticamente para que puedas escribir código Python idiomático.

---

## 🔄 Conversión Automática

### Nombres de Resolvers

**GraphQL Schema:**
```graphql
type Query {
    getUser(userId: ID!): User
    getAllUsers: [User!]!
}
```

**Python Resolvers:**
```python
class QueryResolvers:
    def get_user(self, parent, info, user_id):
        # GraphQL: getUser(userId)
        # Python:  get_user(user_id)
        return {'id': user_id, ...}
    
    def get_all_users(self, parent, info):
        # GraphQL: getAllUsers
        # Python:  get_all_users
        return [...]
```

### Nombres de Campos

**GraphQL Schema:**
```graphql
type User {
    id: ID!
    firstName: String!
    lastName: String!
    emailAddress: String!
}
```

**Python Resolvers (si necesitas custom logic):**
```python
class UserResolvers:
    def first_name(self, parent, info):
        # GraphQL: firstName
        # Python:  first_name
        return parent.get('firstName')
    
    def email_address(self, parent, info):
        # GraphQL: emailAddress
        # Python:  email_address
        return parent.get('emailAddress')
```

### Argumentos

**GraphQL Query:**
```graphql
query {
  getUser(userId: "123") {
    firstName
    lastName
  }
}
```

**Python Resolver:**
```python
def get_user(self, parent, info, user_id):
    # GraphQL envía: userId="123"
    # Python recibe: user_id="123"
    print(f"User ID: {user_id}")
    return {...}
```

---

## 📋 Ejemplos de Conversión

| GraphQL (camelCase) | Python (snake_case) |
|---------------------|---------------------|
| `getUser` | `get_user` |
| `getAllUsers` | `get_all_users` |
| `firstName` | `first_name` |
| `lastName` | `last_name` |
| `emailAddress` | `email_address` |
| `userId` | `user_id` |
| `createdAt` | `created_at` |
| `isActive` | `is_active` |

---

## 🚀 Ejemplo Completo

Ver `tests/basic/run_camel_snake.py` para un ejemplo funcional completo.

**Ejecutar:**
```bash
python tests/basic/run_camel_snake.py
```

**Probar:**
```bash
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ getAllUsers { id firstName lastName } }"}'
```

---

## 💡 Notas Importantes

1. **Datos de retorno**: Los diccionarios que retornas deben usar las mismas keys que el schema GraphQL (camelCase):
   ```python
   def get_user(self, parent, info, user_id):
       return {
           'id': user_id,
           'firstName': 'John',  # ← camelCase (GraphQL)
           'lastName': 'Doe'
       }
   ```

2. **Solo para métodos**: La conversión solo aplica a nombres de métodos y argumentos, NO a los datos:
   ```python
   # ✅ Correcto
   def get_user(self, parent, info, user_id):  # snake_case
       return {'firstName': 'John'}  # camelCase en datos
   
   # ❌ Incorrecto
   def get_user(self, parent, info, user_id):
       return {'first_name': 'John'}  # GraphQL no encontrará este campo
   ```

3. **Automático y transparente**: No necesitas hacer nada especial, la conversión es automática.

---

## 🧪 Test de Conversión

Ejecuta el test para verificar la conversión:

```bash
python tests/basic/test_camel_snake.py
```

Output esperado:
```
✅ getUser              → get_user
✅ getAllUsers          → get_all_users  
✅ firstName            → first_name
✅ lastName             → last_name
✅ emailAddress         → email_address
✅ userId               → user_id
```

---

## 📚 Relacionado

- Ver `SCALARS.md` para custom scalars
- Ver `tests/basic/run_camel_snake.py` para ejemplo completo
