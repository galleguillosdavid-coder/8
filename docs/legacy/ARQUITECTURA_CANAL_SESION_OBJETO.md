# 🌐 Arquitectura IPv7: Canal → Sesión → Objeto
# Paradigma orientado a objetos en lugar de puertos

> ℹ️ **Estado de implementación (2026-08-18):** `Channel` y `Session`
> descritos en este documento ya están integrados y validados en
> `ipv7_mvp/node.py` usando `src/core/channel_manager.py` y
> `src/core/session_manager.py` (9/9 tests unitarios + 5/5 validaciones
> multiproceso real, ver `DESARROLLO_CHECK.md`). A diferencia del
> `session_8172_abcd` (string) usado como ejemplo más abajo, el
> `session_id` real es un entero de 32 bits (`uint32`), compatible con
> el wire format `!I` del paquete. `Container/Object` sigue **solo en
> diseño** — ver `ARQUITECTURA_NUEVO_INTERNET.md`, Sección 36, antes de
> asumir que el formato descrito aquí es definitivo.

## 🎯 Filosofía Fundamental

**No diseñamos un TCP/IP con puertos más grandes. Diseñamos una red donde el concepto de puerto es opcional y subordinado a una arquitectura de canales, sesiones y objetos.**

## 📐 Jerarquía de Identificación

### Nivel 1: Identidad (DID)
```
did:ipv7:ABCDEFGH12345678
└── Identidad permanente del nodo
    └── Criptográficamente verificable
```

### Nivel 2: Canal (Subport Primitiva)
```
Channel ID: 0x82A71F03 (32-bit opcional)
├── 0x00: Control
├── 0x01: Telemetry  
├── 0x02: Query
├── 0x03: Write
├── 0x04: Emergency
└── 0x64+: Reservado para Profiles
```

### Nivel 3: Sesión
```
Session ID: session_8172_abcd
├── Contexto de comunicación específico
├── Estado de la conexión
├── Metadata de sesión
└── Identificadores temporales
```

### Nivel 4: Contenedor
```
Container ID: container_temp_sensors
├── Agrupación lógica de objetos
├── Definición de schema
└── Metadata del contenedor
```

### Nivel 5: Objeto (IDTLV)
```
Object ID: 14 (índice local)
├── tipo: sensor_temperatura
├── valor: 23.5°C
├── timestamp: 1234567890
└── metadata: {"unit": "celsius", "precision": 0.1}
```

## 🔄 Modelo de Comunicación

### Modo A: Channel-Oriented (Compatibilidad)
```python
# Para comunicaciones tradicionales
packet = {
    'origin': 'did:ipv7:ABC...',
    'destination': 'did:ipv7:XYZ...',
    'channel': 0x82A71F03,      # Canal de 32 bits
    'session': 'session_8172', # ID de sesión
    'payload': b'raw_bytes'
}
```

### Modo B: Object-Oriented (Nativo IPv7)
```python
# Para arquitectura avanzada
packet = {
    'origin': 'did:ipv7:ABC...',
    'destination': 'did:ipv7:XYZ...',
    'object': 'sensor_temperatura',  # Objeto semántico
    'profile': 'sensor_profile',     # Profile que define semántica
    'context': 'edificio/2/piso/4',  # Contexto del objeto
    'container': 'temp_sensors',      # Contenedor lógico
    'payload': IDTLV_encoded_data     # Datos estructurados
}
```

## 🧩 Estructura Core vs Profiles

### Core (Estructura, no semántica)
```python
class IPv7Core:
    """
    Core transporta estructura, no semántica
    """
    
    def __init__(self):
        # Capa de identidad
        self.identity_layer = IdentityManager()
        
        # Capa de transporte (canales)
        self.transport_layer = ChannelManager()
        
        # Capa de sesión
        self.session_layer = SessionManager()
        
        # Capa de fragmentación
        self.fragmentation_layer = FragmentationManager()
        
        # Capa de integridad
        self.integrity_layer = IntegrityManager()
        
        # Capa de entrega
        self.delivery_layer = DeliveryManager()
    
    def create_channel(self, channel_id: int, profile: str, capabilities: dict):
        """
        Crear canal dinámico durante handshake
        
        OPEN CHANNEL
            channel_id = 0x82A71F03
            profile = sensor_profile
            capabilities = {"telemetry": True, "query": True}
        """
        return self.transport_layer.create_channel(channel_id, profile, capabilities)
    
    def close_channel(self, channel_id: int):
        """Cerrar canal existente"""
        return self.transport_layer.close_channel(channel_id)
    
    def route_to_object(self, destination_did: str, object_type: str, context: str):
        """
        Enrutamiento orientado a objetos
        El Core no necesita saber qué es una consulta de temperatura,
        solo enruta hacia el objeto/servicio
        """
        return self.delivery_layer.route_object(destination_did, object_type, context)
```

