from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthorizeInfo:
    """Información de autorización para interceptar resolvers
    
    Attributes:
        operation: Tipo de operación GraphQL ('query', 'mutation', 'subscription')
        src_type: Nombre del tipo GraphQL padre desde donde se invoca (ej: 'User' cuando se accede a User.company)
        dst_type: Nombre del tipo GraphQL siendo ejecutado (ej: 'Company' en User.company)
        resolver: Nombre del campo/resolver siendo ejecutado (ej: 'getUser', 'company')
        session_id: ID de sesión del usuario haciendo la consulta (obtenido de cookies)
    """
    operation: str
    src_type: Optional[str]
    dst_type: str
    resolver: str
    session_id: Optional[str] = None
