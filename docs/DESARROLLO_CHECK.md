# IPv7-SIMBI - Check de Desarrollo

**Estado**: Core integrado en el MVP | 9/9 tests unitarios PASS | 5/5 validaciones multiproceso real PASS | A → B → C relay validado
**Última actualización**: 18/08/2026
**Fase actual**: Fase 2.5 cerrada — próximo hito es Fase 3: diseño de Node Knowledge + First Contact (sin código todavía)

---

## 🎯 Visión del Proyecto

**IPv7 no es una evolución de IPv4/IPv6. Es una arquitectura de Internet nueva que explora paradigmas diferentes de comunicación.**

### Principio Fundamental
> **El Core debe transportar estructura, no imponer semántica.**

```
CORE → PROFILES → APPLICATIONS
```

**Objetivo final**: Una red donde identidad, localización, sesión, canal, objeto, contenido y aplicación sean conceptos independientes pero composibles, sin las limitaciones fundamentales del TCP/IP actual.

---

## 📋 Principios Fundamentales Actualizados

### Arquitectura Core vs Profiles
- **Core**: Transporta estructura (identidad, transporte, sesiones, canales, objetos)
- **Profiles**: Aportan semántica (sensores, multimedia, IoT, vehículos, etc.)
- **Applications**: Usan Profiles y primitivas del Core

### Object-Oriented Networking
- **NO**: `bytes → paquetes → bytes` (paradigma TCP/IP)
- **SÍ**: `objetos → contenedores → objetos` (paradigma IPv7)

### IDTLV
- **Estructura**: `TYPE | LENGTH | ID | VALUE`
- **ID Local**: Índice local dentro del contenedor (NO dirección global, NO DID)
- **Type**: 1 byte para categorías estructurales (NO semántica masiva)

### NO TCP/IP con Puertos Más Grandes
- **Rechazado**: `IP + PORT = SERVICE` (paradigma antiguo)
- **Implementado**: `CHANNEL → SESSION → CONTAINER → OBJECT`

### Canales Lógicos (Subports)
- **0**: Control
- **1**: Telemetry
- **2**: Query
- **3**: Write
- **4**: Emergency
- **100+**: Reservado para Profiles

### Desarrollo Minimalista
- **Python simple**: Solo librería estándar donde sea posible
- **Funcionalidad primero**: Demostrar que funciona antes de optimizar
- **Sin sobreingeniería**: No crear frameworks para problemas hipotéticos

---

## 🧩 Arquitectura Técnica Actualizada

### Sistema de Identificación
- **DIDs**: Identificadores criptográficos en formato `did:ipv7:XXXXXXXXXXXX`
- **Separación**: Identidad ≠ Ubicación física
- **Persistencia**: DIDs almacenados localmente
- **Evolución**: Soporte para rotación de claves y PQC (post-quantum cryptography)

### Cifrado y Seguridad
- **Por diseño**: Seguridad integrada en todas las capas
- **Algoritmos**: Ed25519, ML-DSA, AES-GCM, HKDF (evaluación en curso)
- **Handshake**: Intercambio de claves + derivación de sesión
- **Integridad**: Firmas, anti-replay, timestamps, TTL

### Transporte y Red
- **Transporte**: UDP para fases iniciales (evolución hacia QUIC/WireGuard)
- **Discovery**: Query/response orientado (la red escucha más de lo que grita)
- **Enrutamiento**: Separación de identidad, ubicación, servicio, objeto
- **Overlay**: Aprovechar IPv4/IPv6 como infraestructura mientras IPv7 desarrolla su propia arquitectura

### Estructura de Paquetes
```
IPv7 Packet
├── Core Header
├── Security / Integrity  
├── Session / Channel information
└── Container
     ├── IDTLV Object
     ├── IDTLV Object
     └── IDTLV Object
```

---

## 📁 Estructura del Proyecto Actualizada

### MVP (Nueva Arquitectura, Core integrado)
```
ipv7_mvp/
├── main.py                    - Punto de entrada (--port, --mtu, --node-id, --name)
├── node.py                    - Nodo funcional con CLI (usa src/core/session_manager.py y channel_manager.py)
├── packet.py                  - Paquete básico (HEADER + PAYLOAD + SHA-256)
├── object.py                  - IDTLV simple (TYPE | LENGTH | ID | VALUE) — heredado, en revisión (Sección 36)
├── session.py                 - ⚠️ LEGACY, ya no se usa (ver src/core/session_manager.py)
├── tests.py                   - Suite unitaria (9/9 PASS)
├── test_multiprocess.py       - Validación con 4 procesos OS independientes (5/5 PASS)
└── README.md                  - Instrucciones del MVP
```

