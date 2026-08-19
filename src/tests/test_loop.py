import socket
import json
import threading
import sys
import time
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.network import IPv7Network
from core.discovery import NetworkDiscovery
from config.constants import Config

# Inicializar componentes
network = IPv7Network()
discovery = NetworkDiscovery(network)

# Importar del módulo refactorizado
sys.path.append(os.path.join(os.path.dirname(__file__), '../implementations'))
from ipv7_autonomo import hilo_receptor

mi_nombre = "did:ipv7:LOCAL"
t = threading.Thread(target=hilo_receptor, args=(mi_nombre,), daemon=True)
t.start()

time.sleep(1) # Esperar a que el hilo levante el socket
ip_destino = discovery.broadcast_search(mi_nombre)
print(f"IP DESTINO ENCONTRADA: {ip_destino}")

mensaje = "hola"
payload_cifrado = network.cifrar_payload(mensaje)
paquete = network.crear_paquete("MENSAJE", mi_nombre, mi_nombre, payload_cifrado)

network.enviar_udp(paquete, ip_destino)
print("PAQUETE ENVIADO.")

time.sleep(2)
print("FIN.")