### Profiles (Semántica, no estructura)
```python
class SensorProfile:
    """
    Profile define qué significa un canal QUERY
    """
    
    def __init__(self):
        self.profile_name = "sensor_profile"
        self.version = "1.0"
        self.capabilities = {
            "telemetry": True,
            "query": True,
            "write": False,
            "emergency": True
        }
    
    def handle_query(self, object_id: int, context: str):
        """
        El Profile sabe qué es una consulta de temperatura
        """
        if context.startswith("edificio"):
            return self._query_building_sensor(object_id, context)
        elif context.startswith("vehiculo"):
            return self._query_vehicle_sensor(object_id, context)
    
    def encode_telemetry(self, sensor_data: dict) -> bytes:
        """Codificar datos de sensor usando IDTLV"""
        return IDTLV.encode(sensor_data)
    
    def decode_telemetry(self, data: bytes) -> dict:
        """Decodificar datos de sensor usando IDTLV"""
        return IDTLV.decode(data)


class MultimediaProfile:
    """
    Profile define qué significa un canal STREAM
    """
    
    def __init__(self):
        self.profile_name = "multimedia_profile"
        self.version = "2.0"
        self.capabilities = {
            "stream": True,
            "query": True,
            "write": True
        }
    
    def handle_stream(self, object_id: int, quality: str):
        """El Profile sabe qué es streaming de video"""
        return self._setup_video_stream(object_id, quality)


class IoTProfile:
    """
    Profile define qué significa actuación IoT
    """
    
    def __init__(self):
        self.profile_name = "iot_profile"
        self.version = "1.5"
        self.capabilities = {
            "telemetry": True,
            "write": True,
            "emergency": True
        }
    
    def handle_actuation(self, object_id: int, command: str, context: str):
        """El Profile sabe qué es activar un relay IoT"""
        return self._execute_iot_command(object_id, command, context)
```

## 🌊 Ejemplo de Comunicación Real

### Escenario: Sensor de temperatura en edificio inteligente

```python
# Nodo A (Sensor) tiene esta estructura:
Nodo_A = {
    'did': 'did:ipv7:ABCDEFGH12345678',
    'sesiones': {
        'session_8172': {
            'canales': {
                0x82A71F03: {  # Canal dinámico
                    'profile': 'sensor_profile',
                    'contenedores': {
                        'temp_sensors': {
                            'objetos': {
                                14: {'tipo': 'temperatura', 'valor': 23.5, 'contexto': 'edificio/2/piso/4'},
                                15: {'tipo': 'humedad', 'valor': 45.2, 'contexto': 'edificio/2/piso/4'},
                                16: {'tipo': 'presión', 'valor': 1013, 'contexto': 'edificio/2/piso/4'},
                                17: {'tipo': 'bateria', 'valor': 85, 'contexto': 'edificio/2/piso/4'}
                            }
                        }
                    }
                }
            }
        }
    }
}

# Nodo B (Cliente) consulta:
query_packet = {
    'origin': 'did:ipv7:XYZ1234567890AB',
    'destination': 'did:ipv7:ABCDEFGH12345678',
    'mode': 'object-oriented',
    'object': 'sensor_temperatura',
    'profile': 'sensor_profile',
    'context': 'edificio/2/piso/4',
    'container': 'temp_sensors',
    'query': {
        'object_ids': [14, 15],  # Temperatura y humedad
        'format': 'idtlv'
    }
}

# Respuesta del Sensor:
response_packet = {
    'origin': 'did:ipv7:ABCDEFGH12345678',
    'destination': 'did:ipv7:XYZ1234567890AB',
    'session': 'session_8172',
    'container': 'temp_sensors',
    'objects': [
        {
            'id': 14,
            'idtlv': IDTLV.encode({
                'type': 'temperature',
                'value': 23.5,
                'unit': 'celsius',
                'timestamp': 1234567890
            })
        },
        {
            'id': 15,
            'idtlv': IDTLV.encode({
                'type': 'humidity',
                'value': 45.2,
                'unit': 'percent',
                'timestamp': 1234567890
            })
        }
    ]
}
```

## 🎭 Handshake Dinámico de Canales

```python
# Cliente inicia handshake:
handshake_request = {
    'type': 'OPEN_CHANNEL',
    'channel_id': 0x82A71F03,  # Propuesto por cliente
    'profile': 'sensor_profile',
    'capabilities': {
        'telemetry': True,
        'query': True,
        'emergency': False
    },
    'context': 'edificio/2/piso/4'
}

# Servidor responde:
handshake_response = {
    'type': 'CHANNEL_ACCEPTED',
    'channel_id': 0x82A71F03,  # Confirmado
    'session_id': 'session_8172',
    'negotiated_capabilities': {
        'telemetry': True,
        'query': True,
        'emergency': False
    },
    'container_access': ['temp_sensors', 'power_sensors']
}

# Cliente cierra canal:
close_request = {
    'type': 'CLOSE_CHANNEL',
    'channel_id': 0x82A71F03,
    'session_id': 'session_8172',
    'reason': 'normal_shutdown'
}
```

## 📊 Escalabilidad del Nuevo Modelo

### Capacidades por Dispositivo
```
1 dispositivo típico:
├── 1 identidad (DID permanente)
├── 10 sesiones simultáneas
├── 100 canales dinámicos
└── 1,000 objetos por sesión

Total: 1,000,000 objetos direccionables por dispositivo
```