### Core (Nueva Arquitectura)
```
src/core/
├── identity.py                - Gestión de DIDs criptográficos
├── network.py                 - Transporte UDP y cifrado
├── discovery.py               - Descubrimiento de red
├── channel_manager.py         - Canales dinámicos (subports)
├── session_manager.py         - Sesiones de comunicación
└── object_manager.py          - Gestión de objetos IDTLV
```

### Profiles (Nueva Arquitectura)
```
src/profiles/
├── sensor_profile.py          - Semántica de sensores IoT
└── __init__.py
```

### Implementaciones Legacy (Paradigma Antiguo)
```
src/implementations/
├── ipv7_visual.py             - Prototipo visual (paradigma puertos)
├── ipv7_real.py               - Prototipo físico (paradigma puertos)
├── ipv7_autonomo.py           - Versión autónoma (paradigma puertos)
├── ipv7_experimental.py       - Versión experimental (paradigma puertos)
└── tracker.py                 - Sistema de tracking (paradigma puertos)
```

### Documentación Arquitectónica
```
docs/
├── ARQUITECTURA_CANAL_SESION_OBJETO.md - Nueva arquitectura
├── ARQUITECTURA_NUEVO_INTERNET.md - Visión del nuevo internet
├── NODE_KNOWLEDGE.md - Modelo de conocimiento del nodo (First Contact)
├── FIRST_CONTACT_DESIGN.md - Diseño del flujo de First Contact
├── CONTACT_KNOWLEDGE_INVARIANTS.md - Invariantes de Contact/Knowledge/Truth/Lifetime/Probe
├── CONTAINER_OBJECT_WIREFORM_DESIGN.md - Diseño del modelo lógico Container → Object
├── PROTOCOLO_IPV7_TRANSPORT.md - Especificación de transporte
├── SISTEMA_PUERTOS_VIRTUALES.md - Sistema de puertos virtuales
├── CARACTERISTICAS_IPV7.md - Características detalladas
└── DESARROLLO_CHECK.md - Este archivo
```

---

## ✅ Fases Completadas

### Fase Legacy (Paradigma Antiguo - Puertos)
Estas fases usaban el paradigma `IP + PORT = SERVICE`:

✅ **Fase 1: Prototipo Visual** - Interfaz web Flask con visualización de paquetes
✅ **Fase 2: Prototipo Físico** - UDP punto a punto con tracker
✅ **Fase 3: Autonomía P2P** - DIDs automáticos con broadcast discovery
✅ **Fase 4: Experimental** - Archivos, mesh networking y puentes
✅ **Fase 5: Empaquetado** - Ejecutables .exe con PyInstaller

### Fase Nueva Arquitectura (Paradigma CHANNEL → SESSION → OBJECT)

✅ **Fase 0: Arquitectura Definida** - Principios fundamentales establecidos
✅ **Fase 1: MVP Funcional** - Implementación mínima que demuestra la arquitectura
- Packet básico con HEADER + PAYLOAD
- IDTLV simple (TYPE | LENGTH | ID | VALUE)
- Sesiones dinámicas con IDs aleatorios
- Canales lógicos (subports)
- Discovery LAN básico
- CLI funcional para pruebas

