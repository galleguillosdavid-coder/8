import socket
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.network import IPv7Network
from config.constants import Config

# Inicializar componentes del sistema
network = IPv7Network()

def registrar_en_tracker(ip_tracker, mi_nombre):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    paquete_registro = {"tipo": "REGISTRO", "nombre": mi_nombre}
    
    print(f"📡 Registrando {mi_nombre} en el Tracker ({ip_tracker})...")
    try:
        sock.sendto(json.dumps(paquete_registro).encode("utf-8"), (ip_tracker, Config.TRACKER_PORT))
        datos, _ = sock.recvfrom(1024)
        if json.loads(datos.decode())["status"] == "OK":
            print("✅ Registro exitoso.")
            return True
    except Exception as e:
        print(f"❌ Error al contactar el Tracker: {e}")
        return False
    finally:
        sock.close()

def buscar_en_tracker(ip_tracker, objetivo):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    paquete_busqueda = {"tipo": "BUSQUEDA", "objetivo": objetivo}
    
    print(f"🔍 Preguntando al Tracker por la IP de {objetivo}...")
    try:
        sock.sendto(json.dumps(paquete_busqueda).encode("utf-8"), (ip_tracker, Config.TRACKER_PORT))
        datos, _ = sock.recvfrom(1024)
        respuesta = json.loads(datos.decode())
        return respuesta.get("ip")
    except Exception as e:
        print(f"❌ Error al buscar en Tracker: {e}")
        return None
    finally:
        sock.close()

def iniciar_receptor(ip_tracker, mi_nombre):
    if not registrar_en_tracker(ip_tracker, mi_nombre):
        print("Advertencia: No se pudo registrar. Iniciando escucha de todos modos...")
        
    print(f"\n[MODO RECEPTOR] {mi_nombre} escuchando en el puerto UDP {Config.DEFAULT_PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", Config.DEFAULT_PORT))
    
    while True:
        datos, addr = sock.recvfrom(65535)
        print(f"\n--- PAQUETE FÍSICO INTERCEPTADO DESDE {addr} ---")
        
        try:
            paquete = json.loads(datos.decode("utf-8"))
            print(f"📦 Cabecera leída: Origen={paquete['origen']} | Destino={paquete['destino']}")
            print(f"🔒 Payload (Cifrado): {paquete['payload_cifrado'][:30]}...")
            
            if paquete['destino'] == mi_nombre:
                print("🚦 [Router] El destino es válido. Descifrando...")
                mensaje_descifrado = network.descifrar_payload(paquete['payload_cifrado'])
                print(f"✅ [Entrega Exitosa] Mensaje: '{mensaje_descifrado}'")
            else:
                print(f"❌ [Router] Descartado. Destino {paquete['destino']} no coincide con mi nombre ({mi_nombre}).")
                
        except Exception as e:
            print(f"❌ Error procesando el paquete: {e}")

def iniciar_emisor(ip_tracker, mi_nombre):
    print(f"\n[MODO EMISOR] Identificado como {mi_nombre}")
    objetivo = input("¿A qué Nodo quieres enviar el mensaje? (ej. NODO_B): ").strip()
    if not objetivo: return
    
    ip_destino = buscar_en_tracker(ip_tracker, objetivo)
    
    if not ip_destino:
        print(f"❌ El Tracker no sabe dónde está {objetivo}. Operación abortada.")
        return
        
    print(f"🎯 El Tracker respondió: {objetivo} está en la IP {ip_destino}")
    
    mensaje = input("Escribe el mensaje que deseas enviar: ").strip()
    if not mensaje: return
        
    print("\n[Paso 1] Cifrando el mensaje con AES (Fernet)...")
    payload_cifrado = network.cifrar_payload(mensaje)
    
    paquete = network.crear_paquete("MENSAJE", mi_nombre, objetivo, payload_cifrado)
    
    print("[Paso 2] Empaquetando y enviando físicamente por la red...")
    network.enviar_udp(paquete, ip_destino)
    print(f"✅ ¡Paquete disparado a {ip_destino}:{Config.DEFAULT_PORT}!")

if __name__ == "__main__":
    print("=" * 40)
    print("IPv7 - Fase 3 (Descubrimiento Automático)")
    print("=" * 40)
    ip_tracker = input("Ingresa la IP del Tracker (ej. 127.0.0.1): ").strip()
    mi_nombre = input("¿Cuál es el nombre de este nodo? (ej. NODO_A o NODO_B): ").strip().upper()
    
    print("\n1. Actuar como Receptor (Escuchar)")
    print("2. Actuar como Emisor (Transmitir)")
    
    try:
        opcion = input("\nIngresa 1 o 2: ").strip()
        if opcion == "1":
            iniciar_receptor(ip_tracker, mi_nombre)
        elif opcion == "2":
            iniciar_emisor(ip_tracker, mi_nombre)
        else:
            print("Opción no válida.")
    except KeyboardInterrupt:
        print("\nSaliendo...")
        sys.exit(0)
