# IPv7 MVP - Minimum Viable Protocol

Implementación mínima funcional de IPv7 siguiendo la arquitectura:

```
CORE → PROFILES → APPLICATIONS
```

## 🚀 Ejecución Rápida

### Terminal 1:
```bash
cd ipv7_mvp
python main.py --port 9000 --mtu 1500
```

### Terminal 2:
```bash
cd ipv7_mvp
python main.py --port 9001 --mtu 1280
```

## 📋 Comandos CLI

En cada nodo puedes usar:

```
discover     - Enviar broadcast para descubrir nodos
peers        - Ver nodos conocidos y sus MTUs
path <id>    - Descubrir ruta y calcular PATH_MTU
sessions     - Ver sesiones activas y sus MTUs
ping <id>    - Hacer ping a un nodo
send <id> <msg> - Enviar mensaje a un nodo
quit         - Salir
```

## 🧪 Prueba Básica

1. **Iniciar dos nodos** con diferentes MTUs:
   ```bash
   # Terminal 1
   python main.py --port 9000 --mtu 1500
   
   # Terminal 2  
   python main.py --port 9001 --mtu 1280
   ```

2. **En el nodo 1**: `discover`
3. **En el nodo 2**: `discover` 
4. **En el nodo 1**: `peers` (debería ver al nodo 2)
5. **En el nodo 1**: `path <id_nodo_2>` (descubrir ruta y MTU)
6. **En el nodo 1**: `sessions` (ver sesiones y MTUs)
7. **En el nodo 1**: `ping <id_nodo_2>`
8. **En el nodo 1**: `send <id_nodo_2> Hola IPv7`

## 🧪 Tests

Ejecutar tests obligatorios:

```bash
python tests.py
```

Tests implementados:
- ✅ SHA-256 correcto
- ✅ Detección de corrupción
- ✅ Cálculo de PATH_MTU
- ✅ Rechazo de payload demasiado grande
- ✅ Actualización de MTU por cambio de ruta

## 🏗️ Arquitectura

### Componentes Core (sin semántica):
- **packet.py**: Estructura de paquete con SHA-256 (32 bytes)
- **object.py**: IDTLV simple (TYPE | LENGTH | ID | VALUE)
- **session.py**: Gestión de sesiones con PATH_MTU
- **node.py**: Nodo con PATH_DISCOVERY y validación de integridad
- **tests.py**: Tests obligatorios de PATH MTU + SHA-256

### Características Implementadas:
- ✅ SHA-256 para integridad (32 bytes)
- ✅ PATH_DISCOVERY para descubrir MTU de ruta
- ✅ PATH_MTU = MIN(MTU de todos los saltos)
- ✅ Validación de integridad con hmac.compare_digest
- ✅ Rechazo de paquetes corruptos
- ✅ Verificación de MTU antes de enviar
- ✅ Sessions con PATH_MTU almacenado
- ✅ PATH_CHANGED para invalidar MTU por cambio de ruta

## 📊 Formato de Paquete Actualizado

```
HEADER (18 bytes):
- version: 1 byte
- flags: 1 byte  
- source_id: 4 bytes
- dest_id: 4 bytes
- channel: 4 bytes
- session_id: 4 bytes

PAYLOAD:
- message_type: 1 byte
- data: variable

CHECKSUM (32 bytes):
- SHA-256: 32 bytes

Total: HEADER + PAYLOAD + CHECKSUM
```

## 🎯 Objetivos del MVP Actualizados

- [x] Dos nodos pueden descubrirse
- [x] PING/PONG funcional
- [x] Envío de datos básico
- [x] IDTLV encoding/decoding
- [x] Sesiones básicas
- [x] CLI funcional
- [x] SHA-256 para integridad (32 bytes)
- [x] PATH_DISCOVERY para descubrir MTU de ruta
- [x] PATH_MTU = MIN(MTU de todos los saltos)
- [x] Validación de integridad con hmac.compare_digest
- [x] Rechazo de paquetes corruptos
- [x] Verificación de MTU antes de enviar
- [x] Sessions con PATH_MTU almacenado
- [x] PATH_CHANGED para invalidar MTU por cambio de ruta

## 🔄 Roadmap de Fases

Este MVP cubre las fases iniciales:
- ✅ FASE 1: Packet
- ✅ FASE 2: Node  
- ✅ FASE 3: Discovery (básico)
- ⏳ FASE 4: Identity (básica)
- ⏳ FASE 5: Channel
- ⏳ FASE 6: Session
- ✅ FASE 7: IDTLV
- ⏳ FASE 8: Container
- ⏳ FASE 9: Profiles
- ⏳ FASE 10: Encryption

## 🛠️ Requisitos

- Python 3.7+
- Sin dependencias externas (solo librería estándar)

## 📝 Notas

Esta es una implementación mínima para demostrar que la arquitectura:
```
CHANNEL → SESSION → CONTAINER → OBJECT
```
funciona realmente sin convertirse en TCP/IP con puertos más grandes.

El Core sabe que existe un canal QUERY, pero no qué significa una consulta de temperatura. Eso es responsabilidad de los Profiles.