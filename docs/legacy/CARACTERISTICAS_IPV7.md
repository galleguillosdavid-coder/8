# 🌐 IPv7-SIMBI - Características del Sistema

## 🎯 Arquitectura Actualizada

**IPv7 no es una evolución de TCP/IP. Es una arquitectura de Internet nueva con paradigma CHANNEL → SESSION → CONTAINER → OBJECT.**

```
CORE → PROFILES → APPLICATIONS
```

## 📋 Tabla de Características por Arquitectura

### 🆕 Nueva Arquitectura (IPv7 Real)

| Categoría | Característica | Descripción | Estado | Implementación |
|-----------|---------------|-------------|---------|----------------|
| **ARQUITECTURA** | Core Structure | Core transporta estructura, no semántica | ✅ Activo | `src/core/` |
| **ARQUITECTURA** | Profile Semantics | Profiles aportan semántica específica | ⏳ Planeado | `src/profiles/` (aún no integrado al MVP) |
| **ARQUITECTURA** | Object-Oriented | Objetos → Contenedores → Objetos (no solo bytes) | 🎨 Modelo lógico en diseño (Fase 4) | Ver `CONTAINER_OBJECT_WIREFORM_DESIGN.md` |
| **ARQUITECTURA** | IDTLV | TYPE \| LENGTH \| ID \| VALUE con IDs locales | ⚠️ Heredado / candidato a revisión | `ipv7_mvp/object.py` (punto de partida; decisión final pendiente tras comparar ≥3 alternativas) |
| **ARQUITECTURA** | Container / Object Wire Format | Diseño lógico e invariantes de Container → Object: IDs locales, relaciones por Profile, objetos de conocimiento componibles, forward compatibility | 🎨 En diseño (Fase 4) | Ver `CONTAINER_OBJECT_WIREFORM_DESIGN.md` |
| **ARQUITECTURA** | Logical Channels | Canales lógicos (0=control, 1=telemetry, 2=query, 3=write, 4=emergency) | ✅ Activo e integrado | `src/core/channel_manager.py` usado por `ipv7_mvp/node.py` |
| **ARQUITECTURA** | Dynamic Sessions | Sesiones con `session_id: uint32` (compatible wire format `!I`), `remote_node_id`, `channel`, `path_mtu` | ✅ Activo e integrado | `src/core/session_manager.py` usado por `ipv7_mvp/node.py` |
| **ARQUITECTURA** | Identity Separation | Identidad ≠ Ubicación física | ⏳ Planeado | `src/core/identity.py` (aún no integrado al MVP) |
| **ARQUITECTURA** | PATH_MTU | Descubrimiento de ruta y MTU mínimo del camino, invalidación ante cambio de ruta | ✅ Activo y validado | `ipv7_mvp/node.py` (`PATH_DISCOVER`/`PATH_RESPONSE`) |
| **ARQUITECTURA** | Node Knowledge | Modelo de conocimiento progresivo del nodo: Identity, Locator, Reachability, Availability, Capabilities, Profiles, Path, Metrics; DECLARED / OBSERVED / VERIFIED | 🎨 **En diseño (Fase 3)** | Ver `NODE_KNOWLEDGE.md` y `ARQUITECTURA_NUEVO_INTERNET.md` Sección 38 |
| **ARQUITECTURA** | First Contact | Presentación/sondeo inicial progresivo para aprender sobre un nodo sin exigir verificación previa | ✅ Diseño cerrado conceptualmente (Fase 3) | Ver `NODE_KNOWLEDGE.md` |
| **ARQUITECTURA** | First Contact Design | Matriz de conocimiento, situaciones de contacto, flujo DISCOVERY → FIRST CONTACT → PATH → SESSION → KNOWLEDGE, ciclo de vida del conocimiento | ✅ Diseño cerrado conceptualmente (Fase 3) | Ver `FIRST_CONTACT_DESIGN.md` |
| **ARQUITECTURA** | Contact/Knowledge Invariants | Reglas de diseño para CONTACT, KNOWLEDGE, TRUTH, LIFETIME, PROBE que debe respetar cualquier wire format futuro | ✅ Diseño cerrado conceptualmente (Fase 3) | Ver `CONTACT_KNOWLEDGE_INVARIANTS.md` |
| **ARQUITECTURA** | Availability | `Membership`, `Presence`, `Response Capability`, `Expected Latency`, `Communication Window`, `Wake Pattern`, `Communication Mode`, declaración `AVAILABLE_FOR` por canal | ⏳ **Solo documentado** | Ver `ARQUITECTURA_NUEVO_INTERNET.md`, Sección 35. Depende de Container/Object e Identity |
| **IDENTIDAD** | DID Criptográfico | Identificadores únicos en formato `did:ipv7:XXXXXXXXXXXX` | ✅ Activo | `src/core/identity.py` |
| **IDENTIDAD** | Persistencia Local | DIDs almacenados en archivos JSON | ✅ Activo | `src/core/identity.py` |
| **IDENTIDAD** | Multi-Puerto | Soporte para múltiples identidades por puerto | ✅ Activo | `src/core/identity.py` |
| **IDENTIDAD** | Generación Automática | Creación automática de DIDs si no existen | ✅ Activo | `src/core/identity.py` |
| **TRANSPORTE** | UDP Nativo | Transporte mediante socket UDP real (no simulado) | ✅ Activo y validado multiproceso | `ipv7_mvp/node.py` (`socket.SOCK_DGRAM`) |
| **TRANSPORTE** | Packet Structure | HEADER + PAYLOAD + SHA-256 | ✅ Activo | `ipv7_mvp/packet.py` |
| **TRANSPORTE** | Channel Manager | Gestión de canales dinámicos, integrado en el MVP | ✅ Activo e integrado | `src/core/channel_manager.py` → `ipv7_mvp/node.py` |
| **TRANSPORTE** | Session Manager | Gestión de sesiones, integrado en el MVP | ✅ Activo e integrado | `src/core/session_manager.py` → `ipv7_mvp/node.py` |
| **DISCOVERY** | Query-Oriented | La red escucha más de lo que grita | ⏳ Planeado | `src/core/discovery.py` (existe pero no integrado; MVP usa DISCOVER/HERE propio) |
| **DISCOVERY** | LAN Discovery | Discovery básico en red local (DISCOVER/HERE) | ✅ Activo | `ipv7_mvp/node.py` |
| **DISCOVERY** | Route CLI | Fijar manualmente el siguiente salto (`route <dest_id> <ip> <port>`) para pruebas multiproceso | ✅ Activo | `ipv7_mvp/node.py` |
| **OBJECTS** | Object Manager | Gestión de objetos semánticos | ⏳ Solo diseño | `src/core/object_manager.py` existe, pero el wire format de Container/Object está en fase de diseño (Sección 36) antes de integrarse |
| **OBJECTS** | Local IDs | IDs locales (índices) no direcciones globales | ⏳ Solo diseño | Decisión de diseño pendiente: ¿es `ID` necesario en todos los objetos? |
| **OBJECTS** | Containers | Contenedores lógicos agrupan objetos relacionados | ⏳ Solo diseño | Formato final pendiente de comparar ≥3 alternativas de wire format |
| **PROFILES** | Sensor Profile | Semántica específica para sensores IoT | ⏳ Planeado | `src/profiles/sensor_profile.py` (existe pero no integrado al MVP) |
| **PROFILES** | Profile Evolution | Profiles pueden evolucionar sin modificar Core | ⏳ Planeado | `src/profiles/` |
| **CLI** | MVP CLI | Interfaz funcional para pruebas | ✅ Activo | `ipv7_mvp/node.py` |
| **CLI** | Comandos Básicos | discover, peers, path, sessions, channels, route, ping, send, quit | ✅ Activo | `ipv7_mvp/node.py` |
| **TESTING** | Suite Unitaria | Packet, SHA-256, PATH_MTU, ChannelManager, SessionManager Core | ✅ 9/9 PASS | `ipv7_mvp/tests.py` |
| **TESTING** | Validación Multiproceso | 4 procesos OS independientes vía UDP real (no simulación in-process) | ✅ 5/5 PASS | `ipv7_mvp/test_multiprocess.py` |
| **BUILD** | Build Unificado | Sistema de build consolidado | ✅ Activo | `build.py` |
| **CONFIG** | Constants Centralized | Constantes centralizadas en `config/constants.py` | ✅ Activo | `src/config/constants.py` |

