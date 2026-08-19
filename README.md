# IPv7-SIMBI - Nuevo Protocolo de Internet

**IPv7 no es una evolución de IPv4/IPv6. Es una arquitectura de Internet nueva que explora paradigmas diferentes de comunicación.**

## 🎯 Principio Fundamental

> **El Core debe transportar estructura, no imponer semántica.**

```
CORE → PROFILES → APPLICATIONS
```

- **Core**: Primitivas universales (identidad, transporte, sesiones, canales, objetos)
- **Profiles**: Semántica específica (sensores, multimedia, IoT, vehículos, etc.)
- **Applications**: Usan Profiles y primitivas del Core

## Estado del Proyecto

✅ **Arquitectura Definida** - Principios fundamentales establecidos y documentados

✅ **MVP Funcional** - Implementación mínima en Python que demuestra la arquitectura

✅ **Refactorización Completada** - Código simplificado y modularizado

❌ **Implementación Rust ELIMINADA** - Se eliminó por complejidad innecesaria

## 🚀 Arquitectura Revolucionaria

### ❌ NO es TCP/IP con puertos más grandes
```
IP + PORT = SERVICE (paradigma antiguo)
```

### ✅ SÍ es CHANNEL → SESSION → CONTAINER → OBJECT
```
Identidad → Objeto/Servicio → Contexto → Sesión
did:ipv7:ABC...
    └── servicio
         ├── tipo: sensor
         ├── objeto: temperatura
         ├── versión: 3
         └── contexto: edificio/2/piso/4
```

## 🌐 Características Implementadas

### Implementación MVP (ipv7_mvp/)
- **Protocolo mínimo funcional** que demuestra la arquitectura
- Packet básico con HEADER + PAYLOAD
- IDTLV (TYPE | LENGTH | ID | VALUE) para objetos
- Sesiones dinámicas con IDs aleatorios
- Canales lógicos (0=control, 1=telemetry, 2=query, 3=write, 4=emergency)
- Discovery LAN básico
- CLI funcional para pruebas

### Implementaciones Anteriores (src/implementations/)
Estas implementaciones fueron los prototipos iniciales que llevaron a la arquitectura actual:

- **ipv7_visual.py**: Prototipo visual con interfaz web Flask
- **ipv7_real.py**: Prototipo físico UDP punto a punto  
- **ipv7_autonomo.py**: Versión autónoma P2P con DIDs
- **ipv7_experimental.py**: Versión experimental con archivos y mesh
- **tracker.py**: Sistema de tracking central

**Nota**: Estas implementaciones usan el paradigma antiguo de puertos y están siendo migradas a la nueva arquitectura.

## 🏗️ Arquitectura IPv7

### Core (Estructura, no semántica)
```
src/core/
├── identity.py       → Gestión de DIDs criptográficos
├── network.py        → Transporte UDP y cifrado
├── discovery.py      → Descubrimiento de red
├── channel_manager.py → Canales dinámicos (subports)
├── session_manager.py → Sesiones de comunicación
└── object_manager.py  → Gestión de objetos IDTLV
```

### Profiles (Semántica, no estructura)
```
src/profiles/
├── sensor_profile.py → Semántica de sensores IoT
├── multimedia_profile.py → Semántica multimedia (próximo)
└── iot_profile.py → Semántica IoT general (próximo)
```

### MVP (Implementación mínima)
```
ipv7_mvp/
├── packet.py        → Estructura de paquete básica
├── object.py        → IDTLV simple
├── session.py       → Sesiones básicas
├── node.py          → Nodo funcional con CLI
└── main.py          → Punto de entrada
```

### Principios Arquitectónicos
- **Object-oriented networking**: `objetos → contenedores → objetos` (no solo bytes)
- **IDTLV**: `TYPE | LENGTH | ID | VALUE` con IDs locales (no direcciones globales)
- **Subports**: Canales lógicos (0=control, 1=telemetry, 2=query, etc.)
- **Sessions**: Comunicación dinámica con OPEN/DATA/CLOSE
- **Identity**: DID criptográfico separado de ubicación física

## 📁 Estructura del Proyecto

