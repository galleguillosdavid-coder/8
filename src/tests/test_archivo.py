import socket
import json
import threading
import sys
import time
import os
import base64

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.network import IPv7Network
from core.identity import IdentityManager
from core.discovery import NetworkDiscovery
from config.constants import Config

# Inicializar componentes
network = IPv7Network()
discovery = NetworkDiscovery(network)

# Importar del módulo refactorizado
sys.path.append(os.path.join(os.path.dirname(__file__), '../implementations'))
from ipv7_experimental import hilo_receptor

print("--- INICIANDO SIMULACIÓN DE TRANSFERENCIA DE ARCHIVOS ---")

# 1. Obtener la identidad real
mi_nombre = IdentityManager.get_or_create()
print(f"Identidad cargada: {mi_nombre}")

# 2. Iniciar el receptor silencioso (simulando que la app está abierta)
t = threading.Thread(target=hilo_receptor, args=(mi_nombre,), daemon=True)
t.start()

# 3. Crear un archivo de prueba
ruta_archivo = "archivo_prueba.txt"
with open(ruta_archivo, "w") as f:
    f.write("¡Este es un mensaje ultrasecreto enviado mediante el Protocolo de Blobs de IPv7!\nLa red P2P funciona perfecto.")
print(f"Archivo de prueba creado: {ruta_archivo}")

time.sleep(1) # Esperar a que el receptor levante

# 4. Simular el emisor buscando la IP
ip_destino = discovery.multi_port_search(mi_nombre)
print(f"Buscando IP destino... IP ENCONTRADA: {ip_destino}")

# 5. Enviar el archivo cifrado
print(f"Cifrando {ruta_archivo} y enviando a {ip_destino}...")
with open(ruta_archivo, "rb") as f:
    bytes_archivo = f.read()

b64_bytes = base64.b64encode(bytes_archivo)
payload_cifrado = network.cipher_suite.encrypt(b64_bytes).decode()

paquete = {
    "tipo": "ARCHIVO",
    "version": Config.EXPERIMENTAL_VERSION,
    "origen": mi_nombre,
    "destino": mi_nombre,
    "nombre_archivo": "archivo_prueba_ipv7.txt",
    "longitud": len(payload_cifrado),
    "payload_cifrado": payload_cifrado
}

network.enviar_udp(paquete, ip_destino)
print("¡Paquete disparado a la red!\n")

# Dar tiempo al receptor para que reciba, descifre y guarde
time.sleep(2)
print("\n--- SIMULACIÓN FINALIZADA ---")