### 🔄 Legacy (Paradigma Antiguo - Parcialmente Obsoleto)

| Categoría | Característica | Descripción | Estado | Nota |
|-----------|---------------|-------------|---------|------|
| **CIFRADO** | AES-256 (Fernet) | Cifrado simétrico para payloads | ✅ Activo | Migrando a nueva arquitectura |
| **CIFRADO** | Clave Precompartida | Sistema de clave compartida | ✅ Activo | Legacy - será reemplazado |
| **MESH** | Gossip Protocol | Protocolo de chisme para retransmisión | ✅ Activo | Legacy - necesita migración |
| **MESH** | TTL (Time-To-Live) | Sistema de TTL para evitar bucles | ✅ Activo | Legacy - necesita migración |
| **TRACKER** | Directorio Central | Sistema tracker central | ✅ Activo | Legacy - será reemplazado por discovery orientado |
| **VISUAL** | Interfaz Web Flask | Prototipo visual con interfaz web | ✅ Activo | Legacy - demo visual |
| **EMPACADO** | Ejecutables .exe | Generación de ejecutables con PyInstaller | ✅ Activo | Funcional para legacy |

## 🏗️ Arquitectura por Capas

### **Capa Core (Estructura, no semántica)**
```
src/core/
├── identity.py       → Gestión de DIDs criptográficos
├── network.py        → Transporte UDP y cifrado
├── discovery.py      → Descubrimiento orientado a objetos
├── channel_manager.py → Canales dinámicos (subports)
├── session_manager.py → Sesiones de comunicación
└── object_manager.py  → Gestión de objetos IDTLV
```