### Escalabilidad Global
```
10 billones de dispositivos:
├── 10 billones de identidades
├── 100 billones de sesiones
├── 1 trillón de canales
└── 10 cuatrillones de objetos

Sin necesidad de tabla global de puertos
```

## 🚀 Beneficios del Nuevo Paradigma

### 1. **Semántica Nativa**
- Los objetos tienen significado inherente
- No necesitamos mapear números a servicios
- El enrutamiento puede ser semántico

### 2. **Escalabilidad Verdadera**
- Los IDs de objetos son locales (índices)
- No requieren coordinación global
- Combinaciones prácticamente infinitas

### 3. **Flexibilidad Extrema**
- Canales creados dinámicamente
- Profiles agregan semántica sin modificar Core
- Contextos definen ámbito de operación

### 4. **Compatibilidad con IDTLV**
- Objetos codificados naturalmente en IDTLV
- Core transporta estructura, Profiles interpretan
- Separación perfecta de responsabilidades

### 5. **Gestión de Recursos**
- Canales pueden cerrarse cuando no se necesitan
- Sesiones tienen lifecycle claro
- Objetos pueden ser cacheados/localizados

## 🎯 Regla de Oro Reafirmada

**Core transporta estructura; Profiles aportan semántica.**

- Core sabe que existe un canal QUERY
- Core NO necesita saber qué es una consulta de temperatura
- SensorProfile define semántica de consultas de temperatura
- MultimediaProfile define semántica de consultas de video
- IoTProfile define semántica de consultas de actuadores

## 🌐 Este SÍ es un Nuevo Internet

No es TCP/IP con puertos más grandes. Es:

- Una red donde transportamos **objetos semánticos**, no bytes
- Una arquitectura donde la **identidad** es primaria, no la dirección
- Un sistema donde el **contexto** define el ámbito, no el puerto
- Un protocolo donde los **profiles** dan significado, no números

Este cambio sí es digno de llamarse un nuevo internet.


# IPv7 — INSTRUCCIONES PARA IMPLEMENTAR PATH MTU + SHA-256

Estas instrucciones complementan la implementación IPv7 en Python.

La prioridad sigue siendo:

> **Código simple, funcional, fácil de probar y fácil de modificar.**

No sobreingenierizar estas funcionalidades.

---

# 1. PATH MTU DE LA SESIÓN

IPv7 debe implementar un mecanismo sencillo para determinar el tamaño máximo de paquete que puede utilizar una sesión.

La idea es:

```text
Emisor
   │
   │ descubrir ruta
   ▼
Nodo A
   │ MTU = 1500
   ▼
Nodo B
   │ MTU = 1280
   ▼
Nodo C
   │ MTU = 1400
   ▼
Receptor
```

El emisor consulta el MTU disponible en cada salto.

Al finalizar el descubrimiento:

```text
PATH_MTU = MIN(MTU de todos los saltos)
```

En este ejemplo:

```text
MIN(1500, 1280, 1400) = 1280
```

Por tanto:

```text
session.mtu = 1280
```

Todos los paquetes posteriores de esa sesión deben respetar:

```python
len(packet) <= session.mtu
```

---

# 2. NO HACER PATH MTU DISCOVERY COMPLEJO

No implementar inicialmente:

* algoritmos complejos de PMTUD
* fragmentación dinámica
* retransmisiones específicas para MTU
* ICMP
* descubrimiento estadístico
* algoritmos adaptativos
* tablas globales de MTU

La primera implementación debe ser:

```text
descubrir ruta
      ↓
preguntar MTU
      ↓
recibir MTU de cada salto
      ↓
calcular mínimo
      ↓
guardar MTU en Session
      ↓
usar ese MTU durante la sesión
```

---

# 3. INFORMACIÓN DE CADA NODO

Cada nodo IPv7 debe tener un MTU local configurable.

Por ejemplo:

```python
node.mtu = 1280
```

Por defecto utilizar un valor razonable y configurable.

Por ejemplo:

```text
--mtu 1280
```

Esto permitirá probar fácilmente diferentes rutas.

Ejemplo:

```bash
python main.py --port 9000 --mtu 1500
python main.py --port 9001 --mtu 1280
python main.py --port 9002 --mtu 1400
```

---

# 4. MENSAJE DE DESCUBRIMIENTO DE RUTA

Crear un mensaje de control sencillo:

```text
PATH_DISCOVER
```

El nodo que recibe la solicitud debe responder incluyendo su MTU:

```text
PATH_RESPONSE
    node_id
    mtu
```

No crear todavía una estructura complicada.

El objetivo es poder construir:

```python
path = [
    {"node": "A", "mtu": 1500},
    {"node": "B", "mtu": 1280},
    {"node": "C", "mtu": 1400},
]
```

y posteriormente:

```python
path_mtu = min(item["mtu"] for item in path)
```

Resultado:

```text
1280
```

---

# 5. GUARDAR EL MTU EN LA SESIÓN

La sesión debe conservar el resultado.

Por ejemplo:

```python
@dataclass
class Session:
    session_id: int
    destination: bytes
    mtu: int
```

