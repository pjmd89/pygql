"""
Test unitario para verificar que assess() funciona correctamente
SIN necesidad de iniciar un servidor HTTP
"""
import sys
sys.path.insert(0, '/home/munozp/Proyectos/python/pygql')

from pgql.resolvers.base import Scalar, ScalarResolved
from pgql.errors import new_fatal
from datetime import datetime

# DateScalar
class DateScalar(Scalar):
    def set(self, value):
        if value is None:
            return None
        return value.strftime("%Y-%m-%d")
    
    def assess(self, resolved: ScalarResolved):
        print(f"🔍 [TEST] DateScalar.assess() llamado con: '{resolved.value}'")
        try:
            parsed = datetime.strptime(resolved.value, "%Y-%m-%d")
            print(f"✅ [TEST] Parseado exitosamente: {parsed}")
            print(f"✅ [TEST] Tipo: {type(parsed)}")
            return (parsed, None)
        except ValueError as e:
            print(f"❌ [TEST] Error al parsear: {e}")
            return (None, new_fatal(str(e)))

# Test manual
if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA: DateScalar.assess()")
    print("=" * 60)
    print()
    
    scalar = DateScalar()
    
    # Test 1: Fecha válida
    print("TEST 1: Fecha válida '2025-11-16'")
    print("-" * 60)
    resolved = ScalarResolved(value="2025-11-16", kind="STRING")
    result, error = scalar.assess(resolved)
    
    print(f"\n📊 RESULTADO:")
    print(f"   result = {result}")
    print(f"   error = {error}")
    print(f"   type(result) = {type(result)}")
    
    if result:
        print(f"\n✅ TEST 1 PASÓ: assess() retornó datetime correctamente")
        print(f"   Valor parseado: {result}")
        print(f"   Tipo: {type(result)}")
    else:
        print(f"\n❌ TEST 1 FALLÓ: assess() no retornó datetime")
    
    print("\n" + "=" * 60)
    
    # Test 2: Fecha inválida
    print("\nTEST 2: Fecha inválida 'invalid-date'")
    print("-" * 60)
    resolved = ScalarResolved(value="invalid-date", kind="STRING")
    result, error = scalar.assess(resolved)
    
    print(f"\n📊 RESULTADO:")
    print(f"   result = {result}")
    print(f"   error = {error}")
    
    if error:
        print(f"\n✅ TEST 2 PASÓ: assess() retornó error correctamente")
        print(f"   Error: {error}")
    else:
        print(f"\n❌ TEST 2 FALLÓ: assess() debería haber retornado error")
    
    print("\n" + "=" * 60)
    print("PRUEBAS COMPLETADAS")
    print("=" * 60)
