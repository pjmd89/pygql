"""
Test para verificar que las directivas funcionan tanto en:
1. FIELD_DEFINITION (en el schema)
2. FIELD (en la query)
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pgql import HTTPServer, Directive, ResolverInfo
import yaml

# Directiva de prueba
class UppercaseDirective(Directive):
    """Convierte texto a mayúsculas"""
    def invoke(self, args, type_name, field_name):
        mode = args.get('mode', 'upper')
        print(f"🔹 UppercaseDirective ejecutada con mode={mode}")
        return {'apply_uppercase': True, 'mode': mode}, None

class LogDirective(Directive):
    """Registra ejecución"""
    def invoke(self, args, type_name, field_name):
        message = args.get('message', 'default message')
        print(f"🔹 LogDirective ejecutada con message='{message}'")
        return {'logged': True, 'message': message}, None

# Schema con directivas
schema = """
directive @uppercase(mode: String) on FIELD_DEFINITION | FIELD
directive @log(message: String) on FIELD_DEFINITION | FIELD

type Query {
    # Directiva en SCHEMA (FIELD_DEFINITION)
    messageFromSchema: String @uppercase(mode: "schema")
    
    # Sin directiva en schema (se puede aplicar en query)
    messageFromQuery: String
    
    # Con directiva en schema pero puede sobrescribirse
    messageOverride: String @uppercase(mode: "schema")
}
"""

# Resolvers
class QueryResolvers:
    def message_from_schema(self, info: ResolverInfo):
        """Directiva aplicada desde el SCHEMA"""
        print(f"⚡ Resolver: message_from_schema")
        
        uppercase = info.directives.get('uppercase')
        text = "hello from schema"
        
        if uppercase:
            mode = uppercase.get('mode', 'upper')
            print(f"   Aplicando uppercase con mode={mode}")
            text = text.upper()
        
        return text
    
    def message_from_query(self, info: ResolverInfo):
        """Directiva aplicada desde la QUERY"""
        print(f"⚡ Resolver: message_from_query")
        
        uppercase = info.directives.get('uppercase')
        log = info.directives.get('log')
        
        text = "hello from query"
        
        if log:
            print(f"   Log: {log.get('message')}")
        
        if uppercase:
            mode = uppercase.get('mode', 'upper')
            print(f"   Aplicando uppercase con mode={mode}")
            text = text.upper()
        
        return text
    
    def message_override(self, info: ResolverInfo):
        """Directiva en schema pero sobrescrita por query"""
        print(f"⚡ Resolver: message_override")
        
        uppercase = info.directives.get('uppercase')
        text = "hello override"
        
        if uppercase:
            mode = uppercase.get('mode', 'unknown')
            print(f"   Aplicando uppercase con mode={mode}")
            text = text.upper()
        
        return text

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TEST: Directivas ON FIELD_DEFINITION y ON FIELD")
    print("="*70)
    
    # Crear config temporal
    import tempfile
    
    # Primero crear el schema en un archivo temporal
    schema_dir = tempfile.mkdtemp()
    schema_file = os.path.join(schema_dir, 'schema.gql')
    with open(schema_file, 'w') as f:
        f.write(schema)
    
    config_path = '/tmp/test_field_directives.yml'
    config = {
        'http_port': 8090,
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
    server.directive('uppercase', UppercaseDirective())
    server.directive('log', LogDirective())
    print("   ✅ Directivas registradas")
    
    # Registrar resolvers
    print("\n📋 Registrando resolvers...")
    server.gql({'Query': QueryResolvers()})
    
    print("\n" + "="*70)
    print("✅ Servidor listo en http://localhost:8090/graphql")
    print("="*70)
    
    print("\n💡 Tests a ejecutar:\n")
    
    print("1️⃣  Directiva desde SCHEMA (FIELD_DEFINITION):")
    print('   curl -X POST http://localhost:8090/graphql -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "{ messageFromSchema }"}\'')
    print("   Esperado: HELLO FROM SCHEMA (mode=schema desde schema)\n")
    
    print("2️⃣  Directiva desde QUERY (FIELD):")
    print('   curl -X POST http://localhost:8090/graphql -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "{ messageFromQuery @uppercase(mode: \\"query\\") }"}\'')
    print("   Esperado: HELLO FROM QUERY (mode=query desde query)\n")
    
    print("3️⃣  Múltiples directivas en QUERY:")
    print('   curl -X POST http://localhost:8090/graphql -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "{ messageFromQuery @log(message: \\"test\\") @uppercase(mode: \\"multi\\") }"}\'')
    print("   Esperado: HELLO FROM QUERY (con log + uppercase)\n")
    
    print("4️⃣  Sobrescribir directiva del SCHEMA:")
    print('   curl -X POST http://localhost:8090/graphql -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "{ messageOverride @uppercase(mode: \\"override\\") }"}\'')
    print("   Esperado: HELLO OVERRIDE (mode=override sobrescribe mode=schema)\n")
    
    print("="*70)
    print("🚀 Iniciando servidor...\n")
    
    server.start()
