"""
IPv7 Network Discovery
Handles node discovery via broadcast and directory management
"""

import socket
import json
import time
import sys
from typing import Optional, Dict

from src.config.constants import Config


class NetworkDiscovery:
    """Manages network node discovery and directory"""
    
    def __init__(self, network_manager):
        """
        Initialize discovery manager
        
        Args:
            network_manager: IPv7Network instance for communication
        """
        self.network = network_manager
        self.directorio = network_manager.directorio_local
    
    def broadcast_search(self, objetivo: str, timeout: float = None) -> Optional[str]:
        """
        Search for a node via broadcast
        
        Args:
            objetivo: DID of the node to find
            timeout: Search timeout in seconds (uses BROADCAST_TIMEOUT if None)
            
        Returns:
            IP address if found, None otherwise
        """
        # Check cache first
        if objetivo in self.directorio:
            return self.directorio[objetivo]
        
        # Send broadcast search
        paquete = {"tipo": "BUSQUEDA_BROADCAST", "objetivo": objetivo}
        self.network.enviar_broadcast(paquete)
        
        # Wait for response
        timeout = timeout or Config.BROADCAST_TIMEOUT
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            if objetivo in self.directorio:
                return self.directorio[objetivo]
            time.sleep(Config.DISCOVERY_DELAY)
        
        return None
    
    def multi_port_search(self, objetivo: str, timeout: float = None) -> Optional[str]:
        """
        Search for a node via broadcast on multiple ports
        
        Args:
            objetivo: DID of the node to find
            timeout: Search timeout in seconds (uses BROADCAST_TIMEOUT if None)
            
        Returns:
            IP address if found, None otherwise
        """
        if objetivo in self.directorio:
            return self.directorio[objetivo]
        
        paquete = {"tipo": "BUSQUEDA_BROADCAST", "objetivo": objetivo}
        self.network.enviar_multi_broadcast(paquete)
        
        timeout = timeout or Config.BROADCAST_TIMEOUT
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            if objetivo in self.directorio:
                return self.directorio[objetivo]
            time.sleep(Config.DISCOVERY_DELAY)
        
        return None
    
    def network_scan(self, timeout: float = None) -> Dict[str, str]:
        """
        Scan network for all active nodes
        
        Args:
            timeout: Scan timeout in seconds (uses SCAN_TIMEOUT if None)
            
        Returns:
            Dictionary of DID -> IP mappings
        """
        self.directorio.clear()
        
        paquete = {"tipo": "PING_GENERAL"}
        self.network.enviar_multi_broadcast(paquete)
        
        timeout = timeout or Config.SCAN_TIMEOUT
        time.sleep(timeout)
        
        return self.directorio.copy()
    
    def display_scan_results(self) -> None:
        """Display scan results in formatted output"""
        resultados = self.network_scan()
        
        sys.stdout.write("\n📡 Escaneando red local (espera 1 seg)...\n")
        sys.stdout.write("--- NODOS CONECTADOS ---\n")
        
        if not resultados:
            sys.stdout.write("Ningún otro nodo encontrado.\n")
        else:
            for did, ip in resultados.items():
                sys.stdout.write(f"- {did} (IP: {ip})\n")
        
        sys.stdout.write("------------------------\n\n")
        sys.stdout.flush()
    
    def handle_discovery_response(self, nombre: str, ip_origen: str) -> None:
        """
        Handle a discovery response from another node
        
        Args:
            nombre: DID of the responding node
            ip_origen: IP address of the responding node
        """
        self.directorio[nombre] = ip_origen