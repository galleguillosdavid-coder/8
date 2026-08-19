"""
IPv7 Packet - Estructura básica de paquete
FASE 1: Comunicación mínima + SHA-256
"""

import struct
import hashlib
import hmac
from dataclasses import dataclass
from typing import Optional


@dataclass
class IPv7Packet:
    """
    Paquete IPv7 básico con SHA-256
    Mantener simple: HEADER + PAYLOAD + SHA-256
    """
    version: int = 1
    source_id: int = 0
    dest_id: int = 0
    channel: int = 0  # Subport lógico
    session_id: int = 0
    payload: bytes = b''
    checksum: bytes = b''  # SHA-256 (32 bytes)
    
    HEADER_FORMAT = '!BBIIII'  # version, flags, source, dest, channel, session
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    CHECKSUM_SIZE = 32  # SHA-256 = 32 bytes
    
    def integrity_data(self) -> bytes:
        """
        Datos protegidos por SHA-256.

        Incluye los campos de header que deben permanecer inalterables
        durante el tránsito (versión, flags, source_id, dest_id,
        channel, session_id) seguidos del payload/contenedor.

        No incluye el propio campo SHA-256 (checksum) ni campos que
        puedan modificarse legítimamente en la red.
        """
        header = struct.pack(
            self.HEADER_FORMAT,
            self.version,
            0,  # flags (reservado)
            self.source_id,
            self.dest_id,
            self.channel,
            self.session_id
        )
        return header + self.payload
    
    def calculate_checksum(self) -> bytes:
        """Calcular SHA-256 de los datos a proteger"""
        return hashlib.sha256(self.integrity_data()).digest()
    
    def encode(self) -> bytes:
        """Codificar paquete a bytes con SHA-256"""
        # Calcular checksum
        self.checksum = self.calculate_checksum()
        
        header = struct.pack(
            self.HEADER_FORMAT,
            self.version,
            0,  # flags (reservado)
            self.source_id,
            self.dest_id,
            self.channel,
            self.session_id
        )
        return header + self.payload + self.checksum
    
    @classmethod
    def decode(cls, data: bytes) -> Optional['IPv7Packet']:
        """Decodificar bytes a paquete"""
        if len(data) < cls.HEADER_SIZE + cls.CHECKSUM_SIZE:
            return None
        
        # Extraer header
        header_data = struct.unpack(cls.HEADER_FORMAT, data[:cls.HEADER_SIZE])
        
        # Extraer payload (sin checksum)
        payload_end = len(data) - cls.CHECKSUM_SIZE
        payload = data[cls.HEADER_SIZE:payload_end]
        
        # Extraer checksum recibido
        received_checksum = data[payload_end:]
        
        packet = cls(
            version=header_data[0],
            source_id=header_data[2],
            dest_id=header_data[3],
            channel=header_data[4],
            session_id=header_data[5],
            payload=payload,
            checksum=received_checksum
        )
        
        return packet
    
    def verify_checksum(self) -> bool:
        """Verificar que el SHA-256 sea correcto"""
        expected = self.calculate_checksum()
        return hmac.compare_digest(self.checksum, expected)


# Tipos de mensajes básicos para FASE 1
class MessageType:
    HELLO = 1
    PING = 2
    PONG = 3
    DATA = 4
    DISCOVER = 5
    HERE = 6
    PATH_DISCOVER = 7
    PATH_RESPONSE = 8
    PATH_CHANGED = 9