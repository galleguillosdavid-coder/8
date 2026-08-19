"""
IPv7 Session Manager
Gestión de sesiones como contexto de comunicación
Una sesión identifica una comunicación concreta, no un servicio

NOTA DE INTEGRACIÓN (Fase 2 - Core <-> MVP):
Esta es la implementación OFICIAL de Session/SessionManager para todo IPv7.
`ipv7_mvp/session.py` queda marcado como LEGACY (no se elimina todavía,
pero el MVP ya no debe usarlo). Los campos `path_mtu`, `remote_node_id`
y `channel` se incorporaron aquí porque el MVP los necesitaba y el
Core original no los tenía.

`session_id` es un entero de 32 bits (no un string) para poder viajar
dentro del campo `session_id` del header de `IPv7Packet` (formato `!I`).
"""

from typing import Dict, Optional, Set, List
import time
import secrets


class Session:
    """Representación de una sesión de comunicación"""
    
    def __init__(self, session_id: int, remote_node_id: Optional[int] = None,
                 channel: int = 0, path_mtu: Optional[int] = None,
                 participants: Optional[Set[str]] = None):
        self.session_id = session_id
        self.remote_node_id = remote_node_id  # Nodo remoto (MVP, sin DID todavía)
        self.channel = channel  # Canal lógico principal de esta sesión
        self.path_mtu: Optional[int] = path_mtu  # None = no descubierto / invalidado
        self.path: List[dict] = []  # Ruta descubierta (PATH_DISCOVER/RESPONSE)
        self.participants = participants or set()  # Set de DIDs (Identity, fase futura)
        self.created_at = time.time()
        self.last_activity = time.time()
        self.channels: Set[int] = {channel} if channel is not None else set()  # Canales asociados
        self.containers: Dict[str, dict] = {}  # Contenedores lógicos
        self.state = "active"
        self.metadata: Dict = {}
    
    def add_channel(self, channel_id: int):
        """Asociar canal a la sesión"""
        self.channels.add(channel_id)
        self.update_activity()
    
    def update_path_mtu(self, new_mtu: Optional[int]):
        """
        Actualizar PATH_MTU de la sesión.
        None significa "todavía no conocido" o "invalidado" (ej. PATH_CHANGED).
        """
        self.path_mtu = new_mtu
        self.update_activity()
    
    def remove_channel(self, channel_id: int):
        """Desasociar canal de la sesión"""
        self.channels.discard(channel_id)
        self.update_activity()
    
    def add_container(self, container_id: str, container_data: dict):
        """Agregar contenedor lógico a la sesión"""
        self.containers[container_id] = container_data
        self.update_activity()
    
    def update_activity(self):
        """Actualizar timestamp de última actividad"""
        self.last_activity = time.time()
    
    def close(self, reason: str = "normal"):
        """Cerrar la sesión"""
        self.state = f"closed_{reason}"


class SessionManager:
    """
    Gestor de sesiones del Core
    Una sesión agrupa canales y contenedores para un contexto específico
    """
    
    def __init__(self):
        self.sessions: Dict[int, Session] = {}
    
    def create_session(self, remote_node_id: Optional[int] = None, channel: int = 0,
                        path_mtu: Optional[int] = None,
                        participants: Optional[Set[str]] = None,
                        metadata: Dict = None) -> Session:
        """
        Crear nueva sesión con ID aleatorio de 32 bits (compatible con el
        campo session_id del header de IPv7Packet).
        
        Args:
            remote_node_id: node_id del nodo remoto (MVP, sin DID todavía)
            channel: canal lógico principal de la sesión
            path_mtu: PATH_MTU inicial (None = todavía no descubierto)
            participants: Set de DIDs participantes (Identity, fase futura)
            metadata: Metadata opcional de la sesión
            
        Returns:
            Session object
        """
        session_id = secrets.randbits(32)
        while session_id in self.sessions:
            session_id = secrets.randbits(32)
        
        session = Session(session_id, remote_node_id, channel, path_mtu, participants)
        session.metadata = metadata or {}
        self.sessions[session_id] = session
        
        return session
    
    def get_session(self, session_id: int) -> Optional[Session]:
        """Obtener sesión por ID"""
        return self.sessions.get(session_id)
    
    def close_session(self, session_id: int, reason: str = "normal") -> bool:
        """Cerrar sesión existente"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id].close(reason)
        del self.sessions[session_id]
        return True
    
    def update_session_mtu(self, session_id: int, new_mtu: Optional[int]) -> bool:
        """
        Actualizar PATH_MTU de una sesión (compatibilidad con la API que
        usaba ipv7_mvp/session.py).
        """
        session = self.get_session(session_id)
        if session:
            session.update_path_mtu(new_mtu)
            return True
        return False
    
    def get_sessions_for_remote_node(self, remote_node_id: int) -> List[Session]:
        """Obtener sesiones asociadas a un node_id remoto (uso MVP)"""
        return [s for s in self.sessions.values() if s.remote_node_id == remote_node_id]
    
    def get_sessions_for_participant(self, did: str) -> Set[int]:
        """Obtener todas las sesiones donde participa un DID"""
        session_ids = set()
        for session_id, session in self.sessions.items():
            if did in session.participants:
                session_ids.add(session_id)
        return session_ids
    
    def cleanup_inactive_sessions(self, timeout_seconds: int = 7200):
        """Limpiar sesiones inactivas (2 horas default)"""
        current_time = time.time()
        inactive_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_activity > timeout_seconds:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            self.close_session(session_id, "timeout")
        
        return len(inactive_sessions)