Después del descubrimiento:

```python
session.mtu = path_mtu
```

El MTU pasa a ser una propiedad de la sesión.

Conceptualmente:

```text
SESSION
├── session_id
├── destination
├── path
└── mtu
```

No recalcular el MTU para cada paquete.

---

# 6. ¿QUÉ PASA SI CAMBIA LA RUTA?

No intentar resolver esto con un sistema complicado.

Simplemente considerar que una modificación de ruta invalida el MTU asociado.

Por ejemplo:

```text
PATH_CHANGED
```

Entonces:

```text
ruta nueva
   ↓
nuevo PATH_MTU
   ↓
actualizar Session
```

Si una ruta cambia de:

```text
A → B → C
```

a:

```text
A → B → D → C
```

se vuelve a calcular:

```text
PATH_MTU = MIN(MTU de los nuevos saltos)
```

---

# 7. RESERVAR 256 BITS PARA INTEGRIDAD

IPv7 utilizará un campo de:

```text
256 bits = 32 bytes
```

para la integridad del contenido.

Utilizar:

```python
SHA-256
```

de la biblioteca estándar:

```python
import hashlib
```

No crear un algoritmo de checksum propio.

---

# 8. SHA-256 DEL PAQUETE

Para la primera implementación:

```python
checksum = hashlib.sha256(data).digest()
```

El resultado debe ser exactamente:

```text
32 bytes
256 bits
```

El paquete conceptualmente será:

```text
┌───────────────────────────────┐
│ IPv7 Header                   │
├───────────────────────────────┤
│ ...                           │
├───────────────────────────────┤
│ SHA-256 = 32 bytes            │
├───────────────────────────────┤
│ Payload / Container            │
└───────────────────────────────┘
```

Pero cuidado:

**no calcular el hash incluyendo el propio campo SHA-256.**

---

# 9. QUÉ DEBE PROTEGER EL HASH

El hash debe permitir detectar corrupción del contenido transmitido.

Una implementación sencilla puede calcular:

```python
digest = hashlib.sha256(data_to_protect).digest()
```

donde `data_to_protect` contiene:

```text
header relevante
+
session_id
+
sequence
+
container/payload
```

No incluir en el cálculo ningún campo que cambie durante el tránsito.

La decisión exacta de qué campos entran en `data_to_protect` debe quedar encapsulada en una función:

```python
def integrity_data(packet) -> bytes:
    ...
```

Esto permitirá modificar la regla posteriormente sin reescribir todo el protocolo.

---

# 10. VALIDACIÓN EN EL RECEPTOR

El receptor debe:

```text
1. recibir paquete
2. extraer SHA-256 recibido
3. reconstruir los datos protegidos
4. calcular SHA-256 nuevamente
5. comparar
```

Conceptualmente:

```python
expected = hashlib.sha256(data).digest()

if not hmac.compare_digest(received_hash, expected):
    reject_packet()
```

Utilizar:

```python
hmac.compare_digest()
```

para la comparación.

No utilizar simplemente `==` si ya estamos implementando una comprobación relacionada con seguridad.

---

# 11. SI EL HASH NO COINCIDE

El paquete debe descartarse.

Registrar:

```text
[ERROR] Integrity check failed
```

No entregar el payload a la aplicación.

Flujo:

```text
RECEIVE
   ↓
PARSE
   ↓
CHECK SHA-256
   │
   ├── FAIL → DROP
   │
   └── OK
        ↓
      SESSION
        ↓
      CONTAINER
        ↓
      APPLICATION
```

La validación debe ocurrir antes de entregar los objetos a las capas superiores.

---

# 12. IMPORTANTE: SHA-256 NO ES AUTENTICACIÓN

No confundir:

```text
SHA-256
```

con:

```text
seguridad criptográfica completa
```

SHA-256 permite detectar:

* corrupción accidental
* modificación accidental
* errores de transmisión

Pero un atacante que pueda modificar el paquete también podría recalcular SHA-256.

Por eso posteriormente podremos añadir:

```text
AEAD
firma digital
identidad
PQC
```

Pero **NO implementar esas capas ahora solamente para resolver este problema**.

El MVP debe tener:

```text
SHA-256 → integridad
```

y posteriormente:

```text
AEAD → confidencialidad + autenticidad
```

---

# 13. NO USAR EL SHA-256 COMO IDENTIDAD

El hash de 256 bits NO es:

* node_id
* DID
* session_id
* dirección
* puerto
* objeto ID

Su función inicial es exclusivamente:

```text
INTEGRITY
```

---

# 14. COMBINACIÓN CON IDTLV

El SHA-256 puede proteger el Container completo:

```text
IPv7 Packet
│
├── Header
│
├── Session
│
├── Container
│   ├── Object 1
│   ├── Object 2
│   └── Object 3
│
└── SHA-256
```

Esto evita calcular un hash separado para cada objeto.

Si un Profile necesita integridad individual de objetos en el futuro, podrá implementarlo por separado.

---

# 15. RELACIÓN ENTRE MTU Y CONTAINER

El tamaño completo del paquete debe respetar:

