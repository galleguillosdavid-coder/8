"""
IPv7 Channel Manager
Gestión de canales dinámicos como primitiva del Core
El Core sabe que existe un canal QUERY, pero no qué significa
"""

from typing import Dict, Optional, Set
from enum import IntEnum
import time


class ChannelType(IntEnum):
    """Tipos de canales predefinidos (subports)"""
    CONTROL = 0x00
    TELEMETRY = 0x01
    QUERY = 0x02
    WRITE = 0x03
    EMERGENCY = 0x04
    # 0x05-0x63: Reservado
    # 0x64+: Para Profiles


class Channel:
    """Representación de un canal de comunicación"""
    
    def __init__(self, channel_id: int, profile: str, capabilities: Dict):
        self.channel_id = channel_id
        self.profile = profile
        self.capabilities = capabilities
        self.created_at = time.time()
        self.last_activity = time.time()
        self.state = "open"
    
    def update_activity(self):
        """Actualizar timestamp de última actividad"""
        self.last_activity = time.time()
    
    def close(self, reason: str = "normal"):
        """Cerrar el canal"""
        self.state = f"closed_{reason}"


class ChannelManager:
    """
    Gestor de canales dinámicos del Core
    El Core transporta estructura, no semántica
    """
    
    def __init__(self):
        self.channels: Dict[int, Channel] = {}
        self.channel_counter = 0x64  # Empezar después de canales predefinidos
        self.predefined_channels = {
            ChannelType.CONTROL: {"name": "control", "description": "Control messages"},
            ChannelType.TELEMETRY: {"name": "telemetry", "description": "Telemetry data"},
            ChannelType.QUERY: {"name": "query", "description": "Query requests"},
            ChannelType.WRITE: {"name": "write", "description": "Write operations"},
            ChannelType.EMERGENCY: {"name": "emergency", "description": "Emergency messages"}
        }
    
    def create_channel(self, channel_id: Optional[int] = None, 
                      profile: str = "default", 
                      capabilities: Dict = None) -> Channel:
        """
        Crear canal dinámico durante handshake
        
        OPEN CHANNEL
            channel_id = 0x82A71F03
            profile = sensor_profile
            capabilities = {"telemetry": True, "query": True}
        """
        if channel_id is None:
            channel_id = self._generate_channel_id()
        
        if channel_id in self.channels:
            raise ValueError(f"Channel {channel_id} already exists")
        
        capabilities = capabilities or {}
        channel = Channel(channel_id, profile, capabilities)
        self.channels[channel_id] = channel
        
        return channel
    
    def close_channel(self, channel_id: int, reason: str = "normal") -> bool:
        """
        Cerrar canal existente
        
        CLOSE CHANNEL
            channel_id = 0x82A71F03
            reason = normal_shutdown
        """
        if channel_id not in self.channels:
            return False
        
        self.channels[channel_id].close(reason)
        del self.channels[channel_id]
        return True
    
    def get_channel(self, channel_id: int) -> Optional[Channel]:
        """Obtener canal por ID"""
        return self.channels.get(channel_id)
    
    def is_predefined_channel(self, channel_id: int) -> bool:
        """Verificar si es un canal predefinido"""
        return channel_id in self.predefined_channels
    
    def get_predefined_channel_info(self, channel_id: int) -> Optional[Dict]:
        """Obtener información de canal predefinido"""
        return self.predefined_channels.get(channel_id)
    
    def _generate_channel_id(self) -> int:
        """Generar ID único de canal (32-bit)"""
        while True:
            channel_id = self.channel_counter
            self.channel_counter += 1
            
            # Evitar colisiones con canales predefinidos
            if channel_id > 0x63 and channel_id not in self.channels:
                return channel_id
            
            # Wrap around si necesario (raro en práctica)
            if self.channel_counter >= 0xFFFFFFFF:
                self.channel_counter = 0x64
    
    def get_active_channels(self) -> Set[int]:
        """Obtener conjunto de canales activos"""
        return set(self.channels.keys())
    
    def cleanup_inactive_channels(self, timeout_seconds: int = 3600):
        """Limpiar canales inactivos"""
        current_time = time.time()
        inactive_channels = []
        
        for channel_id, channel in self.channels.items():
            if current_time - channel.last_activity > timeout_seconds:
                inactive_channels.append(channel_id)
        
        for channel_id in inactive_channels:
            self.close_channel(channel_id, "timeout")
        
        return len(inactive_channels)