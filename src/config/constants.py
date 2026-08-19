"""
IPv7 Configuration Constants
Centralized configuration for all IPv7 components
"""

class Config:
    # Cifrado
    SHARED_KEY = b'cM3Zt-2_XjI2W8fXWJzM5Y8V1W-7Q_k5z3K_qD_G7c0='
    
    # Red
    DEFAULT_PORT = 7007
    TRACKER_PORT = 7000
    BROADCAST_IP = "255.255.255.255"
    LOCAL_PORTS = [7007, 7008, 7009, 7010]
    
    # Mesh
    DEFAULT_TTL = 3
    PACKET_HISTORY_SIZE = 1000
    MAX_FILE_SIZE = 40000  # 40KB
    
    # Timing
    BROADCAST_TIMEOUT = 2.0
    SCAN_TIMEOUT = 1.0
    DISCOVERY_ATTEMPTS = 10
    DISCOVERY_DELAY = 0.2
    
    # Protocolo
    PROTOCOL_VERSION = 7
    EXPERIMENTAL_VERSION = 8