✅ **Fase 2: Core Refactorizado (parcial)** - SessionManager y ChannelManager reales integrados en el MVP (`ipv7_mvp/node.py`), validado con 9/9 tests unitarios
✅ **Fase 2.5: Validación multiproceso real** - 4 procesos OS independientes (UDP real, sin router in-process) validando PATH_DISCOVER/PATH_RESPONSE/PATH_MTU/SessionManager/ChannelManager. 5/5 checks PASS (`ipv7_mvp/test_multiprocess.py`)
✅ **Fase 2.5-ext: Validación A → B → C con relay obligatorio** - 3 nodos UDP reales, A sin visibilidad directa de C, PATH_DISCOVER + DATA relay a través de B, PATH_MTU = 1280 mínimo (`ipv7_mvp/demo_3nodes.py`)
🎨 **Fase 3: Node Knowledge + First Contact Design — CERRADA CONCEPTUALMENTE, sin código todavía** - Modelo de conocimiento construido *sobre* las primitivas del Core: DECLARED / OBSERVED / VERIFIED; Identity, Locator, Reachability, Availability, Capabilities, Profiles, Path, Metrics. Matriz de conocimiento, tres situaciones de contacto, flujo DISCOVERY → FIRST CONTACT → PATH → SESSION → KNOWLEDGE, ciclo de vida stale/refresh/update/expire/verify, separación entre mecanismo de contacto (Core) e información intercambiada (Objects/Profiles), modelo CONTACT → OBSERVE → KNOWLEDGE → PROBE → VERIFIED, tres categorías de conocimiento (Observation / Measurement / Capability), e invariantes de diseño cerradas en `CONTACT_KNOWLEDGE_INVARIANTS.md`. Ver `ARQUITECTURA_NUEVO_INTERNET.md` Sección 38, `NODE_KNOWLEDGE.md`, `FIRST_CONTACT_DESIGN.md` y `CONTACT_KNOWLEDGE_INVARIANTS.md`.
✅ **Fase 4.5: Container → Object / IDTLV — BYTE FREEZE V1, sin código todavía** - Wire format V1 congelado: Container Header 5 bytes (VERSION, FLAGS, OBJECT_COUNT, PAYLOAD_LENGTH big-endian); Object Header 4 bytes (TYPE, ID, LENGTH big-endian); ID 0..254 válidos/255 reservado; TYPE 0 y 255 reservados; LENGTH=0 válido; big endian; ejemplos hexadecimales de First Contact, Node Knowledge, Measurement, Capability, Availability, Evidence, nodo no-IPv7, Container anidado, fragmentación y firma; casos A–I verificados; ataques al formato definidos. Ver `CONTAINER_OBJECT_WIREFORM_DESIGN.md`.
⏳ **Fase 5: Identity** - Integración mínima de `src/core/identity.py` en el MVP
⏳ **Fase 6: Availability** - `Membership`, `Presence`, `Response Capability`, `Expected Latency`, `Communication Window`, `Wake Pattern`, `Communication Mode` + declaración `AVAILABLE_FOR` por canal. **Solo documentado** (ver `ARQUITECTURA_NUEVO_INTERNET.md`, Sección 35). Depende de Container/Object e Identity. Principio: *IPv7 no define cuándo un nodo está conectado; define cómo puede participar en la comunicación.*
⏳ **Fase 7: Profiles Implementados** - Sensor profile y demás perfiles semánticos
⏳ **Fase 8: Seguridad Integrada** - Handshake, key derivation, AEAD
⏳ **Fase 9: Anti-replay**
⏳ **Fase 10: Routing avanzado**

---

## 🚀 Comandos Disponibles

### Comandos de Usuario
- `/lista` - Escanear red local y mostrar nodos disponibles
- `/enviar archivo.txt did:ipv7:XXXX` - Enviar archivo cifrado
- `did:ipv7:XXXX:mensaje` - Enviar mensaje cifrado

### Ejecución
```bash
# Prototipo Visual
python ipv7_visual.py
# Abrir navegador en http://localhost:5000

# Prototipo Físico
python ipv7_real.py
# Seguir instrucciones para Emisor/Receptor

# Versión Autónoma
python ipv7_autonomo.py
# DID generado automáticamente, usar /lista

# Versión Experimental
python ipv7_experimental.py
# /enviar archivo.txt did:ipv7:XXXX
```

---

## 📊 Comparativa: IPv4 vs IPv6 vs IPv7

| Dimensión | IPv4 | IPv6 | IPv7 (Python) |
|-----------|------|------|---------------|
| **Direccionamiento** | 32 bits (agotado) | 128 bits (masivo) | DIDs base-12 descentralizados |
| **NAT** | Requerido (CGNAT) | Opcional | No necesario (UDP Broadcast) |
| **Cifrado** | No nativo (IPsec) | Opcional | Nativo (AES-256) |
| **Cabecera** | Variable (20-60 bytes) | Fija (40 bytes) | Mínima transparente |
| **Enrutamiento** | Centralizado (BGP) | Centralizado (BGP) | Descentralizado (Mesh) |
| **Identidad** | IP física | IP física | DID lógico |

---

## 🛠️ Stack Tecnológico (Python)

### Dependencias
```bash
pip install flask cryptography
```

### Para Empaquetado
```bash
pip install pyinstaller
```

### Librerías Utilizadas
- **Transporte**: `socket` / `asyncio` (UDP nativo)
- **Cifrado**: `cryptography.fernet` (AES-256)
- **Interfaz**: `flask` (servidor web local)
- **Threading**: `threading` (full-duplex)

---

## 🔮 Roadmap Futuro

### Prioridad Alta
- [ ] Interfaz gráfica nativa (sin web)
- [ ] Integración de audio/videollamadas
- [ ] Gateway a Internet real

### Prioridad Media
- [ ] Resolución de nombres tipo DNS
- [ ] Optimización de rendimiento
- [ ] Persistencia de mensajes

### Prioridad Baja
- [ ] Redes multicapa avanzadas
- [ ] Integración con sistemas legados
- [ ] Movilidad entre redes

---

## ⚠️ Notas de Ingeniería

