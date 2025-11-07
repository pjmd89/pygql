class User:
    @staticmethod
    def getUser(parent, info):
        return {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'}
    @staticmethod
    def getUsers(parent, info):
        return [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane Doe', 'email': 'jane@example.com'}
        ]