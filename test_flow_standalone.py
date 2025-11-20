"""
Test STANDALONE para verificar el flujo de assess()
NO importa nada de pgql para evitar dependencias
"""
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Optional, Any

# Copia de las clases necesarias
@dataclass
class ScalarResolved:
    value: Any
    kind: str

class Error:
    def __init__(self, message: str, fatal: bool = False):
        self.message = message
        self.fatal = fatal
    
    def __str__(self):
        return f"{'FATAL' if self.fatal else 'WARNING'}: {self.message}"

def new_fatal(message: str) -> Error:
    return Error(message, fatal=True)

class Scalar(ABC):
    @abstractmethod
    def set(self, value: Any) -> Any:
        pass
    
    @abstractmethod
    def assess(self, resolved: ScalarResolved) -> Tuple[Any, Optional[Error]]:
        pass

# DateScalar implementation
class DateScalar(Scalar):
    def set(self, value):
        if value is None:
            return None
        return value.strftime("%Y-%m-%d")
    
    def assess(self, resolved: ScalarResolved):
        print(f"🔍 [ASSESS] DateScalar.assess() llamado")
        print(f"   Input value: '{resolved.value}'")
        print(f"   Input kind: {resolved.kind}")
        
        try:
            parsed = datetime.strptime(resolved.value, "%Y-%m-%d")
            print(f"✅ [ASSESS] Parseado exitosamente")
            print(f"   Result: {parsed}")
            print(f"   Type: {type(parsed)}")
            return (parsed, None)
        except ValueError as e:
            print(f"❌ [ASSESS] Error al parsear: {e}")
            return (None, new_fatal(str(e)))

# Simulación del flujo completo
def simulate_graphql_flow(input_string: str):
    """
    Simula el flujo completo:
    1. GraphQL recibe string "2025-11-16"
    2. assess() lo parsea a datetime
    3. El resultado va a kwargs
    4. kwargs se convierte a snake_kwargs
    5. snake_kwargs se asigna a resolver_info.args
    6. El resolver accede a info.args.get('after')
    """
    print("\n" + "=" * 70)
    print(f"SIMULANDO FLUJO: Query con after=\"{input_string}\"")
    print("=" * 70)
    
    # PASO 1: GraphQL ejecuta assess()
    print("\n📌 PASO 1: GraphQL ejecuta scalar.assess()")
    print("-" * 70)
    
    scalar = DateScalar()
    resolved = ScalarResolved(value=input_string, kind="STRING")
    parsed_value, error = scalar.assess(resolved)
    
    if error:
        print(f"\n❌ ERROR en assess(): {error}")
        return
    
    print(f"\n✅ assess() retornó: {parsed_value} (tipo: {type(parsed_value)})")
    
    # PASO 2: El valor parseado va a kwargs
    print("\n📌 PASO 2: Valor parseado se pone en kwargs")
    print("-" * 70)
    kwargs = {'after': parsed_value}
    print(f"kwargs = {kwargs}")
    print(f"kwargs['after'] = {kwargs['after']}")
    print(f"type(kwargs['after']) = {type(kwargs['after'])}")
    
    # PASO 3: kwargs se convierte a snake_kwargs (no cambia en este caso)
    print("\n📌 PASO 3: kwargs se convierte a snake_kwargs")
    print("-" * 70)
    snake_kwargs = {key: value for key, value in kwargs.items()}
    print(f"snake_kwargs = {snake_kwargs}")
    print(f"snake_kwargs['after'] = {snake_kwargs['after']}")
    print(f"type(snake_kwargs['after']) = {type(snake_kwargs['after'])}")
    
    # PASO 4: snake_kwargs se asigna a resolver_info.args
    print("\n📌 PASO 4: snake_kwargs se asigna a resolver_info.args")
    print("-" * 70)
    
    @dataclass
    class ResolverInfo:
        args: dict
    
    resolver_info = ResolverInfo(args=snake_kwargs)
    print(f"resolver_info.args = {resolver_info.args}")
    print(f"resolver_info.args['after'] = {resolver_info.args['after']}")
    print(f"type(resolver_info.args['after']) = {type(resolver_info.args['after'])}")
    
    # PASO 5: Resolver accede a info.args.get('after')
    print("\n📌 PASO 5: Resolver accede a info.args.get('after')")
    print("-" * 70)
    
    def events_resolver(info: ResolverInfo):
        after = info.args.get('after')
        print(f"⚡ [RESOLVER] events() llamado")
        print(f"   after = {after}")
        print(f"   type(after) = {type(after)}")
        
        events = [
            {"id": "1", "name": "Event A", "date": datetime(2025, 11, 15)},
            {"id": "2", "name": "Event B", "date": datetime(2025, 11, 17)},
            {"id": "3", "name": "Event C", "date": datetime(2025, 11, 20)},
        ]
        
        if after:
            print(f"   Filtrando eventos después de {after}...")
            filtered = [e for e in events if e["date"] > after]
            print(f"   ✅ {len(filtered)} eventos encontrados después de {after}")
            return filtered
        else:
            print(f"   ⚠️  after=None, retornando todos los eventos")
            return events
    
    result = events_resolver(resolver_info)
    
    print("\n📊 RESULTADO FINAL:")
    print("-" * 70)
    print(f"Eventos retornados: {len(result)}")
    for event in result:
        print(f"  - {event['name']} ({event['date'].strftime('%Y-%m-%d')})")
    
    print("\n" + "=" * 70)
    print("✅ FLUJO COMPLETO SIMULADO")
    print("=" * 70)

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TEST STANDALONE: Flujo completo de assess() → resolver")
    print("=" * 70)
    
    # Test con fecha válida
    simulate_graphql_flow("2025-11-16")
    
    print("\n\n")
    
    # Test con fecha inválida
    print("=" * 70)
    print("TEST 2: Fecha inválida")
    print("=" * 70)
    simulate_graphql_flow("invalid-date")
