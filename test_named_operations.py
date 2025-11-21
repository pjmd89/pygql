"""
Test para verificar que las directivas funcionan con:
1. Queries inline: { field @directive }
2. Named operations: query Name { field @directive }
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pgql import HTTPServer, Directive, ResolverInfo
import yaml

# Directiva de paginación
class PaginateDirective(Directive):
    """Directiva de paginación"""
    def invoke(self, args, type_name, field_name):
        page = args.get('page', 1)
        split = args.get('split', 10)
        
        paginate_data = {
            'page': page,
            'split': split,
            'skip': (page - 1) * split,
            'limit': split
        }
        
        print(f"🔹 PaginateDirective: page={page}, split={split}")
        return paginate_data, None

# Schema
schema = """
directive @paginate(page: Int, split: Int) on FIELD_DEFINITION | FIELD

type LeadSource {
    id: ID!
    name: String!
    description: String
}

type Query {
    # Field sin directiva en schema
    getLeadSources: [LeadSource!]!
    
    # Field con directiva en schema
    getAllLeadSources: [LeadSource!]! @paginate(page: 1, split: 5)
}
"""

# Resolvers
class QueryResolvers:
    def __init__(self):
        # Datos de prueba
        self.lead_sources = [
            {"id": str(i), "name": f"Lead Source {i}", "description": f"Description {i}"}
            for i in range(1, 21)
        ]
    
    def get_lead_sources(self, info: ResolverInfo):
        """Query sin directiva en schema (se aplica desde query)"""
        print(f"⚡ Resolver: get_lead_sources")
        
        paginate = info.directives.get('paginate')
        
        if paginate:
            skip = paginate['skip']
            limit = paginate['limit']
            print(f"   Paginando: skip={skip}, limit={limit}")
            return self.lead_sources[skip:skip + limit]
        else:
            print(f"   Sin paginación, retornando todos ({len(self.lead_sources)})")
            return self.lead_sources
    
    def get_all_lead_sources(self, info: ResolverInfo):
        """Query con directiva en schema"""
        print(f"⚡ Resolver: get_all_lead_sources")
        
        paginate = info.directives.get('paginate')
        
        if paginate:
            skip = paginate['skip']
            limit = paginate['limit']
            print(f"   Paginando: skip={skip}, limit={limit}")
            return self.lead_sources[skip:skip + limit]
        else:
            print(f"   Sin paginación, retornando todos ({len(self.lead_sources)})")
            return self.lead_sources

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TEST: Named Operations con Directivas")
    print("="*70)
    
    # Crear config temporal
    import tempfile
    
    schema_dir = tempfile.mkdtemp()
    schema_file = os.path.join(schema_dir, 'schema.gql')
    with open(schema_file, 'w') as f:
        f.write(schema)
    
    config_path = '/tmp/test_named_operations.yml'
    config = {
        'http_port': 8091,
        'debug': True,
        'server': {
            'host': 'localhost',
            'routes': [{
                'mode': 'gql',
                'endpoint': '/graphql',
                'schema': schema_dir
            }]
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Crear servidor
    server = HTTPServer(config_path)
    
    # Registrar directivas
    print("\n📋 Registrando directivas...")
    server.directive('paginate', PaginateDirective())
    print("   ✅ Directiva 'paginate' registrada")
    
    # Registrar resolvers
    print("\n📋 Registrando resolvers...")
    server.gql({'Query': QueryResolvers()})
    
    print("\n" + "="*70)
    print("✅ Servidor listo en http://localhost:8091/graphql")
    print("="*70)
    
    print("\n💡 Tests a ejecutar:\n")
    
    print("1️⃣  Query inline con directiva:")
    print('   curl -X POST http://localhost:8091/graphql -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "{ getLeadSources @paginate(page: 2, split: 3) { id name } }"}\'')
    print("   Esperado: 3 items (Lead Source 4, 5, 6)\n")
    
    print("2️⃣  Named operation con directiva:")
    print('   curl -X POST http://localhost:8091/graphql -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "query getAllLeadSource { getLeadSources @paginate(page: 2, split: 3) { id name } }"}\'')
    print("   Esperado: 3 items (Lead Source 4, 5, 6)\n")
    
    print("3️⃣  Named operation SIN paréntesis:")
    print('   curl -X POST http://localhost:8091/graphql -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "query getAllLeadSource { getLeadSources @paginate { id name } }"}\'')
    print("   Esperado: 10 items (default: page=1, split=10)\n")
    
    print("4️⃣  Directiva en schema con named operation:")
    print('   curl -X POST http://localhost:8091/graphql -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "query GetAll { getAllLeadSources { id name } }"}\'')
    print("   Esperado: 5 items (directiva del schema: page=1, split=5)\n")
    
    print("5️⃣  Sobrescribir directiva del schema con named operation:")
    print('   curl -X POST http://localhost:8091/graphql -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "query GetAll { getAllLeadSources @paginate(page: 3, split: 2) { id name } }"}\'')
    print("   Esperado: 2 items (Lead Source 5, 6)\n")
    
    print("="*70)
    print("🚀 Iniciando servidor...\n")
    
    server.start()
