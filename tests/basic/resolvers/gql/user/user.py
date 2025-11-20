from pgql import ResolverInfo

class User:
    def get_user(self, info: ResolverInfo):
        """Obtener un usuario por ID"""
        # Los argumentos vienen en info.args (en snake_case)
        user_id = info.args.get('user_id')
        
        print(f"🔍 get_user llamado con user_id={user_id}")
        print(f"   Operation: {info.operation}")
        print(f"   Type: {info.type_name}")
        print(f"   Session: {info.session_id}")
        print(f"   Parent: {info.parent}")
        
        return {
            'id': user_id or 1, 
            'name': 'John Doe', 
            'email': 'john@example.com'
        }
    
    def get_users(self, info: ResolverInfo):
        """Obtener todos los usuarios"""
        print(f"📋 get_users llamado")
        print(f"   Args recibidos: {info.args}")
        
        return [
            {'id': 1, 'name': 'Jose', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Mario', 'email': 'jane@example.com'}
        ]