```
README.md                      - Documentación principal

ipv7_mvp/                      - MVP funcional (NUEVA ARQUITECTURA)
├── main.py                    - Punto de entrada
├── node.py                    - Nodo con CLI
├── packet.py                  - Estructura de paquete
├── object.py                  - IDTLV simple
├── session.py                 - Gestión de sesiones
└── README.md                  - Instrucciones del MVP

src/
├── core/                      - Core del sistema (NUEVA ARQUITECTURA)
│   ├── identity.py            - Gestión de DIDs
│   ├── network.py             - Transporte y cifrado
│   ├── discovery.py           - Descubrimiento de red
│   ├── channel_manager.py     - Canales dinámicos
│   ├── session_manager.py     - Sesiones de comunicación
│   └── object_manager.py      - Gestión de objetos IDTLV
├── profiles/                  - Profiles con semántica
│   ├── sensor_profile.py      - Semántica de sensores
│   └── __init__.py
├── config/                    - Configuración centralizada
│   └── constants.py           - Constantes del sistema
└── implementations/           - Implementaciones anteriores (legacy)
    ├── ipv7_visual.py         - Prototipo visual
    ├── ipv7_real.py           - Prototipo físico
    ├── ipv7_autonomo.py       - Versión autónoma
    ├── ipv7_experimental.py   - Versión experimental
    └── tracker.py             - Sistema de tracking

docs/                          - Documentación arquitectónica
├── ARQUITECTURA_CANAL_SESION_OBJETO.md - Nueva arquitectura
├── ARQUITECTURA_NUEVO_INTERNET.md - Visión del nuevo internet
├── PROTOCOLO_IPV7_TRANSPORT.md - Especificación de transporte
├── SISTEMA_PUERTOS_VIRTUALES.md - Sistema de puertos virtuales
└── CARACTERISTICAS_IPV7.md - Características detalladas

build.py                       - Sistema de build unificado
```

## 🚀 Instalación y Uso

### MVP (Nueva Arquitectura - Recomendado)
```bash
cd ipv7_mvp
python main.py --port 9000
```

**Comandos CLI:**
- `discover` - Enviar broadcast para descubrir nodos
- `peers` - Ver nodos conocidos
- `ping <node_id>` - Hacer ping a un nodo
- `send <node_id> <message>` - Enviar mensaje a un nodo
- `quit` - Salir

### Implementaciones Legacy (Paradigma Antiguo)
Estas implementaciones usan el paradigma de puertos y están siendo migradas:

```bash
# Prototipo Visual
python src/implementations/ipv7_visual.py

# Prototipo Físico
python src/implementations/ipv7_real.py

# Versión Autónoma
python src/implementations/ipv7_autonomo.py

# Versión Experimental
python src/implementations/ipv7_experimental.py
```

## 🛠️ Requisitos

### MVP (Sin dependencias externas)
- Python 3.7+
- Solo librería estándar: `socket`, `struct`, `threading`, `secrets`, `dataclasses`

### Implementaciones Legacy
```bash
pip install flask cryptography
```

### Para empaquetar ejecutables
```bash
pip install pyinstaller
```

## 📚 Documentación

- `docs/ARQUITECTURA_CANAL_SESION_OBJETO.md` - Nueva arquitectura (recomendado)
- `docs/ARQUITECTURA_NUEVO_INTERNET.md` - Visión del nuevo internet
- `docs/CARACTERISTICAS_IPV7.md` - Características detalladas actualizadas
- `docs/DESARROLLO_CHECK.md` - Check de desarrollo actualizado
- `docs/PROTOCOLO_IPV7_TRANSPORT.md` - Propuesta anterior (superada)
- `docs/SISTEMA_PUERTOS_VIRTUALES.md` - Propuesta anterior (superada)

## 🎯 Filosofía de Desarrollo

**Core transporta estructura; Profiles aportan semántica.**

- **Minimalismo Extremo**: Código funcional directo sin abstracciones innecesarias
- **Python Simple**: Solo librería estándar donde sea posible
- **Funcionalidad Primero**: Demostrar que funciona antes de optimizar
- **Sin Sobreingeniería**: No crear frameworks para problemas hipotéticos

## 🔄 Estado de Transición

**Paradigma Antiguo (Puertos) → Paradigma Nuevo (Canal/Sesión/Objeto)**

- ✅ Arquitectura definida y documentada
- ✅ MVP funcional implementado
- ✅ Core refactorizado creado
- ⏳ Migración de implementaciones legacy
- ⏳ Integración completa de nueva arquitectura

## Pruebas

El proyecto incluye varios scripts de prueba:
- `test_loop.py` - Pruebas de bucle local
- `test_archivo.py` - Pruebas de transmisión de archivos
- `test_mesh_sender.py` - Pruebas de retransmisión mesh
- `test_swarm.py` - Pruebas de enjambre de nodos

## Documentación

- `docs/DESARROLLO_CHECK.md` - Check de desarrollo consolidado (visión, arquitectura, estado actual)

## Roadmap Futuro

- [ ] Integración de audio/videollamadas
- [ ] Gateway a Internet real
- [ ] Resolución de nombres tipo DNS
- [ ] Optimización de rendimiento
- [ ] Interfaz gráfica nativa (sin web)

## Filosofía de Desarrollo

**Minimalismo Extremo**: Código funcional directo sin abstracciones innecesarias.

**Cero Fricción**: Enfoque en validación rápida y prototipado visual antes de industrializar.

**Happy Path**: Implementación del camino ideal sin código defensivo excesivo.

## Licencia

Proyecto de investigación y desarrollo de redes alternativas.

## Autores

IPv7-SIMBI Team
