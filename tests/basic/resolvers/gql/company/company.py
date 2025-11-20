class Company:
    def company(self, parent, info):
        return {'id': parent['id'], 'name': 'Acme Corp', 'address': '123 Main St'}
    
    def getCompany(self, parent, info):
        return {'id': 1, 'name': 'Acme Corp', 'address': '123 Main St'}
    
    def getCompanies(self, parent, info):
        return [
            {'id': 1, 'name': 'Acme Corp', 'address': '123 Main St'},
            {'id': 2, 'name': 'Globex Inc', 'address': '456 Elm St'}
        ]