### **Capa Profiles (Semántica, no estructura)**
```
src/profiles/
├── sensor_profile.py → Semántica de sensores IoT
├── multimedia_profile.py → Semántica multimedia (próximo)
└── iot_profile.py → Semántica IoT general (próximo)
```

### **Capa MVP (Implementación mínima, integrada con Core real)**
```
ipv7_mvp/
├── packet.py            → Estructura de paquete (HEADER + PAYLOAD + SHA-256)
├── object.py            → IDTLV simple (heredado, en revisión)
├── session.py           → ⚠️ LEGACY — ya NO se usa, ver nota abajo
├── node.py              → Nodo funcional con CLI (usa src/core/session_manager.py y channel_manager.py)
├── main.py              → Punto de entrada (--port, --mtu, --node-id, --name)
├── tests.py             → Suite unitaria (9/9 PASS)
└── test_multiprocess.py → Validación con 4 procesos OS independientes (5/5 PASS)
```

> ⚠️ **`ipv7_mvp/session.py` es legacy.** `ipv7_mvp/node.py` importa
> `SessionManager`/`Session` y `ChannelManager` directamente desde
> `src/core/`, no desde este archivo. Se conserva por referencia
> histórica pero no debe recibir nuevas funcionalidades.

## 📊 Comparativa: Paradigma Antiguo vs Nuevo

