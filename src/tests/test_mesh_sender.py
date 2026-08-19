import socket
import json
import uuid
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.network import IPv7Network
from config.constants import Config

# Inicializar componentes
network = IPv7Network()

print("--- INICIANDO INYECCIÓN DE PAQUETE FANTASMA (MESH) ---")

# Vamos a enviar un mensaje a un nodo que no existe en esta red
objetivo = "did:ipv7:LUNA"
mensaje = "Hola computadora en la luna, ¿me escuchas?"
payload_cifrado = network.cifrar_payload(mensaje)

paquete = {
    "id": uuid.uuid4().hex,
    "ttl": Config.DEFAULT_TTL,
    "tipo": "MENSAJE",
    "version": Config.EXPERIMENTAL_VERSION,
    "origen": "did:ipv7:INTRUSO", # Nodo falso
    "destino": objetivo,
    "longitud": len(payload_cifrado),
    "payload_cifrado": payload_cifrado
}

print(f"Lanzando paquete ciego hacia {objetivo} (TTL: {Config.DEFAULT_TTL})...")

network.enviar_broadcast(paquete)

print("¡Paquete fantasma inyectado con éxito al aire!")
print("Revisa la ventana negra de tu aplicación IPv7, debería haberlo atrapado y retransmitido.")
