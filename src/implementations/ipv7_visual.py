from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import time

app = Flask(__name__)

# Generamos una clave maestra simulada para el entorno controlado
SECRET_KEY = Fernet.generate_key()
cipher_suite = Fernet(SECRET_KEY)

# Nodos simulados en memoria (Usando DIDs reales)
NODOS = {
    "did:ipv7:00000000000A": {"nombre": "Computador A"},
    "did:ipv7:00000000000B": {"nombre": "Computador B"},
    "did:ipv7:00000000000C": {"nombre": "Computador C"}
}

# SIMBI Resolver (Nombres legibles -> DIDs Técnicos)
RESOLVER = {
    "NODO_A": "did:ipv7:00000000000A",
    "NODO_B": "did:ipv7:00000000000B",
    "NODO_C": "did:ipv7:00000000000C"
}

def enrutar_paquete(paquete):
    """
    Simulación del Router/Núcleo IPv7. Recibe un paquete, lee la cabecera,
    y lo despacha si el destino es válido, devolviendo el log paso a paso.
    """
    logs = []
    logs.append(f"🔍 [Paso 1] SIMBI Resolver: Traduciendo destino a ID técnico -> {paquete['destino']}.")
    time.sleep(0.5)
    logs.append(f"📦 [Paso 2] Empaquetado: Origen {paquete['origen']} preparó el mensaje.")
    
    # Simulación de transmisión
    time.sleep(0.5)
    logs.append(f"🔒 [Paso 3] Cifrado (IPv7 Núcleo): El payload se ha cifrado a AES. Carga: {paquete['payload_cifrado'][:20]}...")
    
    # Validar destino
    time.sleep(0.5)
    destino = paquete['destino']
    if destino in NODOS:
        nombre_real = NODOS[destino]['nombre']
        logs.append(f"🚦 [Paso 4] Router: Validando destino. {destino} ({nombre_real}) existe. Despachando...")
        time.sleep(0.5)
        # Desencriptar en destino
        mensaje_descifrado = cipher_suite.decrypt(paquete['payload_cifrado'].encode()).decode()
        logs.append(f"✅ [Paso 5] Entrega: {nombre_real} recibió y descifró el mensaje: '{mensaje_descifrado}'.")
        return {"exito": True, "logs": logs, "mensaje": mensaje_descifrado}
    else:
        logs.append(f"❌ [Error] Router: El destino {destino} no existe en la red.")
        return {"exito": False, "logs": logs, "mensaje": None}

