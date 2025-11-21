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
            'age': 30,
            'email': 'john@example.com'
        }
    
    def get_users(self, info: ResolverInfo):
        """Obtener todos los usuarios"""
        print(f"📋 get_users llamado")
        print(f"   Args recibidos: {info.args}")
        
        return [
            {'id': 1, 'name': 'Jose','age': 30, 'email': 'john@example.com'},
            {'id': 2, 'name': 'Mario', 'age': 25, 'email': 'jane@example.com'}
        ]
    def create_user(self, info: ResolverInfo):
        """Crear un nuevo usuario"""
        user_input = info.args.get('input')
        
        print(f"➕ create_user llamado con input={user_input}")
        
        # Aquí normalmente guardarías el usuario en la base de datos
        new_user = {
            'id': 3,  # Simulando un nuevo ID
            'name': user_input['name'],
            'age': user_input['age'],
            'email': user_input['email']
        }
        
        return new_user