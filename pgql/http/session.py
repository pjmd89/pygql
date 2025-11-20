import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timedelta


class Session:
    """Representa una sesión individual con sus datos"""
    
    def __init__(self, session_id: str, max_age: int = 3600):
        self.session_id = session_id
        self.data: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.max_age = max_age  # segundos
        self.last_accessed = datetime.now()
    
    def is_expired(self) -> bool:
        """Verifica si la sesión ha expirado"""
        elapsed = (datetime.now() - self.last_accessed).total_seconds()
        return elapsed > self.max_age
    
    def touch(self):
        """Actualiza el tiempo de último acceso"""
        self.last_accessed = datetime.now()
    
    def set(self, key: str, value: Any):
        """Guarda un valor en la sesión"""
        self.data[key] = value
        self.touch()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de la sesión"""
        self.touch()
        return self.data.get(key, default)
    
    def delete(self, key: str):
        """Elimina un valor de la sesión"""
        if key in self.data:
            del self.data[key]
        self.touch()
    
    def clear(self):
        """Limpia todos los datos de la sesión"""
        self.data.clear()
        self.touch()


class SessionStore:
    """Almacén de sesiones en memoria"""
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
    
    def create(self, max_age: int = 3600) -> Session:
        """Crea una nueva sesión y retorna el objeto Session"""
        session_id = str(uuid.uuid4())
        session = Session(session_id, max_age)
        self._sessions[session_id] = session
        return session
    
    def get(self, session_id: str) -> Optional[Session]:
        """Obtiene una sesión existente o None si no existe o expiró"""
        if not session_id:
            return None
        
        session = self._sessions.get(session_id)
        
        if session is None:
            return None
        
        # Verificar si expiró
        if session.is_expired():
            self.delete(session_id)
            return None
        
        session.touch()
        return session
    
    def delete(self, session_id: str):
        """Elimina una sesión"""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def cleanup_expired(self):
        """Limpia sesiones expiradas (puede llamarse periódicamente)"""
        expired_ids = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]
        for sid in expired_ids:
            del self._sessions[sid]
    
    def count(self) -> int:
        """Retorna el número de sesiones activas"""
        return len(self._sessions)