@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>IPv7 Visual Prototype</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
            body { background: #0f172a; color: #f8fafc; font-family: 'Inter', sans-serif; display: flex; flex-direction: column; align-items: center; padding: 2rem; margin: 0; }
            h1 { font-size: 2.5rem; background: -webkit-linear-gradient(#38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .container { display: flex; gap: 2rem; width: 100%; max-width: 900px; margin-top: 2rem; }
            .card { background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 16px; padding: 1.5rem; flex: 1; backdrop-filter: blur(10px); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
            input, button { width: 100%; padding: 0.75rem; margin-top: 1rem; border-radius: 8px; border: none; font-family: 'Inter', sans-serif; box-sizing: border-box; }
            input { background: #0f172a; color: #fff; border: 1px solid #475569; }
            button { background: #38bdf8; color: #0f172a; font-weight: 600; cursor: pointer; transition: 0.3s; }
            button:hover { background: #7dd3fc; }
            .logs { margin-top: 1.5rem; background: #000; padding: 1rem; border-radius: 8px; font-family: monospace; color: #4ade80; min-height: 150px; font-size: 0.9rem; line-height: 1.5; }
            .log-line { opacity: 0; animation: fadeIn 0.5s forwards; }
            @keyframes fadeIn { to { opacity: 1; } }
            #status-dot { height: 12px; width: 12px; background-color: #ef4444; border-radius: 50%; display: inline-block; margin-right: 8px; box-shadow: 0 0 8px #ef4444; }
            .active-dot { background-color: #22c55e !important; box-shadow: 0 0 8px #22c55e !important; }
        </style>
    </head>
    <body>
        <h1>IPv7 Entorno Controlado</h1>
        <p>Prototipo Visual de Transmisión de Paquetes</p>
        
        <div class="container">
            <!-- NODO A -->
            <div class="card">
                <h2>Nodo A (Emisor)</h2>
                <select id="destino" style="width: 100%; padding: 0.75rem; margin-top: 1rem; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; font-family: 'Inter', sans-serif;">
                    <option value="NODO_B">Destino: Nodo B</option>
                    <option value="NODO_C">Destino: Nodo C</option>
                    <option value="NODO_INEXISTENTE">Destino: Nodo X (Error)</option>
                </select>
                <input type="text" id="mensaje" placeholder="Escribe un mensaje..." autocomplete="off">
                <button onclick="enviar()">Transmitir Paquete</button>
            </div>
            
            <!-- NÚCLEO / LOGS -->
            <div class="card" style="flex: 1.5;">
                <h2><span id="status-dot"></span>Router IPv7 (Logs)</h2>
                <div class="logs" id="log-box">Esperando tráfico...</div>
            </div>

            <!-- SNIFFER (Atacante) -->
            <div class="card" style="border-color: #ef4444;">
                <h2 style="color: #ef4444;">Sniffer (Atacante)</h2>
                <p style="font-size: 0.8rem; color: #94a3b8;">Tratando de leer en la red...</p>
                <div class="logs" id="sniffer-box" style="color: #ef4444; word-break: break-all; min-height: 100px;">Sin capturas...</div>
            </div>
        </div>

        <script>
            async function enviar() {
                const msg = document.getElementById('mensaje').value;
                const dest = document.getElementById('destino').value;
                if(!msg) return;
                
                const logBox = document.getElementById('log-box');
                const snifferBox = document.getElementById('sniffer-box');
                const dot = document.getElementById('status-dot');
                logBox.innerHTML = ''; // Limpiar logs
                snifferBox.innerHTML = 'Interceptando la red...';
                dot.classList.add('active-dot');
                
                // Petición al servidor Python
                const response = await fetch('/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ mensaje: msg, destino: dest })
                });
                
                const data = await response.json();
                
                // Mostrar logs uno por uno para efecto visual
                data.logs.forEach((log, index) => {
                    setTimeout(() => {
                        logBox.innerHTML += `<div class="log-line">${log}</div>`;
                        
                        // Cuando el núcleo cifra, el sniffer atrapa los datos
                        if (log.includes("Cifrado")) {
                            snifferBox.innerHTML = `<strong>¡Paquete Atrapado!</strong><br><br><code>${data.paquete_interceptado}</code><br><br><em>(Totalmente ilegible, cifrado AES)</em>`;
                        }
                    }, index * 600); // 600ms de retraso entre cada linea
                });
                
                setTimeout(() => {
                    dot.classList.remove('active-dot');
                }, data.logs.length * 600);
            }
        </script>
    </body>
    </html>
    """

@app.route("/send", methods=["POST"])
def send_packet():
    datos = request.json
    mensaje_plano = datos.get("mensaje", "")
    destino_nombre = datos.get("destino", "NODO_B")
    
    # Resolución SIMBI
    destino_did = RESOLVER.get(destino_nombre, "did:ipv7:INEXISTENTE_ERROR")
    origen_did = RESOLVER.get("NODO_A")
    
    # 1. Empaquetado y Cifrado (Simulado en Nodo A)
    payload_cifrado = cipher_suite.encrypt(mensaje_plano.encode()).decode()
    
    paquete_ipv7 = {
        "version": 7,
        "origen": origen_did,
        "destino": destino_did,
        "longitud": len(payload_cifrado),
        "payload_cifrado": payload_cifrado
    }
    
    # 2. Despachar a través del Núcleo
    resultado = enrutar_paquete(paquete_ipv7)
    resultado["paquete_interceptado"] = paquete_ipv7["payload_cifrado"]
    
    return jsonify(resultado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
