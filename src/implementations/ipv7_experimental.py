import socket
import json
import threading
import sys
import time
import os
import base64
import uuid

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.network import IPv7Network
from core.identity import IdentityManager
from core.discovery import NetworkDiscovery
from config.constants import Config

# Inicializar componentes del sistema
network = IPv7Network()
discovery = NetworkDiscovery(network)

# Nodos Puente (IPs Globales) para saltar a otras redes (Internet)
puentes_globales = set()
if os.path.exists("ipv7_puentes.json"):
    try:
        with open("ipv7_puentes.json", "r") as f:
            puentes_globales = set(json.load(f))
    except:
        pass

def guardar_puentes():
    with open("ipv7_puentes.json", "w") as f:
        json.dump(list(puentes_globales), f)

def inyectar_a_red(paquete, sock_existente=None):
    """Grita el paquete a la red local y además se lo dispara directo a cada Puente"""
    datos = json.dumps(paquete).encode("utf-8")
    sock = sock_existente or socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if not sock_existente:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
    # 1. Grito a red local a TODOS los puertos posibles
    for p in Config.LOCAL_PORTS:
        sock.sendto(datos, (Config.BROADCAST_IP, p))
        
    # 2. Túneles a Nodos Puente Lejanos
    for ip in puentes_globales:
        sock.sendto(datos, (ip, Config.LOCAL_PORTS[0])) # Asumimos que el lejano escucha en 7007
        
    if not sock_existente:
        sock.close()

def hilo_receptor(sock, mi_nombre):
    """Hilo en background que escucha todo el tráfico UDP (Gritos y Mensajes) usando el socket ya bindeado"""
    while True:
        try:
            datos, addr = sock.recvfrom(65535)
            ip_origen = addr[0]
            
            paquete = json.loads(datos.decode("utf-8"))
            tipo = paquete.get("tipo", "MENSAJE")
            
            # --- LÓGICA MESH ---
            if network.procesar_mesh_retransmision(paquete, mi_nombre):
                sys.stdout.write("\r" + " " * 60 + "\r")
                print(f"🔄 [MESH] Retransmitiendo chisme para {paquete['destino']} (TTL restante: {paquete['ttl']})")
                sys.stdout.write("Tu comando o mensaje (ej. /lista o DID:Mensaje): ")
                sys.stdout.flush()
                
                # Retransmitir a la red local Y a los Puentes Globales
                sock_retrans = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock_retrans.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                inyectar_a_red(paquete, sock_retrans)
                sock_retrans.close()
                continue # Terminamos de retransmitir, no procesamos más
            # --------------------
            
            if tipo == "BUSQUEDA_BROADCAST":
                # Alguien grita en la red buscando a un nodo
                objetivo = paquete.get("objetivo")
                if objetivo == mi_nombre or objetivo == "HOLA_RED":
                    # Soy yo o quieren saludar, le respondo directo a su IP
                    respuesta = {"tipo": "RESPUESTA_BUSQUEDA", "nombre": mi_nombre}
                    sock_resp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock_resp.sendto(json.dumps(respuesta).encode(), (ip_origen, addr[1]))
                    sock_resp.close()
                    
            elif tipo == "PING_GENERAL":
                # Alguien quiere saber quién está conectado
                respuesta = {"tipo": "RESPUESTA_BUSQUEDA", "nombre": mi_nombre}
                sock_resp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock_resp.sendto(json.dumps(respuesta).encode(), (ip_origen, addr[1]))
                sock_resp.close()
                    
            elif tipo == "RESPUESTA_BUSQUEDA":
                # Alguien respondió a nuestro grito
                nombre_descubierto = paquete.get("nombre")
                discovery.handle_discovery_response(nombre_descubierto, ip_origen)
                
            elif tipo == "MENSAJE":
                if paquete['destino'] == mi_nombre:
                    sys.stdout.write("\r" + " " * 60 + "\r") 
                    print(f"\n📩 [NUEVO MENSAJE de {paquete['origen']}]")
                    mensaje_descifrado = network.descifrar_payload(paquete['payload_cifrado'])
                    print(f"✅ '{mensaje_descifrado}'\n")
                    sys.stdout.write("Tu comando o mensaje (ej. /lista o DID:Mensaje): ")
                    sys.stdout.flush()
                    
            elif tipo == "ARCHIVO":
                if paquete['destino'] == mi_nombre:
                    sys.stdout.write("\r" + " " * 60 + "\r") 
                    nombre_archivo = paquete.get("nombre_archivo", "archivo_desconocido")
                    print(f"\n📦 [NUEVO ARCHIVO de {paquete['origen']}] -> {nombre_archivo}")
                    
                    try:
                        bytes_cifrados = paquete['payload_cifrado'].encode()
                        bytes_descifrados = network.cipher_suite.decrypt(bytes_cifrados)
                        bytes_finales = base64.b64decode(bytes_descifrados)
                        
                        # Crear carpeta si no existe
                        if not os.path.exists("descargas_ipv7"):
                            os.makedirs("descargas_ipv7")
                            
                        ruta = os.path.join("descargas_ipv7", nombre_archivo)
                        with open(ruta, "wb") as f:
                            f.write(bytes_finales)
                        print(f"✅ Archivo guardado con éxito en: {ruta}\n")
                    except Exception as e:
                        print(f"❌ Error al procesar archivo: {e}\n")
                        
                    sys.stdout.write("Tu comando o mensaje (ej. /lista o DID:Mensaje): ")
                    sys.stdout.flush()
                    
        except Exception as e:
            print(f"\n[!] Error interno en receptor: {e}")

