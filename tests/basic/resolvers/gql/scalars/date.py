from pgql import Scalar, ScalarResolved
from datetime import datetime

class DateScalar(Scalar):
    def set(self, value):
        """
        Normaliza valores de OUTPUT (resolver → cliente)
        
        Args:
            value: Valor retornado por el resolver
            
        Returns:
            (valor_serializado, error)
        """
        # Manejar valores None
        if value is None:
            return None, None
        
        # Convertir datetime a string ISO format
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d"), None
        
        # Si ya es string, retornarlo
        return str(value), None
    
    def assess(self, resolved):
        """
        Valida y parsea valores de INPUT (cliente → resolver)
        
        Args:
            resolved: ScalarResolved con:
                - value: Valor de entrada desde GraphQL
                - resolver_name: Nombre del resolver
                - resolved: Objeto padre (si aplica)
                
        Returns:
            (valor_parseado, error)
        """
        # Manejar valores None
        if resolved.value is None:
            return None, None
        
        # Validar y parsear string a datetime
        try:
            if isinstance(resolved.value, str):
                parsed_date = datetime.strptime(resolved.value, "%Y-%m-%d")
                return parsed_date, None
            else:
                return None, ValueError(f"Expected string, got {type(resolved.value)}")
        except ValueError as e:
            return None, ValueError(f"Invalid date format: {resolved.value}")