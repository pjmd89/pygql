class User:
    def get_user(self, parent, info):
        return {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}
    
    def get_users(self, parent, info):
        return [
            {'id': 1, 'name': 'Jose', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Mario', 'email': 'jane@example.com'}
        ]