def buscar_por_broadcast(objetivo):
    """Grita en la red local preguntando quién es el objetivo"""
    print(f"🔍 Buscando a {objetivo} en la red local...")
    return discovery.multi_port_search(objetivo)

def escanear_red():
    """Envía un paquete PING_GENERAL a todos los puertos locales para descubrir quién está activo"""
    print("\n📡 Escaneando red local y multiplexada (espera 1 seg)...")
    resultados = discovery.network_scan()
    
    print("--- NODOS CONECTADOS ---")
    if not resultados:
        print("Ningún otro nodo detectado.")
    else:
        for nombre, ip in resultados.items():
            print(f"- {nombre} (IP: {ip})")
    print("------------------------\n")

def obtener_o_crear_identidad(mi_puerto):
    """Genera un identificador único (DID) para este nodo y lo guarda en disco según su puerto"""
    return IdentityManager.get_or_create_for_port(mi_puerto)

def iniciar_emisor(mi_nombre):
    """Bucle principal (CLI) para enviar mensajes"""
    print("\n[MODO CHAT INICIADO]")
    print("Comandos:")
    print("  /lista                      -> Escanea la red local")
    print("  /puente <IP>                -> Conecta la red a un túnel lejano")
    print("  /enviar <ruta_archivo> <DID>-> Envía un archivo cifrado")
    print("  DESTINO:Mensaje             -> Envía mensaje de texto")
    print("\nTu comando o mensaje: ")
    
    while True:
        try:
            entrada = input("").strip()
            if not entrada:
                continue
                
            if entrada == "/lista":
                escanear_red()
                continue
                
            if entrada.startswith("/puente "):
                ip_puente = entrada.split(" ")[1].strip()
                puentes_globales.add(ip_puente)
                guardar_puentes()
                print(f"🌉 ¡Túnel internacional abierto hacia {ip_puente}!\n")
                continue
                
            if entrada.startswith("/enviar "):
                partes = entrada.split(" ")
                if len(partes) >= 3:
                    ruta = partes[1]
                    objetivo = partes[2].strip()
                    
                    if not os.path.exists(ruta):
                        print(f"❌ El archivo '{ruta}' no existe.\n")
                        continue
                        
                    tamaño = os.path.getsize(ruta)
                    if tamaño > 40000: # Límite conservador para un solo paquete UDP
                        print(f"❌ El archivo pesa {tamaño/1024:.1f}KB. En esta fase experimental, el límite es 40KB.\n")
                        continue
                        
                    with open(ruta, "rb") as f:
                        bytes_archivo = f.read()
                        
                    b64_bytes = base64.b64encode(bytes_archivo)
                    payload_cifrado = network.cipher_suite.encrypt(b64_bytes).decode()
                    
                    nombre_base = os.path.basename(ruta)
                    paquete_id = uuid.uuid4().hex
                    paquete = {
                        "id": paquete_id,
                        "ttl": 3, # Inmortalidad de red: 3 saltos
                        "tipo": "ARCHIVO",
                        "version": 8,
                        "origen": mi_nombre,
                        "destino": objetivo,
                        "nombre_archivo": nombre_base,
                        "longitud": len(payload_cifrado),
                        "payload_cifrado": payload_cifrado
                    }
                    
                    # Añadir a mi historial para no auto-retransmitirlo
                    network.agregar_paquete_historial(paquete_id)
                    
                    inyectar_a_red(paquete)
                    print(f"✅ ¡Archivo '{nombre_base}' inyectado en la red Mesh hacia {objetivo}!\n")
                else:
                    print("❌ Formato: /enviar ruta_del_archivo DID_DESTINO\n")
                continue
                
            if ":" not in entrada:
                print("❌ Comando no reconocido. Usa DESTINO:Mensaje\n")
                continue
                
            partes = entrada.rsplit(":", 1)
            objetivo = partes[0].strip()
            mensaje = partes[1].strip()
            
            payload_cifrado = network.cifrar_payload(mensaje)
            paquete_id = uuid.uuid4().hex
            paquete = {
                "id": paquete_id,
                "ttl": 3,
                "tipo": "MENSAJE",
                "version": 8,
                "origen": mi_nombre,
                "destino": objetivo,
                "longitud": len(payload_cifrado),
                "payload_cifrado": payload_cifrado
            }
            
            # Añadir a mi historial para no auto-retransmitirlo
            network.agregar_paquete_historial(paquete_id)
            
            inyectar_a_red(paquete)
            print(f"✅ ¡Mensaje inyectado en la red Mesh hacia {objetivo}!\n")
            
        except KeyboardInterrupt:
            print("\nApagando Nodo experimental...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error al enviar: {e}\n")

