import socket
import json

PUERTO_TRACKER = 7000
directorio = {} # Guarda "NODO_X" -> "192.168.1.Y"

print("=" * 40)
print(f"IPv7 TRACKER (Directorio Central) - Puerto {PUERTO_TRACKER}")
print("=" * 40)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PUERTO_TRACKER))

while True:
    datos, addr = sock.recvfrom(1024)
    ip_origen = addr[0]
    
    try:
        mensaje = json.loads(datos.decode("utf-8"))
        tipo = mensaje.get("tipo")
        
        if tipo == "REGISTRO":
            nombre_nodo = mensaje.get("nombre")
            directorio[nombre_nodo] = ip_origen
            print(f"✅ REGISTRADO: {nombre_nodo} en la IP {ip_origen}")
            
            # Responder confirmación
            sock.sendto(json.dumps({"status": "OK"}).encode(), addr)
            
        elif tipo == "BUSQUEDA":
            objetivo = mensaje.get("objetivo")
            ip_encontrada = directorio.get(objetivo)
            
            print(f"🔍 BÚSQUEDA: Nodo {addr[0]} está buscando a {objetivo} -> Resultado: {ip_encontrada}")
            
            # Responder con la IP (o None si no existe)
            sock.sendto(json.dumps({"ip": ip_encontrada}).encode(), addr)
            
    except Exception as e:
        print(f"❌ Error procesando paquete en el tracker: {e}")
