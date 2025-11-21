from pgql import ResolverInfo, ErrorDescriptor, LEVEL_FATAL, new_error, new_fatal
from datetime import datetime

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
        
        # Validar edad mínima (age viene como datetime de fecha de nacimiento)
        birth_date = user_input.get('age')  # Es un datetime object
        
        if birth_date:
            # Calcular edad actual
            today = datetime.now()
            age_years = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            print(f"📅 Fecha de nacimiento: {birth_date.strftime('%Y-%m-%d')}")
            print(f"📊 Edad calculada: {age_years} años")
            
            if age_years < 30:
                # Opción 1: Con ErrorDescriptor + extensions (recomendado)
                error_descriptor = ErrorDescriptor(
                    message="User must be at least 30 years old",
                    code="AGE_VALIDATION_FAILED",
                    level=LEVEL_FATAL
                )
                
                extensions = {
                    'field': 'age',
                    'minimumAge': 30,
                    'providedAge': age_years,
                    'birthDate': birth_date.strftime('%Y-%m-%d')
                }
                
                raise new_error(err=error_descriptor)
                
                # Opción 2: Solo con mensaje (más simple, sin código)
                # raise new_fatal(
                #     message="User must be at least 30 years old",
                #     extensions={'field': 'age', 'minimumAge': 30}
                # )
                
                # Opción 3: Con mensaje, código y level personalizado
                # raise new_error(
                #     message="User must be at least 30 years old",
                #     code="AGE_VALIDATION_FAILED",
                #     level=LEVEL_FATAL,
                #     extensions={'field': 'age', 'minimumAge': 30}
                # )
        
        # Aquí normalmente guardarías el usuario en la base de datos
        new_user = {
            'id': 3,  # Simulando un nuevo ID
            'name': user_input['name'],
            'age': user_input['age'],
            'email': user_input['email']
        }
        
        return new_user