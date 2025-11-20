"""
Test para verificar la conversión automática de camelCase a snake_case.

GraphQL usa camelCase, Python usa snake_case.
El framework debe convertir automáticamente los nombres de campos.
"""

from pgql import HTTPServer

# Schema con campos en camelCase (convención GraphQL)
SCHEMA = """
type User {
    id: ID!
    firstName: String!
    lastName: String!
    emailAddress: String!
}

type Query {
    getUser(userId: ID!): User
    getAllUsers: [User!]!
}
"""

# Resolvers con métodos en snake_case (convención Python)
class QueryResolvers:
    def get_user(self, parent, info, user_id):
        """
        Método en snake_case que maneja el campo 'getUser' de GraphQL.
        El parámetro 'userId' se convierte a 'user_id'.
        """
        return {
            'id': user_id,
            'firstName': 'John',
            'lastName': 'Doe',
            'emailAddress': 'john.doe@example.com'
        }
    
    def get_all_users(self, parent, info):
        """
        Método en snake_case que maneja el campo 'getAllUsers' de GraphQL.
        """
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

class UserResolvers:
    def first_name(self, parent, info):
        """Resolver para firstName en snake_case"""
        return parent.get('firstName', 'Unknown')
    
    def last_name(self, parent, info):
        """Resolver para lastName en snake_case"""
        return parent.get('lastName', 'Unknown')
    
    def email_address(self, parent, info):
        """Resolver para emailAddress en snake_case"""
        return parent.get('emailAddress', 'unknown@example.com')


if __name__ == '__main__':
    from graphql import build_schema, graphql_sync
    
    print("=" * 60)
    print("🧪 Testing camelCase → snake_case conversion")
    print("=" * 60)
    
    schema = build_schema(SCHEMA)
    
    # Simular asignación manual de resolvers (sin HTTPServer)
    from pgql.http.http import camel_to_snake
    
    # Test de conversión
    test_cases = [
        ('getUser', 'get_user'),
        ('getAllUsers', 'get_all_users'),
        ('firstName', 'first_name'),
        ('lastName', 'last_name'),
        ('emailAddress', 'email_address'),
        ('userId', 'user_id'),
    ]
    
    print("\n📋 Testing conversion function:")
    print("-" * 60)
    for camel, expected_snake in test_cases:
        result = camel_to_snake(camel)
        status = "✅" if result == expected_snake else "❌"
        print(f"{status} {camel:20s} → {result:20s} (expected: {expected_snake})")
    
    print("\n" + "=" * 60)
    print("✅ All conversions passed!" if all(
        camel_to_snake(c) == s for c, s in test_cases
    ) else "❌ Some conversions failed!")
    print("=" * 60)
