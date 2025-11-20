"""
Test básico del sistema de directivas
"""
from pgql import Directive, ResolverInfo


class SimpleDirective(Directive):
    """Directiva de ejemplo que agrega metadatos"""
    
    def invoke(self, args, type_name, field_name):
        result = {
            'processed_by': 'SimpleDirective',
            'type': type_name,
            'field': field_name,
            'custom_arg': args.get('value', 'default')
        }
        return result, None


class PaginateDirective(Directive):
    """Directiva de paginación (como tu ejemplo de Go)"""
    
    def invoke(self, args, type_name, field_name):
        page = self._parse_int(args.get('page'), default=1)
        split = self._parse_int(args.get('split'), default=10)
        
        # Asegurar valores positivos
        page = max(1, page)
        split = max(1, split)
        
        paginate_data = {
            'page': page,
            'split': split,
            'skip': (page - 1) * split,
            'limit': split
        }
        
        return paginate_data, None
    
    @staticmethod
    def _parse_int(value, default=0):
        """Parse integer from various types (matches Go's type conversion)"""
        if value is None:
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default


def test_simple_directive():
    """Test directiva simple"""
    print("\n" + "="*60)
    print("Test 1: Directiva Simple")
    print("="*60)
    
    directive = SimpleDirective()
    
    # Simular invocación como lo haría el sistema
    result, error = directive.invoke(
        args={'value': 'test123'},
        type_name='Query',
        field_name='users'
    )
    
    assert error is None, "No debería haber error"
    assert result['processed_by'] == 'SimpleDirective'
    assert result['type'] == 'Query'
    assert result['field'] == 'users'
    assert result['custom_arg'] == 'test123'
    
    print(f"✅ Resultado: {result}")


def test_paginate_directive():
    """Test directiva de paginación"""
    print("\n" + "="*60)
    print("Test 2: Directiva Paginate")
    print("="*60)
    
    directive = PaginateDirective()
    
    # Test 1: Con argumentos
    result, error = directive.invoke(
        args={'page': 2, 'split': 20},
        type_name='Query',
        field_name='posts'
    )
    
    assert error is None
    assert result['page'] == 2
    assert result['split'] == 20
    assert result['skip'] == 20  # (2-1) * 20
    assert result['limit'] == 20
    
    print(f"✅ Página 2, Split 20:")
    print(f"   skip={result['skip']}, limit={result['limit']}")
    
    # Test 2: Sin argumentos (defaults)
    result, error = directive.invoke(
        args={},
        type_name='Query',
        field_name='users'
    )
    
    assert result['page'] == 1
    assert result['split'] == 10
    assert result['skip'] == 0  # (1-1) * 10
    assert result['limit'] == 10
    
    print(f"✅ Defaults: page={result['page']}, split={result['split']}")
    
    # Test 3: Conversión de tipos (string a int)
    result, error = directive.invoke(
        args={'page': '3', 'split': '15'},
        type_name='Query',
        field_name='comments'
    )
    
    assert result['page'] == 3
    assert result['split'] == 15
    assert result['skip'] == 30  # (3-1) * 15
    assert result['limit'] == 15
    
    print(f"✅ Conversión de strings: page={result['page']}, split={result['split']}")


def test_directive_in_resolver_info():
    """Test integración con ResolverInfo"""
    print("\n" + "="*60)
    print("Test 3: Directivas en ResolverInfo")
    print("="*60)
    
    # Simular procesamiento de directivas
    paginate = PaginateDirective()
    paginate_result, _ = paginate.invoke({'page': 3, 'split': 25}, 'Query', 'users')
    
    simple = SimpleDirective()
    simple_result, _ = simple.invoke({'value': 'metadata'}, 'Query', 'users')
    
    # Crear ResolverInfo con directivas procesadas
    info = ResolverInfo(
        operation='query',
        resolver='users',
        args={'filter': 'active'},
        parent=None,
        type_name='Query',
        directives={
            'paginate': paginate_result,
            'simple': simple_result
        }
    )
    
    # Simular uso en resolver
    def users_resolver(info: ResolverInfo):
        """Ejemplo de resolver usando directivas"""
        # Acceder a paginación
        paginate = info.directives.get('paginate')
        if paginate:
            print(f"   📄 Paginación: página {paginate['page']}, skip={paginate['skip']}, limit={paginate['limit']}")
        
        # Acceder a metadata
        simple = info.directives.get('simple')
        if simple:
            print(f"   📝 Metadata: {simple['custom_arg']}")
        
        return {'users': [], 'total': 0}
    
    result = users_resolver(info)
    
    assert info.directives['paginate']['page'] == 3
    assert info.directives['paginate']['skip'] == 50
    assert info.directives['simple']['custom_arg'] == 'metadata'
    
    print("✅ Directivas accesibles en resolver")


if __name__ == "__main__":
    print("\n🧪 TEST SISTEMA DE DIRECTIVAS")
    print("Compatible con Go's Directive interface\n")
    
    test_simple_directive()
    test_paginate_directive()
    test_directive_in_resolver_info()
    
    print("\n" + "="*60)
    print("✅ TODOS LOS TESTS PASARON")
    print("="*60)
    print("\n💡 Próximos pasos:")
    print("   1. server.directive('paginate', PaginateDirective())")
    print("   2. Usar @paginate en schema.gql")
    print("   3. Acceder via info.directives.get('paginate') en resolver")
    print()
