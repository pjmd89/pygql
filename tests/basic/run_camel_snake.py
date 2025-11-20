"""
Ejemplo completo demostrando conversión automática camelCase → snake_case.

GraphQL Schema usa camelCase (convención):
- getUser
- getAllUsers  
- firstName
- emailAddress

Resolvers Python usan snake_case (convención):
- get_user
- get_all_users
- first_name
- email_address

El framework convierte automáticamente.
"""

from pgql import HTTPServer

# Resolvers con métodos en snake_case (convención Python)
class QueryResolvers:
    def get_user(self, parent, info, user_id):
        """
        GraphQL: getUser(userId: ID!)
        Python:  get_user(user_id)
        
        ✅ Conversión automática
        """
        print(f"🔍 get_user llamado con user_id={user_id}")
        return {
            'id': user_id,
            'firstName': 'John',
            'lastName': 'Doe',
            'emailAddress': 'john.doe@example.com'
        }
    
    def get_all_users(self, parent, info):
        """
        GraphQL: getAllUsers
        Python:  get_all_users
        
        ✅ Conversión automática
        """
        print("🔍 get_all_users llamado")
        return [
            {
                'id': '1',
                'firstName': 'Jane',
                'lastName': 'Smith',
                'emailAddress': 'jane.smith@example.com'
            },
            {
                'id': '2',
                'firstName': 'Bob',
                'lastName': 'Johnson',
                'emailAddress': 'bob.johnson@example.com'
            }
        ]


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 Demo: camelCase (GraphQL) → snake_case (Python)")
    print("=" * 70)
    
    # Crear servidor
    server = HTTPServer("tests/basic/config_camel_snake.yml")
    
    # Registrar resolvers
    print("\n📦 Registering resolvers...")
    server.gql({
        'Query': QueryResolvers()
    })
    
    print("\n" + "=" * 70)
    print("✨ Server ready!")
    print("=" * 70)
    print("\n📝 GraphQL Schema usa camelCase:")
    print("   - getUser(userId: ID!)")
    print("   - getAllUsers")
    print("   - firstName, lastName, emailAddress")
    print("\n🐍 Python Resolvers usan snake_case:")
    print("   - get_user(user_id)")
    print("   - get_all_users()")
    print("   - first_name, last_name, email_address")
    print("\n✅ El framework convierte automáticamente!")
    
    print("\n" + "=" * 70)
    print("🌐 Server starting on http://localhost:8080/graphql")
    print("=" * 70)
    print("\n📋 Try these queries:")
    print("\n1️⃣  Get single user:")
    print("""
query {
  getUser(userId: "123") {
    id
    firstName
    lastName
    emailAddress
  }
}
""")
    print("\n2️⃣  Get all users:")
    print("""
query {
  getAllUsers {
    id
    firstName
    lastName
    emailAddress
  }
}
""")
    print("\n3️⃣  Using curl:")
    print("""
curl -X POST http://localhost:8080/graphql \\
  -H "Content-Type: application/json" \\
  -d '{"query": "{ getAllUsers { id firstName lastName } }"}'
""")
    print("\n" + "=" * 70 + "\n")
    
    server.start()
