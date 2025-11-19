class Company:
    @staticmethod
    def company(parent, info):
        return {'id': parent['id'], 'name': 'Acme Corp', 'address': '123 Main St'}
    @staticmethod
    def getCompany(parent, info):
        return {'id': 1, 'name': 'Acme Corp', 'address': '123 Main St'}
    @staticmethod
    def getCompanies(parent, info):
        return [
            {'id': 1, 'name': 'Acme Corp', 'address': '123 Main St'},
            {'id': 2, 'name': 'Globex Inc', 'address': '456 Elm St'}
        ]