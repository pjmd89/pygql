"""
Test para verificar que ResolverInfo funciona correctamente
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pgql import ResolverInfo

def test_resolver_info_creation():
    """Test de creación de ResolverInfo"""
    
    # Crear un ResolverInfo con todos los campos
    info = ResolverInfo(
        operation="query",
        resolver="getUser",
        args={"user_id": 123, "include_profile": True},
        parent=None,
        type_name="User",
        parent_type_name="Query",
        session_id="session-abc-123",
        context={"request": "mock-request"},
        field_name="getUser"
    )
    
    # Verificar todos los campos
    assert info.operation == "query"
    assert info.resolver == "getUser"
    assert info.args == {"user_id": 123, "include_profile": True}
    assert info.parent is None
    assert info.type_name == "User"
    assert info.parent_type_name == "Query"
    assert info.session_id == "session-abc-123"
    assert info.context == {"request": "mock-request"}
    assert info.field_name == "getUser"
    
    print("✅ ResolverInfo creado correctamente")
    print(f"   Operation: {info.operation}")
    print(f"   Resolver: {info.resolver}")
    print(f"   Args: {info.args}")
    print(f"   Type: {info.type_name}")
    print(f"   Parent Type: {info.parent_type_name}")
    print(f"   Session ID: {info.session_id}")

def test_resolver_info_optional_fields():
    """Test con campos opcionales"""
    
    # Crear ResolverInfo solo con campos requeridos
    info = ResolverInfo(
        operation="mutation",
        resolver="createUser",
        args={"name": "John", "email": "john@example.com"},
        parent={"id": 1},
        type_name="User"
    )
    
    # Verificar campos requeridos
    assert info.operation == "mutation"
    assert info.resolver == "createUser"
    assert info.args == {"name": "John", "email": "john@example.com"}
    assert info.parent == {"id": 1}
    assert info.type_name == "User"
    
    # Verificar campos opcionales con valores por defecto
    assert info.parent_type_name is None
    assert info.session_id is None
    assert info.context is None
    assert info.field_name is None
    
    print("✅ ResolverInfo con campos opcionales funciona correctamente")

def test_resolver_info_access_args():
    """Test de acceso a argumentos"""
    
    info = ResolverInfo(
        operation="query",
        resolver="searchUsers",
        args={
            "user_id": 42,
            "first_name": "John",
            "last_name": "Doe",
            "is_active": True,
            "page_size": 10
        },
        parent=None,
        type_name="User"
    )
    
    # Acceder a argumentos con .get()
    assert info.args.get("user_id") == 42
    assert info.args.get("first_name") == "John"
    assert info.args.get("last_name") == "Doe"
    assert info.args.get("is_active") is True
    assert info.args.get("page_size") == 10
    assert info.args.get("nonexistent") is None
    assert info.args.get("nonexistent", "default") == "default"
    
    print("✅ Acceso a argumentos funciona correctamente")
    print(f"   Args disponibles: {list(info.args.keys())}")

def test_resolver_signature():
    """Test de firma de resolver usando ResolverInfo"""
    
    # Simular un resolver real (estilo Go - solo info)
    def get_user(info: ResolverInfo):
        """Resolver que usa ResolverInfo (sin parent separado)"""
        user_id = info.args.get('user_id')
        
        # Acceder a parent desde info
        parent = info.parent
        
        # Verificar contexto
        if info.session_id:
            print(f"   Usuario autenticado: {info.session_id}")
        
        return {
            'id': user_id,
            'name': f'User {user_id}',
            'type': info.type_name,
            'parent': parent
        }
    
    # Crear ResolverInfo y llamar al resolver
    info = ResolverInfo(
        operation="query",
        resolver="getUser",
        args={"user_id": 999},
        parent=None,
        type_name="User",
        session_id="test-session-123"
    )
    
    result = get_user(info)
    
    assert result['id'] == 999
    assert result['name'] == 'User 999'
    assert result['type'] == 'User'
    assert result['parent'] is None
    
    print("✅ Resolver con ResolverInfo funciona correctamente")
    print(f"   Result: {result}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Testing ResolverInfo")
    print("="*60 + "\n")
    
    test_resolver_info_creation()
    print()
    
    test_resolver_info_optional_fields()
    print()
    
    test_resolver_info_access_args()
    print()
    
    test_resolver_signature()
    print()
    
    print("="*60)
    print("✅ Todos los tests de ResolverInfo pasaron")
    print("="*60)
