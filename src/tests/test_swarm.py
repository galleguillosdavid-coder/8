import subprocess
import time
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.constants import Config

print("--- INICIANDO ENJAMBRE DE PRUEBA (3 NODOS) ---")

# Vamos a limpiar archivos de identidad viejos para que se generen frescos
for p in Config.LOCAL_PORTS[:3]:  # Solo los primeros 3 puertos
    f = f"ipv7_identidad_{p}.json"
    if os.path.exists(f):
        os.remove(f)

print("Levantando Nodo 1 (Puerto 7007)...")
p1 = subprocess.Popen(["python", "-X", "utf8", "ipv7_experimental.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd="../implementations")
time.sleep(1)

print("Levantando Nodo 2 (Puerto 7008)...")
p2 = subprocess.Popen(["python", "-X", "utf8", "ipv7_experimental.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd="../implementations")
time.sleep(1)

print("Levantando Nodo 3 (Puerto 7009)...")
p3 = subprocess.Popen(["python", "-X", "utf8", "ipv7_experimental.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd="../implementations")
time.sleep(2)

print("¡Enjambre listo! Inyectando paquete ciego hacia 'LUNA'...")
# Usamos el script inyector que hicimos antes
subprocess.run(["python", "-X", "utf8", "test_mesh_sender.py"], stdout=subprocess.DEVNULL, cwd=".")

time.sleep(2) # Dar tiempo a la cascada

p1.kill()
p2.kill()
p3.kill()

out1, _ = p1.communicate()
out2, _ = p2.communicate()
out3, _ = p3.communicate()

def mostrar_retransmisiones(out, nombre_nodo):
    print(f"\n[{nombre_nodo}] Log de retransmisiones:")
    encontrado = False
    for linea in out.split('\n'):
        if "[MESH] Retransmitiendo" in linea:
            print(f"  -> {linea.strip()}")
            encontrado = True
    if not encontrado:
        print("  -> (No retransmitió)")

mostrar_retransmisiones(out1, "NODO 1")
mostrar_retransmisiones(out2, "NODO 2")
mostrar_retransmisiones(out3, "NODO 3")

print("\n--- PRUEBA FINALIZADA ---")
