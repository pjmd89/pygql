"""
Ejemplo completo de uso de directivas con servidor HTTP
"""
from pgql import HTTPServer, Directive, ResolverInfo


# ===== DIRECTIVAS =====

class PaginateDirective(Directive):
    """Directiva de paginación (como tu ejemplo de Go)"""
    
    def invoke(self, args, type_name, field_name):
        page = self._parse_int(args.get('page'), default=1)
        split = self._parse_int(args.get('split'), default=10)
        
        page = max(1, page)
        split = max(1, split)
        
        print(f"   📄 @paginate ejecutada: page={page}, split={split}")
        
        return {
            'page': page,
            'split': split,
            'skip': (page - 1) * split,
            'limit': split
        }, None
    
    @staticmethod
    def _parse_int(value, default=0):
        if value is None:
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default


class UppercaseDirective(Directive):
    """Directiva simple que marca para uppercase"""
    
    def invoke(self, args, type_name, field_name):
        print(f"   🔤 @uppercase ejecutada en {type_name}.{field_name}")
        return {'apply_uppercase': True}, None


# ===== RESOLVERS =====

class Query:
    def __init__(self):
        # Datos de ejemplo
        self.all_users_data = [
            {'id': '1', 'name': 'Alice', 'email': 'alice@example.com'},
            {'id': '2', 'name': 'Bob', 'email': 'bob@example.com'},
            {'id': '3', 'name': 'Charlie', 'email': 'charlie@example.com'},
            {'id': '4', 'name': 'Diana', 'email': 'diana@example.com'},
            {'id': '5', 'name': 'Eve', 'email': 'eve@example.com'},
            {'id': '6', 'name': 'Frank', 'email': 'frank@example.com'},
            {'id': '7', 'name': 'Grace', 'email': 'grace@example.com'},
            {'id': '8', 'name': 'Henry', 'email': 'henry@example.com'},
        ]
    
    def users(self, info: ResolverInfo):
        """
        Resolver que usa directiva @paginate
        
        La directiva se ejecuta ANTES de este método.
        Los resultados están disponibles en info.directives
        """
        print(f"\n⚡ Ejecutando Query.users")
        print(f"   Args: {info.args}")
        
        # Obtener datos de paginación de la directiva
        paginate = info.directives.get('paginate')
        
        if paginate:
            print(f"   Usando paginación: skip={paginate['skip']}, limit={paginate['limit']}")
            skip = paginate['skip']
            limit = paginate['limit']
            
            # Aplicar paginación
            paginated_users = self.all_users_data[skip:skip + limit]
            
            return {
                'data': paginated_users,
                'page': paginate['page'],
                'total': len(self.all_users_data)
            }
        else:
            print("   Sin paginación")
            return {
                'data': self.all_users_data,
                'page': 1,
                'total': len(self.all_users_data)
            }
    
    def all_users(self, info: ResolverInfo):
        """Resolver sin directivas"""
        print(f"\n⚡ Ejecutando Query.all_users (sin directivas)")
        return self.all_users_data
    
    def message(self, info: ResolverInfo):
        """Resolver que usa directiva @uppercase"""
        print(f"\n⚡ Ejecutando Query.message")
        
        # Obtener info de la directiva
        uppercase = info.directives.get('uppercase')
        
        text = "hello world"
        
        if uppercase and uppercase.get('apply_uppercase'):
            print(f"   Aplicando uppercase por directiva")
            text = text.upper()
        
        return text


# ===== SERVIDOR =====

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 SERVIDOR CON DIRECTIVAS")
    print("="*60)
    
    # Crear configuración temporal con path correcto
    import os
    import yaml
    
    config_path = 'etc/http_directives.yml'
    os.makedirs('etc', exist_ok=True)
    
    config = {
        'http_port': 8080,
        'https_port': 8443,
        'cookie_name': 'session_id',
        'debug': True,
        'server': {
            'host': 'localhost',
            'routes': [
                {
                    'mode': 'gql',
                    'endpoint': '/graphql',
                    'schema': 'schema_directives'  # ⬅️ Usar schema_directives
                }
            ]
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Crear servidor
    server = HTTPServer(config_path)
    
    # Registrar directivas ANTES de gql()
    print("\n📋 Registrando directivas...")
    server.directive('paginate', PaginateDirective())
    server.directive('uppercase', UppercaseDirective())
    print("   ✅ Directiva 'paginate' registrada")
    print("   ✅ Directiva 'uppercase' registrada")
    
    # Registrar resolvers
    print("\n📋 Registrando resolvers...")
    server.gql({
        'Query': Query()
    })
    
    print("\n" + "="*60)
    print("✅ Servidor listo en http://localhost:8080/graphql")
    print("="*60)
    print("\n💡 Ejemplos de queries:")
    print("\n1. Con paginación:")
    print("""   {
     users(page: 2, split: 3) {
       data { id name }
       page
       total
     }
   }""")
    
    print("\n2. Sin directivas:")
    print("""   {
     allUsers { id name }
   }""")
    
    print("\n3. Con uppercase:")
    print("""   {
     message
   }""")
    
    print()
    
    server.start()
