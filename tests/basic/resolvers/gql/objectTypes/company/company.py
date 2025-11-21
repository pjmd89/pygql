from pgql import ResolverInfo

class Company:
    def company(self, info: ResolverInfo):
        """Resolver de relación User -> Company"""
        # Acceder al parent desde info
        parent = info.parent
        
        return {
            'id': parent.get('id') if isinstance(parent, dict) else parent['id'], 
            'name': 'Acme Corp', 
            'address': '123 Main St'
        }
    
    def get_company(self, info: ResolverInfo):
        """Obtener una compañía por ID"""
        company_id = info.args.get('company_id')
        
        return {
            'id': company_id or 1, 
            'name': 'Acme Corp', 
            'address': '123 Main St'
        }
    
    def get_companies(self, info: ResolverInfo):
        """Obtener todas las compañías"""
        return [
            {'id': 1, 'name': 'Acme Corp', 'address': '123 Main St'},
            {'id': 2, 'name': 'Globex Inc', 'address': '456 Elm St'}
        ]