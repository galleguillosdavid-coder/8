"""
IPv7 Session - Gestión de sesiones básica con PATH MTU
FASE 5: Session simple + MTU

⚠️ LEGACY (Fase 2 - Integración Core <-> MVP):
Este módulo queda deprecado. La implementación OFICIAL de Session y
SessionManager ahora vive en `src/core/session_manager.py` y es la que
usa `ipv7_mvp/node.py`. Este archivo se conserva temporalmente por
compatibilidad y para referencia histórica, pero no debe recibir
nuevas funcionalidades.
"""

import secrets
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class Session:
    """
    Sesión simple con ID aleatorio y PATH MTU
    """
    session_id: int
    remote_node_id: int
    channel: int
    path_mtu: Optional[int] = None  # MTU de la ruta (MIN de todos los saltos)
    path: List[dict] = None  # Ruta descubierta
    state: str = "open"  # open, closed
    
    def __post_init__(self):
        if self.path is None:
            self.path = []
    
    def close(self):
        """Cerrar sesión"""
        self.state = "closed"


class SessionManager:
    """
    Gestor de sesiones simple
    """
    
    def __init__(self):
        self.sessions: Dict[int, Session] = {}
    
    def create_session(self, remote_node_id: int, channel: int = 0, path_mtu: Optional[int] = None) -> Session:
        """Crear nueva sesión con ID aleatorio"""
        session_id = secrets.randbits(32)
        session = Session(session_id, remote_node_id, channel, path_mtu)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: int) -> Optional[Session]:
        """Obtener sesión por ID"""
        return self.sessions.get(session_id)
    
    def close_session(self, session_id: int) -> bool:
        """Cerrar sesión"""
        if session_id in self.sessions:
            self.sessions[session_id].close()
            del self.sessions[session_id]
            return True
        return False
    
    def update_session_mtu(self, session_id: int, new_mtu: Optional[int]) -> bool:
        """Actualizar MTU de una sesión (por cambio de ruta)"""
        session = self.get_session(session_id)
        if session:
            session.path_mtu = new_mtu
            return True
        return False