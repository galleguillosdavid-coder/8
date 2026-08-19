import subprocess
import time
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.constants import Config

print("--- INICIANDO ENJAMBRE DE PRUEBA (3 NODOS) ---")

os.environ["PYTHONUNBUFFERED"] = "1"

for p in Config.LOCAL_PORTS[:3]:  # Solo los primeros 3 puertos
    f = f"ipv7_identidad_{p}.json"
    if os.path.exists(f):
        os.remove(f)

p1 = subprocess.Popen(["python", "-X", "utf8", "ipv7_experimental.py"], stdin=subprocess.PIPE, stdout=open("out1.txt", "w", encoding="utf-8"), stderr=subprocess.STDOUT, cwd="../implementations")
p2 = subprocess.Popen(["python", "-X", "utf8", "ipv7_experimental.py"], stdin=subprocess.PIPE, stdout=open("out2.txt", "w", encoding="utf-8"), stderr=subprocess.STDOUT, cwd="../implementations")
p3 = subprocess.Popen(["python", "-X", "utf8", "ipv7_experimental.py"], stdin=subprocess.PIPE, stdout=open("out3.txt", "w", encoding="utf-8"), stderr=subprocess.STDOUT, cwd="../implementations")
time.sleep(3)

print("¡Enjambre listo! Inyectando paquete ciego hacia 'LUNA' en los 3 puertos...")
inject_script = f"""
import socket, json, uuid
from cryptography.fernet import Fernet
c = Fernet(b'{Config.SHARED_KEY.decode()}')
paquete = {{
    "id": uuid.uuid4().hex,
    "ttl": {Config.DEFAULT_TTL},
    "tipo": "MENSAJE",
    "version": {Config.EXPERIMENTAL_VERSION},
    "origen": "did:ipv7:INTRUSO",
    "destino": "did:ipv7:LUNA",
    "longitud": 100,
    "payload_cifrado": c.encrypt(b"Hola").decode()
}}
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
for p in [{Config.LOCAL_PORTS[0]}]:
    s.sendto(json.dumps(paquete).encode(), ("{Config.BROADCAST_IP}", p))
s.close()
"""
subprocess.run(["python", "-X", "utf8", "-c", inject_script])

time.sleep(3)
p1.kill()
p2.kill()
p3.kill()

for n in [1, 2, 3]:
    print(f"\n[NODO {n}] Log de retransmisiones:")
    encontrado = False
    with open(f"out{n}.txt", "r", encoding="utf-8") as f:
        for linea in f:
            if "[MESH] Retransmitiendo" in linea:
                print(f"  -> {linea.strip()}")
                encontrado = True
    if not encontrado:
        print("  -> (No retransmitió)")

print("\n--- PRUEBA FINALIZADA ---")