```python
len(encoded_packet) <= session.mtu
```

Esto incluye:

```text
Header
+
Session fields
+
Container
+
SHA-256
```

Por tanto, si:

```text
session.mtu = 1280
```

no significa que el payload pueda ocupar 1280 bytes.

El espacio real disponible es:

```text
payload_max =
    session.mtu
    - header_size
    - session_fields
    - checksum_size
```

donde:

```text
checksum_size = 32
```

La función de construcción del paquete debe comprobar esto antes de enviarlo.

---

# 16. SI EL PAYLOAD ES DEMASIADO GRANDE

Para la primera versión:

**NO implementar fragmentación compleja.**

Si:

```python
len(packet) > session.mtu
```

rechazar la construcción del paquete y mostrar:

```text
[ERROR] Payload exceeds session MTU
```

Posteriormente podremos implementar:

```text
fragmentation
reassembly
```

como una característica independiente.

Esto mantiene el MVP muy sencillo.

---

# 17. PRUEBAS OBLIGATORIAS

Agregar tests pequeños.

### Test 1 — SHA-256 correcto

Enviar un paquete y comprobar que el receptor acepta el hash.

### Test 2 — Corrupción

Modificar un byte del payload:

```text
payload original
    ↓
modificar 1 byte
    ↓
SHA-256 diferente
    ↓
DROP
```

Debe fallar.

### Test 3 — MTU

Crear una ruta:

```text
A = 1500
B = 1280
C = 1400
```

Comprobar:

```python
session.mtu == 1280
```

### Test 4 — Payload demasiado grande

Intentar enviar:

```text
packet > 1280
```

Debe ser rechazado antes de enviarlo.

### Test 5 — Cambio de ruta

Cambiar:

```text
A → B → C
```

por:

```text
A → B → D → C
```

y comprobar que el MTU se vuelve a calcular.

---

# 18. CLI PARA PROBARLO

Agregar comandos simples:

```text
path <node>
```

Debe mostrar:

```text
Path:
A → B → C

MTU:
A = 1500
B = 1280
C = 1400

Session MTU:
1280
```

Y:

```text
sessions
```

debe mostrar:

```text
SESSION     DESTINATION     MTU
812739      node-B          1280
```

Esto permitirá verificar visualmente que funciona.

---

# 19. NO CREAR UNA CAPA "MTU ENGINE"

No crear algo como:

```text
MTUEngine
MTUManager
MTUOptimizer
MTUController
MTUDiscoveryService
```

para resolver esto.

Debe ser algo simple.

Por ejemplo:

```python
def calculate_path_mtu(path):
    return min(node.mtu for node in path)
```

Eso es suficiente para el MVP.

Si en el futuro aparece complejidad real, se refactoriza.

---

# 20. NO CREAR UNA CAPA "CHECKSUM ENGINE"

Tampoco crear una arquitectura enorme para SHA-256.

Simplemente:

```python
def calculate_hash(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()
```

y:

```python
def verify_hash(data: bytes, expected: bytes) -> bool:
    actual = hashlib.sha256(data).digest()
    return hmac.compare_digest(actual, expected)
```

Eso es suficiente.

---

# 21. RESULTADO ARQUITECTÓNICO

Después de implementar estas funcionalidades, una sesión IPv7 debe conceptualmente tener:

```text
SESSION
│
├── session_id
│
├── destination
│
├── path
│    ├── node A
│    ├── node B
│    └── node C
│
├── path_mtu
│
└── state
```

Y cada paquete:

```text
IPv7 PACKET
│
├── Header
├── Session
├── Container
│    ├── IDTLV Object
│    ├── IDTLV Object
│    └── ...
│
└── SHA-256 (32 bytes)
```

---

# 22. PRINCIPIO FINAL

La implementación debe seguir esta secuencia:

```text
DISCOVER
    ↓
FIND PATH
    ↓
QUERY MTU
    ↓
MIN(MTU)
    ↓
CREATE SESSION
    ↓
STORE SESSION MTU
    ↓
BUILD PACKET
    ↓
CHECK packet <= MTU
    ↓
CALCULATE SHA-256
    ↓
SEND
    ↓
RECEIVE
    ↓
VERIFY SHA-256
    ↓
ACCEPT / DROP
```

No agregar complejidad que no sea necesaria para realizar esta secuencia.

### Objetivo

Quiero poder ejecutar dos o más nodos Python y demostrar:

1. descubrimiento;
2. establecimiento de ruta;
3. obtención del MTU de cada salto;
4. cálculo automático del `PATH_MTU`;
5. almacenamiento del MTU en la sesión;
6. construcción de paquetes respetando ese MTU;
7. SHA-256 de 256 bits;
8. detección de corrupción;
9. rechazo de paquetes cuyo tamaño supere el MTU.

**Esto debe funcionar antes de implementar cualquier mecanismo avanzado de routing, fragmentación, PQC, trust engine o virtual ports.**

La filosofía es:

> **Primero una red pequeña que funciona perfectamente. Después hacemos que sea grande.**


# IPv7 — ESTABILIDAD DE RED, DEGRADACIÓN ADAPTATIVA Y AISLAMIENTO

