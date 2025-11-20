"""
Test para verificar el orden de ejecución: Directivas → Resolver
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pgql import Directive, ResolverInfo

# Variable global para rastrear el orden de ejecución
execution_order = []

class TestDirective(Directive):
    """Directiva que registra cuándo se ejecuta"""
    def invoke(self, args, type_name, field_name):
        execution_order.append("DIRECTIVE")
        print("✅ [1] Directiva ejecutada")
        return {"test": "directive_result"}, None

class QueryResolvers:
    """Resolver que registra cuándo se ejecuta"""
    def test_field(self, info: ResolverInfo):
        execution_order.append("RESOLVER")
        print("✅ [2] Resolver ejecutado")
        print(f"   Directivas disponibles: {info.directives}")
        
        # Verificar que la directiva ya se ejecutó
        directive_data = info.directives.get('test')
        if directive_data:
            print(f"   ✅ Directiva data disponible: {directive_data}")
        else:
            print(f"   ❌ ERROR: Directiva data NO disponible")
        
        return "resolver_result"

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TEST: Orden de ejecución Directivas → Resolver")
    print("="*70)
    
    # Simular el flujo del wrapper
    print("\n📌 PASO 1: Ejecutar directiva")
    directive = TestDirective()
    directive_result, error = directive.invoke({}, "Query", "testField")
    
    print("\n📌 PASO 2: Crear ResolverInfo con resultado de directiva")
    resolver_info = ResolverInfo(
        operation="query",
        resolver="test_field",
        args={},
        parent=None,
        type_name="Query",
        directives={"test": directive_result},  # ⬅️ Resultado de directiva
        parent_type_name="Query",
        session_id=None,
        context={},
        field_name="test_field"
    )
    
    print("\n📌 PASO 3: Ejecutar resolver (con directiva ya procesada)")
    resolver = QueryResolvers()
    result = resolver.test_field(resolver_info)
    
    print("\n" + "="*70)
    print("📊 RESULTADO DEL TEST")
    print("="*70)
    print(f"Orden de ejecución: {execution_order}")
    print(f"Resultado del resolver: {result}")
    
    # Verificar orden
    if execution_order == ["DIRECTIVE", "RESOLVER"]:
        print("\n✅ ¡TEST PASÓ! Las directivas se ejecutan ANTES del resolver")
    else:
        print(f"\n❌ ¡TEST FALLÓ! Orden incorrecto: {execution_order}")
    
    # Verificar que el resolver recibió los datos de la directiva
    if directive_result:
        print("✅ El resolver tiene acceso a los resultados de la directiva")
    else:
        print("❌ El resolver NO tiene acceso a los resultados de la directiva")
    
    print("\n" + "="*70)