### Decisiones de Diseño
- **Python sobre Rust**: Mayor velocidad de prototipado y validación visual
- **UDP sobre TCP**: Menor latencia, ideal para mensajería en tiempo real
- **Broadcast sobre Tracker**: Mayor descentralización, menos dependencias
- **Fernet sobre AES raw**: Manejo automático de nonce y seguridad

### Limitaciones Conocidas
- **Firewall Windows**: Puede bloquear conexiones UDP entrantes
- **Broadcast Limitado**: Funciona solo en red local (LAN)
- **Sin IPv6**: Implementación actual usa IPv4 subyacente
- **Escala**: No probado en redes grandes (>100 nodos)

---

## 📈 Métricas de Éxito

### Funcionales
- ✅ Chat cifrado funcional
- ✅ Transmisión de archivos working
- ✅ Retransmisión mesh operativa
- ✅ Autodescubrimiento de nodos
- ✅ Identidad permanente (DIDs)
- ✅ Escáner de red funcional

### Técnicos
- ✅ Código Python limpio y mantenible
- ✅ Sin dependencias complejas
- ✅ Ejecutable en múltiples plataformas
- ✅ Interfaz de usuario intuitiva
- ✅ Documentación completa

---

## 🎓 Lecciones Aprendidas

### Del Desarrollo Rust
- ❌ Complejidad innecesaria con Wintun
- ❌ Tiempo de compilación excesivo
- ❌ Dificultad de depuración
- ❌ Barrera de entrada alta

### Del Desarrollo Python
- ✅ Validación rápida de ideas
- ✅ Feedback visual inmediato
- ✅ Facilidad de modificación
- ✅ Prototipado ágil

---

## 🔄 Estado de Transición

**Rust** → **Python**: COMPLETADO

Justificación:
- Velocidad de desarrollo 10x mayor
- Validación visual inmediata
- Menos dependencias técnicas
- Mayor flexibilidad para experimentación

---

## 📝 Checklist de Desarrollo

- [x] Eliminar código Rust
- [x] Consolidar documentación
- [x] Validar implementación Python
- [x] Documentar arquitectura
- [x] Crear guía de uso
- [ ] Pruebas de estrés
- [ ] Optimización de rendimiento
- [ ] Interfaz gráfica nativa
- [ ] Integración audio/video
- [ ] Gateway a Internet

---

**Última revisión**: Fase 2.5 y validación A → B → C verificadas (9/9 + 5/5 PASS). **Fase 3 cerrada conceptualmente**. **Fase 4.5 cerrada conceptualmente** — Byte Freeze V1 del wire format de Container/Object: Container Header 5 bytes, Object Header 4 bytes (`TYPE|ID|LENGTH`), big endian, IDs y TYPEs reservados, LENGTH=0 válido, ejemplos hexadecimales de 10 casos, ataques al formato definidos. Ver `ARQUITECTURA_NUEVO_INTERNET.md` Sección 36, `NODE_KNOWLEDGE.md`, `FIRST_CONTACT_DESIGN.md`, `CONTACT_KNOWLEDGE_INVARIANTS.md` y `CONTAINER_OBJECT_WIREFORM_DESIGN.md`. **Próximo paso**: Fase 4.6 — Implementación experimental del encoder/decoder V1 en Python, validar con tests sin romper el baseline 9/9 + 5/5.

---

## 🧪 Lección de la prueba real (2026-08-18)

La prueba manual con dos nodos UDP reales demostró:

* ✅ UDP, `route`, `path`, `sessions`, `channels`, `PATH_MTU` funcionan.
* ❌ `ping`/`send` dependen innecesariamente de `peers`.
* ❌ `discover` actual falla por falta de `SO_BROADCAST` y apunta a puerto fijo.

La prueba A → B → C (Fase 2.5-ext, `demo_3nodes.py`) demostró:

* ✅ PATH_DISCOVER multi-salto con relay obligatorio por B.
* ✅ PATH_MTU = mínimo real de la ruta (1280 con A=1500, B=1280, C=1400).
* ✅ DATA enviado por A y recibido por C a través de B.
* ✅ SHA-256 verificado en destino final.

Conclusión: no es un bug de implementación. Es evidencia de que `peers`,
`routes`, `identity` y `availability` deben unificarse en `Node Knowledge`
antes de corregir el código.

**Principio distintivo derivado:**

> **NETWORKS LEARN, THEY DO NOT ASSUME.**
>
> Una red IPv7 no asume que `address = identity`, `silence = failure`,
> `declaration = capability`, `reachable = available` ni
> `available = permanently connected`. Ver `ARQUITECTURA_NUEVO_INTERNET.md`
> Sección 37.8.