## Objetivo

Implementar en IPv7 un principio fundamental:

> **La red no debe sacrificar su estabilidad para mantener a toda costa una conexión o un nodo problemático.**

Cuando un nodo, enlace o ruta comienza a presentar problemas, IPv7 debe **reducir progresivamente los recursos que le asigna**, proteger las conexiones sanas y, si el problema persiste, aislar temporalmente el componente.

Esto es diferente de un sistema tradicional que puede insistir en recuperar una conexión fallida y terminar consumiendo recursos excesivos.

---

# 1. PRINCIPIO FUNDAMENTAL

IPv7 debe priorizar:

```text
ESTABILIDAD GLOBAL
        ↓
COMUNICACIONES SANAS
        ↓
COMUNICACIONES DEGRADADAS
        ↓
COMPONENTES INESTABLES
```

No:

```text
CONEXIÓN FALLIDA
        ↓
MÁS RETRANSMISIONES
        ↓
MÁS RECURSOS
        ↓
MÁS CONGESTIÓN
        ↓
AFECTAR A TODA LA RED
```

La filosofía es:

> **Un componente problemático no debe arrastrar a toda la red.**

---

# 2. NO IMPLEMENTAR UN "CASTIGO"

No llamar inicialmente a esto "penalización" o "castigo".

El sistema debe considerarse un:

```text
Adaptive Stability Controller
```

Su función es proteger la red.

Un nodo puede degradarse por:

* pérdida de paquetes
* latencia excesiva
* timeouts
* retransmisiones
* congestión
* MTU inválido
* respuestas inconsistentes
* rutas inestables
* errores repetidos
* comportamiento anómalo

Pero un único error no debe provocar aislamiento.

---

# 3. ESTADOS DEL NODO/RUTA

Implementar inicialmente solamente cinco estados:

```text
NORMAL
DEGRADED
UNSTABLE
RESTRICTED
ISOLATED
```

Flujo:

```text
NORMAL
   ↓
DEGRADED
   ↓
UNSTABLE
   ↓
RESTRICTED
   ↓
ISOLATED
```

Pero también debe existir recuperación:

```text
ISOLATED
   ↓
PROBE
   ↓
RECOVERING
   ↓
DEGRADED
   ↓
NORMAL
```

No crear todavía un sistema complejo de estados.

---

# 4. RECURSOS

Cada estado define cuánto tráfico puede utilizar el componente.

Ejemplo inicial:

```text
NORMAL       = 100%
DEGRADED     = 50%
UNSTABLE     = 20%
RESTRICTED   = 5%
ISOLATED     = 0%
```

Estos valores son solamente parámetros iniciales.

Deben estar en configuración:

```python
NORMAL_LIMIT = 1.00
DEGRADED_LIMIT = 0.50
UNSTABLE_LIMIT = 0.20
RESTRICTED_LIMIT = 0.05
ISOLATED_LIMIT = 0.00
```

No codificar estos valores directamente en múltiples lugares.

---

# 5. MÉTRICAS MÍNIMAS

No implementar todavía un sistema de telemetría enorme.

Cada vecino/ruta debe registrar solamente:

```text
packets_sent
packets_received
packets_lost
timeouts
retries
latency
last_seen
```

Opcionalmente:

```text
mtu
```

porque el MTU forma parte del estado de la ruta.

---

# 6. SCORE DE ESTABILIDAD

Crear un valor sencillo:

```text
stability_score = 0..100
```

Interpretación:

```text
90–100  NORMAL
70–89   DEGRADADO
40–69   INESTABLE
10–39   RESTRINGIDO
0–9     AISLADO
```

No intentar crear inicialmente una fórmula matemática perfecta.

Debe ser fácil de entender y modificar.

Por ejemplo, se pueden aplicar pequeñas variaciones según:

```text
+ respuesta correcta
+ baja latencia
+ estabilidad

- pérdida
- timeout
- retransmisión
- latencia excesiva
- error de protocolo
```

---

# 7. EVITAR FALSOS POSITIVOS

Esta es una regla crítica.

IPv7 NO debe aislar un nodo porque un solo paquete falló.

Ejemplo:

```text
100 paquetes
2 perdidos
```

No significa que el nodo esté fallando.

Por eso utilizar una ventana de observación.

Por ejemplo:

```text
últimos 20 paquetes
```

o una ventana temporal:

```text
últimos 10 segundos
```

La implementación inicial puede utilizar una ventana pequeña y configurable.

---

# 8. EJEMPLO

Supongamos:

```text
Nodo A → Nodo B
```

Durante una ventana:

```text
100 paquetes enviados
95 recibidos
5 perdidos
```

Pérdida:

```text
5%
```

No aislar inmediatamente.

El nodo puede pasar:

```text
NORMAL
   ↓
DEGRADED
```

Si posteriormente:

```text
100 enviados
30 perdidos
```

y además aparecen:

```text
timeouts
retries
latencia alta
```

puede pasar:

```text
DEGRADED
   ↓
UNSTABLE
```

Si continúa:

```text
UNSTABLE
   ↓
RESTRICTED
   ↓
ISOLATED
```