| Aspecto | Paradigma Antiguo (TCP/IP) | Paradigma Nuevo (IPv7) |
|---------|---------------------------|----------------------|
| **Identificación** | IP + PORT = SERVICE | DID → OBJETO → CONTEXTO → SESIÓN |
| **Escalabilidad** | 65,536 puertos | Ilimitada (IDs locales, no globales) |
| **Semántica** | Protocolos específicos por puerto | Profiles separados del Core |
| **Objetos** | Bytes → Paquetes → Bytes | Objetos → Contenedores → Objetos |
| **Enrutamiento** | Basado en direcciones IP | Orientado a identidad/objeto/contexto |
| **Descubrimiento** | Broadcast masivo | Query/response orientado |
| **Identidad** | IP física | DID criptográfico separado de ubicación |

## 🎯 Principios Fundamentales Implementados

### **Core transporta estructura, no semántica**
- ✅ Core sabe que existe canal QUERY
- ✅ Core NO sabe qué es consulta de temperatura
- ✅ SensorProfile define semántica de consultas de temperatura

### **IDs locales, no direcciones globales**
- ✅ Object ID = índice local dentro del contenedor
- ✅ NO es DID, NO es dirección global
- ✅ Permite referencias locales sin coordinación global

### **Canales lógicos como primitiva**
- ✅ 0=control, 1=telemetry, 2=query, 3=write, 4=emergency
- ✅ Core existe canal, Profile define significado
- ✅ Registrados en `ChannelManager` real, integrado en `ipv7_mvp/node.py`

### **Object-oriented networking (en diseño)**
- ⏳ El wire format actual (`IDTLV` heredado) está en revisión antes de integrarse formalmente como `Container/Object`
- ⏳ Ver checklist de 15 preguntas de diseño y comparación de ≥3 alternativas de wire format en `ARQUITECTURA_NUEVO_INTERNET.md`, Sección 36
- ⚠️ No asumir que `TYPE | LENGTH | ID | VALUE` es la decisión final

## 📈 Métricas de Escalabilidad

### **Capacidad por Dispositivo**
```
1 dispositivo típico:
├── 1 identidad (DID permanente)
├── 10 sesiones simultáneas
├── 100 canales dinámicos
└── 1,000 objetos por sesión

Total: 1,000,000 objetos direccionables por dispositivo
```

### **Escalabilidad Global**
```
10 billones de dispositivos:
├── 10 billones de identidades
├── 100 billones de sesiones
├── 1 trillón de canales
└── 10 cuatrillones de objetos

Sin necesidad de tabla global de puertos
```

## 🚀 Roadmap de Implementación

### **Fase Actual: Core integrado y validado (Fase 2.5 cerrada)**
- ✅ Packet básico (HEADER + PAYLOAD + SHA-256)
- ✅ IDTLV simple (heredado)
- ✅ Sesiones dinámicas — ahora sobre `src/core/session_manager.py` (Core real, no legacy)
- ✅ Canales lógicos — ahora sobre `src/core/channel_manager.py` (Core real, no legacy)
- ✅ Discovery LAN básico + PATH_DISCOVER/PATH_RESPONSE/PATH_MTU
- ✅ CLI funcional (incluye `route`, `channels`, `sessions`)
- ✅ 9/9 tests unitarios PASS
- ✅ 5/5 validaciones multiproceso real (4 procesos OS independientes, UDP real) PASS
- ✅ Validación A → B → C con relay obligatorio por B y PATH_MTU real

### **Próximas Fases**
- ✅ **Fase 3: Node Knowledge + First Contact — DISEÑO CERRADO CONCEPTUALMENTE** (ver `ARQUITECTURA_NUEVO_INTERNET.md` Sección 38, `NODE_KNOWLEDGE.md`, `FIRST_CONTACT_DESIGN.md` y `CONTACT_KNOWLEDGE_INVARIANTS.md`)
  - DECLARED / OBSERVED / VERIFIED
  - Identity, Locator, Reachability, Availability, Capabilities, Profiles, Path, Metrics
  - First Contact progresivo y opt-in
  - CONTACT → OBSERVE → KNOWLEDGE → PROBE → VERIFIED
  - Observation / Measurement / Capability
  - Invariantes de CONTACT, KNOWLEDGE, TRUTH, LIFETIME, PROBE
