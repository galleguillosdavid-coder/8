"""
IPv7 Network Management
Handles encryption, packet creation, and UDP communication
"""

import socket
import json
from cryptography.fernet import Fernet
from typing import Dict, Any, Optional
from collections import deque

from src.config.constants import Config


class IPv7Network:
    """Core network functionality for IPv7"""
    
    def __init__(self, shared_key: bytes = None):
        """
        Initialize network manager
        
        Args:
            shared_key: Optional custom encryption key (uses default if None)
        """
        self.cipher_suite = Fernet(shared_key or Config.SHARED_KEY)
        self.directorio_local = {}
        self.historial_paquetes = deque(maxlen=Config.PACKET_HISTORY_SIZE)
        self.puentes_globales = set()
        
    def cifrar_payload(self, data: str) -> str:
        """Encrypt data using AES-256 (Fernet)"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def descifrar_payload(self, encrypted: str) -> str:
        """Decrypt encrypted data"""
        return self.cipher_suite.decrypt(encrypted.encode()).decode()
    
    def crear_paquete(self, tipo: str, origen: str, destino: str, 
                     payload: str, **kwargs) -> Dict[str, Any]:
        """
        Create a standardized IPv7 packet
        
        Args:
            tipo: Packet type (MENSAJE, ARCHIVO, BUSQUEDA_BROADCAST, etc.)
            origen: Source DID
            destino: Destination DID
            payload: Encrypted payload
            **kwargs: Additional packet fields
            
        Returns:
            Dictionary representing the packet
        """
        paquete = {
            "tipo": tipo,
            "version": Config.PROTOCOL_VERSION,
            "origen": origen,
            "destino": destino,
            "longitud": len(payload),
            "payload_cifrado": payload,
            **kwargs
        }
        return paquete
    
    def enviar_udp(self, paquete: Dict[str, Any], ip_destino: str, 
                  puerto: int = None) -> None:
        """
        Send packet via UDP
        
        Args:
            paquete: Packet dictionary to send
            ip_destino: Destination IP address
            puerto: Destination port (uses default if None)
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(json.dumps(paquete).encode("utf-8"), 
                    (ip_destino, puerto or Config.DEFAULT_PORT))
        sock.close()
    
    def enviar_broadcast(self, paquete: Dict[str, Any], 
                        puerto: int = None) -> None:
        """
        Send packet via broadcast to local network
        
        Args:
            paquete: Packet dictionary to send
            puerto: Destination port (uses default if None)
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(json.dumps(paquete).encode("utf-8"), 
                    (Config.BROADCAST_IP, puerto or Config.DEFAULT_PORT))
        sock.close()
    
    def enviar_multi_broadcast(self, paquete: Dict[str, Any], 
                              puertos: list = None) -> None:
        """
        Send packet via broadcast to multiple ports
        
        Args:
            paquete: Packet dictionary to send
            puertos: List of ports to send to (uses LOCAL_PORTS if None)
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        for puerto in (puertos or Config.LOCAL_PORTS):
            sock.sendto(json.dumps(paquete).encode("utf-8"), 
                        (Config.BROADCAST_IP, puerto))
        
        sock.close()
    
    def agregar_paquete_historial(self, paquete_id: str) -> bool:
        """
        Add packet to history to prevent retransmission loops
        
        Args:
            paquete_id: Unique packet identifier
            
        Returns:
            True if packet was new, False if already in history
        """
        if paquete_id in self.historial_paquetes:
            return False
        
        self.historial_paquetes.append(paquete_id)
        return True
    
    def procesar_mesh_retransmision(self, paquete: Dict[str, Any], 
                                   mi_nombre: str) -> bool:
        """
        Process mesh retransmission logic
        
        Args:
            paquete: Packet to potentially retransmit
            mi_nombre: Current node's DID
            
        Returns:
            True if packet was retransmitted, False otherwise
        """
        paquete_id = paquete.get("id")
        if not paquete_id:
            return False
        
        # Check if already processed
        if not self.agregar_paquete_historial(paquete_id):
            return False
        
        # Check if should retransmit
        destino = paquete.get("destino")
        tipo = paquete.get("tipo")
        
        if destino and destino != mi_nombre and tipo in ["MENSAJE", "ARCHIVO"]:
            ttl = paquete.get("ttl", 0)
            if ttl > 0:
                paquete["ttl"] = ttl - 1
                return True
        
        return False