---

# 9. RECUPERACIÓN

El sistema debe ser reversible.

Nunca asumir:

```text
problemático = permanentemente malo
```

Después del aislamiento, enviar pequeños probes:

```text
PROBE
```

Por ejemplo:

```text
ISOLATED
   ↓
PROBE
   ↓
PONG
```

Si responde correctamente:

```text
ISOLATED
   ↓
DEGRADED
```

Después de suficiente estabilidad:

```text
DEGRADED
   ↓
NORMAL
```

La recuperación debe ser gradual.

---

# 10. PROTEGER LAS CONEXIONES SANAS

Los recursos liberados al degradar un nodo no deben simplemente desaparecer.

Deben quedar disponibles para:

* otras rutas
* otras sesiones
* tráfico de control
* comunicaciones estables

Ejemplo:

```text
Nodo A
 ├── B → inestable
 ├── C → normal
 └── D → normal
```

Si B comienza a fallar:

```text
B ↓ recursos
C ↑ disponibilidad
D ↑ disponibilidad
```

No permitir que B consuma indefinidamente los recursos de A.

---

# 11. PRIORIDAD DEL TRÁFICO

No todo tráfico debe recibir el mismo tratamiento.

Mantener los canales lógicos existentes:

```text
0 = control
1 = telemetry
2 = query
3 = write
4 = emergency
```

El tráfico de control debe tener prioridad suficiente para permitir:

```text
PROBE
PATH_UPDATE
SESSION_CONTROL
```

incluso cuando una ruta esté degradada.

Esto es importante porque un nodo restringido debe poder demostrar que se recuperó.

---

# 12. EMERGENCY

El canal:

```text
4 = emergency
```

puede recibir un tratamiento especial.

Pero NO permitir que "emergency" se convierta en una forma de saltarse todos los límites.

Inicialmente:

```text
emergency > normal traffic
```

pero continúa sujeto a límites globales.

Esto evita que una aplicación pueda marcar todo como emergencia y destruir la protección de la red.

---

# 13. RELACIÓN CON EL ROUTING

El stability score debe influir en la selección de rutas.

Ejemplo:

```text
Ruta A:
A → B → C
score = 95

Ruta B:
A → D → C
score = 45
```

Preferir:

```text
Ruta A
```

Pero no convertir inmediatamente el score en una métrica de routing complicada.

Para el MVP basta:

```python
route_score = min(node_scores)
```

o una métrica sencilla equivalente.

Una ruta que contiene un nodo extremadamente inestable debe considerarse menos atractiva.

---

# 14. RELACIÓN CON EL MTU

El sistema de MTU desarrollado anteriormente debe integrarse con esto.

Una sesión ya tiene:

```text
PATH
PATH_MTU
```

Ejemplo:

```text
A → B → C

B MTU = 1500
C MTU = 1280

PATH_MTU = 1280
```

Si cambia la ruta:

```text
PATH_CHANGED
```

se recalcula:

```text
PATH_MTU
```

Además, una ruta que presenta:

```text
MTU inconsistentes
fragmentación inesperada
errores de tamaño
```

debe reducir su stability score.

No asumir que todo error de MTU significa que el nodo está mal: puede significar simplemente que la ruta necesita recalcularse.

---

# 15. AISLAMIENTO

Cuando el score sea extremadamente bajo o se detecten fallos persistentes:

```text
ISOLATED
```

significa:

> No utilizar normalmente este nodo/ruta para tráfico de datos.

No significa:

> Eliminar el nodo de la existencia de la red.

Debe seguir siendo posible:

```text
PROBE
DISCOVERY
PATH_RECALCULATION
RECOVERY
```

El aislamiento es temporal y reversible.

---

# 16. EVITAR OSCILACIONES

Un problema importante será:

```text
NORMAL
DEGRADED
NORMAL
DEGRADED
NORMAL
...
```

No permitir cambios de estado a cada paquete.

Utilizar umbrales y ventanas.

Ejemplo:

```text
entra en DEGRADED:
score < 90

vuelve a NORMAL:
score > 95
```

La diferencia entre entrada y salida evita oscilaciones.

Esto se llama histéresis, pero la implementación debe mantenerse simple.

---

# 17. NO CREAR UN SISTEMA DISTRIBUIDO COMPLEJO

El estado de estabilidad debe ser inicialmente **local**.

Cada nodo evalúa a sus vecinos según lo que observa directamente.

No implementar todavía:

* consenso
* reputación global
* blockchain
* votaciones
* trust network distribuida
* autoridad central
* ML

Ejemplo:

```text
Nodo A observa B
Nodo A calcula score de B
```

Eso es suficiente para el MVP.

Posteriormente podremos agregar intercambio de información entre nodos.

---

# 18. ESTRUCTURA SIMPLE EN PYTHON

Una implementación inicial puede ser:

```python
@dataclass
class PeerHealth:
    node_id: str
    score: float = 100.0
    state: str = "NORMAL"

    packets_sent: int = 0
    packets_received: int = 0
    timeouts: int = 0
    retries: int = 0
    latency_ms: float = 0.0
```

Y funciones sencillas:

