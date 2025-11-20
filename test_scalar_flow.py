"""
Script simple para probar el flujo de scalars: assess() → resolver
"""
import sys
sys.path.insert(0, '/home/munozp/Proyectos/python/pygql')

from pgql import HTTPServer, Scalar, ScalarResolved, new_fatal, ResolverInfo
from datetime import datetime

# DateScalar simple
class DateScalar(Scalar):
    def set(self, value):
        if value is None:
            return None
        return value.strftime("%Y-%m-%d")
    
    def assess(self, resolved: ScalarResolved):
        print(f"🔍 [ASSESS] DateScalar.assess() llamado con: '{resolved.value}'")
        try:
            parsed = datetime.strptime(resolved.value, "%Y-%m-%d")
            print(f"✅ [ASSESS] DateScalar.assess() retorna: {parsed}")
            return (parsed, None)
        except ValueError as e:
            return (None, new_fatal(str(e)))

# Schema simple
schema = """
scalar Date

type Event {
    id: ID!
    name: String!
    date: Date!
}

type Query {
    events(after: Date): [Event!]!
}
"""

# Resolver simple
class QueryResolvers:
    def __init__(self):
        print("✅ QueryResolvers created")
    
    def events(self, info: ResolverInfo):
        after = info.args.get('after')
        
        print(f"\n⚡ [RESOLVER] events() llamado")
        print(f"   [RESOLVER] after={after}")
        print(f"   [RESOLVER] Type of 'after': {type(after)}")
        print(f"   [RESOLVER] info.args completo: {info.args}")
        
        events = [
            {"id": "1", "name": "Event A", "date": datetime(2025, 11, 15)},
            {"id": "2", "name": "Event B", "date": datetime(2025, 11, 17)},
            {"id": "3", "name": "Event C", "date": datetime(2025, 11, 20)},
        ]
        
        if after:
            print(f"   [RESOLVER] Filtrando eventos después de: {after}")
            events = [e for e in events if e["date"] > after]
            print(f"   [RESOLVER] Eventos filtrados: {len(events)}")
        else:
            print(f"   [RESOLVER] Sin filtro (after=None), retornando todos")
        
        return events

if __name__ == "__main__":
    print("🚀 Iniciando servidor de prueba de scalars...\n")
    
    # Crear servidor
    server = HTTPServer(
        schema=schema,
        resolvers={"Query": QueryResolvers()}
    )
    
    # Registrar scalar
    print("📝 Registrando DateScalar...")
    server.scalar("Date", DateScalar())
    print("✅ DateScalar registrado\n")
    
    # Iniciar servidor
    print("🌐 Servidor corriendo en http://localhost:8000")
    print("📋 Probar con:")
    print('   curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d \'{"query":"{ events(after: \\"2025-11-16\\") { id name date } }"}\'')
    print()
    
    server.start(host="localhost", port=8000)