- 🎨 **Fase 4.3: Container → Object / IDTLV — PRUEBA FORMAL A–I + INVARIANTES + PARSE/INTERPRET + RELAY/TERMINATOR** (cerrada conceptualmente, sin código todavía; debe respetar las invariantes de Fase 3)
  - Veredicto PASS para los 9 casos A–I.
  - Invariantes I-11…I-14: Unknown preservation, Unknown type ≠ invalid object, Semantic opacity, Interpretation isolation.
  - Separación Parse ≠ Interpret.
  - Distinción Relay vs. Terminator.
  - Definir candidatos byte-level A/B/C + tabla de IDs opcional.
- ✅ **Fase 4.5: Container → Object / IDTLV — BYTE FREEZE V1** (cerrada conceptualmente, sin código todavía)
  - Container Header 5 bytes, Object Header 4 bytes (`TYPE|ID|LENGTH`).
  - Big endian, IDs 0..254/255 reservado, TYPE 0/255 reservado.
  - LENGTH=0 válido.
  - Ejemplos hexadecimales de 10 casos (First Contact, Node Knowledge, Measurement, Capability, Availability, Evidence, nodo no-IPv7, nested, fragmentado, signed).
  - Ataques al formato definidos.
- 🛠️ **Fase 4.6: Container → Object / IDTLV — IMPLEMENTACIÓN EXPERIMENTAL** (siguiente prioridad)
  - Encoder/decoder V1 en Python.
  - Tests de parsing de hex dumps.
  - Validación de objetos known/unknown.
  - Integración posterior sin romper baseline 9/9 + 5/5.
- ⏳ **Fase 5: Identity integrada**
- ⏳ **Fase 6: Availability**
- ⏳ **Fase 7: Profiles**
- ⏳ **Fase 8: Security / Handshake / AEAD**
- ⏳ **Fase 9: Anti-replay**
- ⏳ **Fase 10: Routing avanzado**
- ⏳ Profiles adicionales (multimedia, IoT, industrial)
- ⏳ Discovery orientado a objetos avanzado

## 🎯 Regla de Oro

**Core transporta estructura; Profiles aportan semántica.**

Esta regla se aplica a todas las decisiones arquitectónicas de IPv7, evitando que el protocolo se convierta en un sistema monolítico como TCP/IP.

---

## 🏗️ Arquitectura por Capas

### **Capa de Identidad**
- Gestión de DIDs únicos y persistentes
- Soporte multi-puerto para múltiples instancias
- Generación automática y gestión de errores

### **Capa de Red**
- Transporte UDP optimizado
- Descubrimiento broadcast y multi-puerto
- Gestión de sockets y caché de directorios

### **Capa de Seguridad**
- Cifrado AES-256 (Fernet)
- Claves precompartidas
- Cifrado end-to-end de payloads

### **Capa de Mesh**
- Protocolo gossip para retransmisión
- Sistema TTL para evitar bucles
- Historial optimizado con deque

### **Capa de Aplicación**
- CLI con comandos intuitivos
- Interfaz web visual para demostración
- Sistema de archivos cifrados

### **Capa de Infraestructura**
- Sistema de build unificado
- Tests automatizados
- Empaquetado de ejecutables

---

## 📊 Matriz de Implementación por Fase

| Fase | Nombre | Archivo Principal | Características Clave |
|------|--------|------------------|----------------------|
| **Fase 1** | Prototipo Visual | `ipv7_visual.py` | Interfaz web, SIMBI Resolver, Sniffer visual |
| **Fase 2** | Prototipo Físico | `ipv7_real.py` | UDP real, Emisor/Receptor, Tracker integration |
| **Fase 3** | Autonomía P2P | `ipv7_autonomo.py` | DIDs automáticos, Threading, Broadcast discovery |
| **Fase 4** | Experimental | `ipv7_experimental.py` | Protocolo blobs, Archivos, Mesh, Puentes |
| **Fase 5** | Empaquetado | `build.py` | Ejecutables .exe, Optimización UPX |