```python
record_success(peer)
record_failure(peer)
update_score(peer)
update_state(peer)
```

No crear una arquitectura de clases enorme.

---

# 19. ALGORITMO SIMPLE

La primera versión puede funcionar así:

```text
paquete correcto
    ↓
score aumenta ligeramente

timeout
    ↓
score disminuye

pérdida
    ↓
score disminuye

latencia excesiva
    ↓
score disminuye

score bajo
    ↓
cambiar estado
```

No buscar inicialmente una fórmula perfecta.

La fórmula debe ser configurable para poder experimentar.

---

# 20. LOGS

Mostrar cambios importantes:

```text
[HEALTH] node-B score=82 state=DEGRADED
```

Después:

```text
[HEALTH] node-B score=48 state=UNSTABLE
```

Después:

```text
[HEALTH] node-B score=18 state=RESTRICTED
```

Y finalmente:

```text
[HEALTH] node-B score=5 state=ISOLATED
```

Durante recuperación:

```text
[HEALTH] node-B probe successful
[HEALTH] node-B state=DEGRADED
```

---

# 21. COMANDOS DE DIAGNÓSTICO

Agregar al CLI:

```text
peers
```

debe mostrar algo parecido a:

```text
NODE       SCORE    STATE       LATENCY    LOSS
node-A     98       NORMAL      12ms       0%
node-B     61       UNSTABLE    180ms      8%
node-C     94       NORMAL      20ms       1%
```

Esto será muy útil durante las pruebas.

---

# 22. PRUEBAS

Crear pruebas para:

### Test 1

Nodo estable:

```text
score ≈ 100
state = NORMAL
```

### Test 2

Pérdida moderada:

```text
score disminuye
state = DEGRADED
```

### Test 3

Muchos timeouts:

```text
score disminuye significativamente
```

### Test 4

Fallos persistentes:

```text
NORMAL
→ DEGRADED
→ UNSTABLE
→ RESTRICTED
→ ISOLATED
```

### Test 5

Recuperación:

```text
ISOLATED
→ PROBE
→ DEGRADED
→ NORMAL
```

### Test 6

Dos rutas:

```text
Ruta A score 95
Ruta B score 45
```

La ruta A debe ser preferida.

---

# 23. REGLA DE ORO

La red debe comportarse así:

```text
                 ┌──────────────┐
                 │ RED ESTABLE  │
                 └──────┬───────┘
                        │
                  detectar problema
                        │
                        ▼
                 ┌──────────────┐
                 │  DEGRADAR    │
                 └──────┬───────┘
                        │
                 sigue fallando
                        │
                        ▼
                 ┌──────────────┐
                 │  RESTRINGIR  │
                 └──────┬───────┘
                        │
                 sigue fallando
                        │
                        ▼
                 ┌──────────────┐
                 │   AISLAR     │
                 └──────┬───────┘
                        │
                      probe
                        │
                        ▼
                 ┌──────────────┐
                 │  RECUPERAR   │
                 └──────────────┘
```

## PRINCIPIO ARQUITECTÓNICO

> **IPv7 debe proteger la red antes que proteger una conexión individual.**

Un nodo sano no debe perder estabilidad porque otro nodo esté fallando.

Un nodo problemático recibe progresivamente menos recursos, pero conserva un canal mínimo para control, diagnóstico y recuperación.

La degradación debe ser:

* gradual
* medible
* reversible
* local inicialmente
* resistente a falsos positivos
* compatible con routing
* compatible con sesiones
* compatible con PATH_MTU

Y, sobre todo:

> **No implementar más de lo necesario para demostrar este comportamiento en un MVP Python funcional.**

---

# 23. Fase 3 — Node Knowledge, Discovery y Availability

La prueba real con dos nodos UDP (A en 9010, B en 9011) mostró que `Channel`
y `Session` funcionan, pero el modelo de `peers`/`routes` está acoplado.

La nueva arquitectura separa:

```text
IDENTITY → NODE KNOWLEDGE → PATH → AVAILABILITY
```

* `Node Knowledge` unifica lo que hoy está disperso en `peers`, `routes`,
  `sessions` e `identity`.
* `Discovery` pasa a ser consulta de locator/identidad, no heartbeat.
* `Availability` reemplaza el booleano `connected`.

Ver `ARQUITECTURA_NUEVO_INTERNET.md` Sección 37.

---

# 24. Node Knowledge — Conocer por identidad, observar por comportamiento

IPv7 no asume que conoce a un nodo porque este lo declara. Construye
conocimiento progresivamente a partir de:

* **Identity**: ¿quién es?
* **Declaration**: ¿qué dice que puede hacer?
* **Observation**: ¿qué demuestra con su comportamiento?

> **Declared capability is information. Observed capability is evidence.**

Este modelo permite que sensores, sondas espaciales, servidores y nodos
IPv4/IPv6 conectados mediante un gateway entren en la red sin necesidad de
heartbeat ni broadcast periódico.

> **NETWORKS LEARN, THEY DO NOT ASSUME.**

Ver `ARQUITECTURA_NUEVO_INTERNET.md` Sección 37.8.
