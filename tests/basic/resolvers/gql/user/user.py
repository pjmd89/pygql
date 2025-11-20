class User:
    def getUser(self, parent, info):
        return {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}
    
    def getUsers(self, parent, info):
        return [
            {'id': 1, 'name': 'Jose', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Mario', 'email': 'jane@example.com'}
        ]