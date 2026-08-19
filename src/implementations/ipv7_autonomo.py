import socket
import json
import threading
import sys
import time
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.network import IPv7Network
from core.identity import IdentityManager
from core.discovery import NetworkDiscovery
from config.constants import Config

# Inicializar componentes del sistema
network = IPv7Network()
discovery = NetworkDiscovery(network)

def hilo_receptor(mi_nombre):
    """Hilo en background que escucha todo el tráfico UDP (Gritos y Mensajes)"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", Config.DEFAULT_PORT))
    
    while True:
        try:
            datos, addr = sock.recvfrom(65535)
            ip_origen = addr[0]
            
            paquete = json.loads(datos.decode("utf-8"))
            tipo = paquete.get("tipo", "MENSAJE") # Por defecto es un mensaje
            
            if tipo == "BUSQUEDA_BROADCAST":
                # Alguien grita en la red buscando a un nodo
                objetivo = paquete.get("objetivo")
                if objetivo == mi_nombre:
                    # Soy yo, le respondo directo a su IP
                    respuesta = {"tipo": "RESPUESTA_BUSQUEDA", "nombre": mi_nombre}
                    sock_resp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock_resp.sendto(json.dumps(respuesta).encode(), (ip_origen, Config.DEFAULT_PORT))
                    sock_resp.close()
                    
            elif tipo == "PING_GENERAL":
                # Alguien quiere saber quién está conectado
                respuesta = {"tipo": "RESPUESTA_BUSQUEDA", "nombre": mi_nombre}
                sock_resp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock_resp.sendto(json.dumps(respuesta).encode(), (ip_origen, Config.DEFAULT_PORT))
                sock_resp.close()
                    
            elif tipo == "RESPUESTA_BUSQUEDA":
                # Alguien respondió a nuestro grito
                nombre_descubierto = paquete.get("nombre")
                discovery.handle_discovery_response(nombre_descubierto, ip_origen)
                
            elif tipo == "MENSAJE":
                # Llegó un paquete IPv7 físico
                if paquete['destino'] == mi_nombre:
                    # Sobrescribir la línea actual de consola para no romper el formato
                    sys.stdout.write("\r" + " " * 60 + "\r") 
                    print(f"\n📩 [NUEVO MENSAJE de {paquete['origen']}]")
                    mensaje_descifrado = network.descifrar_payload(paquete['payload_cifrado'])
                    print(f"✅ '{mensaje_descifrado}'\n")
                    sys.stdout.write("Tu mensaje (escribe destino:texto y pulsa Enter): ")
                    sys.stdout.flush()
                    
        except Exception as e:
            print(f"\n[!] Error interno en receptor: {e}")

def buscar_por_broadcast(objetivo):
    """Grita en la red local preguntando quién es el objetivo"""
    print(f"🔍 Buscando a {objetivo} en la red local...")
    return discovery.broadcast_search(objetivo)

def escanear_red():
    """Grita en la red pidiendo que todos se presenten y muestra la lista."""
    discovery.display_scan_results()

def iniciar_emisor(mi_nombre):
    """Bucle principal (CLI) para enviar mensajes"""
    print("\n[MODO CHAT INICIADO]")
    print("Escribe '/lista' para ver quién está conectado.")
    print("Formato de envío -> DESTINO: Tu mensaje secreto\n")
    
    while True:
        try:
            # Esperamos input del usuario
            entrada = input("Tu comando o mensaje (ej. /lista o DID:Mensaje): ").strip()
            if not entrada:
                continue
                
            if entrada == "/lista":
                escanear_red()
                continue
                
            if ":" not in entrada:
                print("❌ Formato incorrecto. Usa DESTINO:Mensaje o el comando /lista\n")
                continue
                
            partes = entrada.rsplit(":", 1)
            objetivo = partes[0].strip()
            mensaje = partes[1].strip()
            
            # Buscar IP dinámicamente
            ip_destino = buscar_por_broadcast(objetivo)
            
            if not ip_destino:
                print(f"❌ No se encontró a {objetivo} en la red local. ¿Está encendido?\n")
                continue
                
            # Cifrar y enviar
            payload_cifrado = network.cifrar_payload(mensaje)
            paquete = network.crear_paquete("MENSAJE", mi_nombre, objetivo, payload_cifrado)
            
            network.enviar_udp(paquete, ip_destino)
            
            print(f"✅ ¡Paquete seguro entregado a {objetivo} ({ip_destino})!\n")
            
        except KeyboardInterrupt:
            print("\nApagando Nodo...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error al enviar: {e}\n")

def obtener_o_crear_identidad():
    """Busca la identidad local o la crea si no existe."""
    return IdentityManager.get_or_create("ipv7_identidad.json")

if __name__ == "__main__":
    print("=" * 50)
    print("IPv7 - Fase 5 (Identidad Permanente Zero-Config)")
    print("=" * 50)
    
    mi_nombre = obtener_o_crear_identidad()
    print(f"🌟 Tu Identidad Permanente: {mi_nombre}")
    print(f"Pásale este ID a tus amigos para que te escriban.\n")
    
    # 1. Iniciar Receptor silencioso en segundo plano
    t = threading.Thread(target=hilo_receptor, args=(mi_nombre,), daemon=True)
    t.start()
    
    # 2. Iniciar consola interactiva
    iniciar_emisor(mi_nombre)