if __name__ == "__main__":
    os.system("color 0A")
    print("==================================================")
    print("   🌐 IPv7 EXPERIMENTAL (Mesh & Bridges) 🌐")
    print("==================================================")
    
    # Intentar bindear a un puerto libre
    sock_receptor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    mi_puerto = None
    for p in Config.LOCAL_PORTS:
        try:
            sock_receptor.bind(("0.0.0.0", p))
            mi_puerto = p
            break
        except OSError:
            continue
            
    if not mi_puerto:
        print("❌ Todos los puertos multiplexados están ocupados. Cierra ventanas.")
        sys.exit(1)
        
    mi_nombre = obtener_o_crear_identidad(mi_puerto)
    print(f"🌟 Tu Identidad Permanente: {mi_nombre}")
    print(f"🔌 Escuchando en el puerto local: {mi_puerto}")
    print("Pásale este ID a tus amigos para que te envíen archivos o mensajes.")
    
    # 2. Iniciar el hilo que escucha de fondo
    t = threading.Thread(target=hilo_receptor, args=(sock_receptor, mi_nombre,), daemon=True)
    t.start()
    
    # 3. Anunciarnos al entrar
    paquete_saludo = {"tipo": "BUSQUEDA_BROADCAST", "version": 8, "origen": mi_nombre, "objetivo": "HOLA_RED"}
    inyectar_a_red(paquete_saludo)
    
    # 4. Iniciar la consola de entrada
    iniciar_emisor(mi_nombre)