---

## 🎯 Roadmap Futuro (Características Planificadas)

| Característica | Descripción | Prioridad | Estado |
|----------------|-------------|-----------|--------|
| Audio/Videollamadas | Integración de comunicación multimedia en tiempo real | Alta | 📋 Planeado |
| Gateway a Internet | Conexión segura a redes externas | Alta | 📋 Planeado |
| Resolución DNS | Sistema de nombres tipo DNS para DIDs | Media | 📋 Planeado |
| Optimización Rendimiento | Mejoras de velocidad y eficiencia | Media | 📋 Planeado |
| Interfaz Gráfica Nativa | GUI sin dependencia web | Baja | 📋 Planeado |
| Persistencia Mesh | Historial de conexiones mesh persistente | Baja | 📋 Planeado |
| Compresión de Archivos | Compresión antes de transmisión | Media | 📋 Planeado |
| Cifrado Asimétrico | Opción de cifrado asimétrico (RSA/ECC) | Alta | 📋 Planeado |

---

## 🔒 Especificaciones Técnicas

### **Protocolo IPv7**
- **Versión**: 7 (básico), 8 (experimental)
- **Transporte**: UDP/IP
- **Cifrado**: AES-256 (Fernet)
- **Identificación**: DID (Decentralized Identifier)
- **Descubrimiento**: UDP Broadcast
- **Enrutamiento**: Gossip Mesh con TTL

### **Configuración de Red**
- **Puerto Default**: 7007
- **Puertos Multiplexados**: 7007, 7008, 7009, 7010
- **Puerto Tracker**: 7000
- **Broadcast IP**: 255.255.255.255
- **TTL Default**: 3 saltos
- **Timeout Broadcast**: 2.0 segundos
- **Timeout Scan**: 1.0 segundos

### **Límites y Capacidades**
- **Tamaño Máximo Archivo**: 40KB por paquete
- **Historial Paquetes**: 1000 paquetes (deque)
- **Formato DID**: Base-12 (0-9, a, b)
- **Longitud DID**: 8 caracteres (sufijo)

---

## 🚀 Modos de Operación

### **Modo Autónomo** (`ipv7_autonomo.py`)
- Operación P2P completa sin tracker
- Descubrimiento broadcast automático
- Chat full-duplex con threading
- Identidad permanente con DIDs

### **Modo Experimental** (`ipv7_experimental.py`)
- Todas las características del modo autónomo
- Transmisión de archivos cifrados
- Mesh networking con retransmisión
- Soporte para nodos puente

### **Modo Real** (`ipv7_real.py`)
- Operación punto a punto con tracker
- Modo emisor/receptor separado
- Comunicación UDP física entre máquinas
- Integración con tracker central

### **Modo Visual** (`ipv7_visual.py`)
- Interfaz web para demostración
- SIMBI Resolver para nombres legibles
- Sniffer visual para demostrar seguridad
- Logs en tiempo real del flujo de paquetes

---

## 📝 Notas de Implementación

- **Minimalismo Extremo**: Código funcional directo sin abstracciones innecesarias
- **Cero Fricción**: Enfoque en validación rápida y prototipado visual
- **Happy Path**: Implementación del camino ideal sin código defensivo excesivo
- **Modularidad Reciente**: Refactorización reciente para mejor mantenibilidad
- **Testing Integrado**: Suite de tests para validación de componentes

---

**Última Actualización**: 2026-08-18
**Versión del Sistema**: IPv7-SIMBI v5.1 (Core integrado — Fase 2.5 cerrada)
**Estado del Proyecto**: 9/9 tests unitarios PASS + 5/5 validaciones multiproceso real PASS
**Próximo hito**: Fase 4.6 — Implementación experimental del encoder/decoder V1 en Python, tests de parsing de hex dumps y validación de objetos known/unknown (ver `CONTAINER_OBJECT_WIREFORM_DESIGN.md`).