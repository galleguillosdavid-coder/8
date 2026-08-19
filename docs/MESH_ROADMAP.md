# IPv7 — Mesh / VPN Roadmap y Checklist

> Fecha: 2026-08-19  
> Estado: **IPv7 Mesh v0.1 funcional**. Fases 1-5 implementadas y probadas localmente.  
> Alcance actual: transporte estructural sobre UDP/WireGuard/DERP con descubrimiento, DIDs, canales y PATH_MTU.

---

## Arquitectura objetivo

```text
┌──────────────────────────────────────────┐
│             APPLICATIONS                 │
│       Chat / Files / Media / IoT         │
├──────────────────────────────────────────┤
│                PROFILES                  │
│ Chat / File / Media / Sensor / Gateway   │
├──────────────────────────────────────────┤
│                  IPv7 CORE               │
│                                          │
│ Identity                                  │
│ Session                                   │
│ Container                                 │
│ Object / IDTLV                            │
│ Sequence / Object Version                 │
│ Fragmentation                             │
│ Integrity                                 │
│ Path / MTU / Multipath                    │
│ Channel / Priority / Reliability          │
│ TTL / Ordering                            │
│                                          │
│       ← SIN conocimiento semántico       │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│             DATA PLANE                   │
│ UDP / WireGuard / QUIC / DERP / etc.     │
├──────────────────────────────────────────┤
│             EXISTING NETWORK             │
│ Ethernet / Wi-Fi / 4G / 5G / Internet    │
└──────────────────────────────────────────┘
```

> **Regla de oro:** el Core conoce estructura, direccionamiento, sesión, transporte, fragmentación, integridad y control. El Profile conoce significado. La Application conoce comportamiento. El Data Plane es intercambiable.

---

## IPv7 Core Specification v0.1 (línea base)

> Especificación mínima que debe congelarse antes de agregar nuevos perfiles. El ADN de IPv7.

1. **Container** — unidad estructural de transporte. Contiene metadatos comunes y uno o más Objects.
2. **Object / IDTLV** — `Type | Length | Object ID | Value`.
   - `Type` = estructural.
   - `Length` = bytes de `Object ID + Value`.
   - `Object ID` = identifica la instancia **dentro de la Session** (no del Container). Permite reutilizar y actualizar el mismo objeto en múltiples Containers.
   - `Object ID` de 1 byte es suficiente para v0.1 (256 IDs por sesión). Se puede extender en versiones futuras.
3. **Object Type vs Object ID** — `Type` describe la estructura; `Object ID` identifica el objeto concreto dentro de la sesión. Son distintos.
4. **Object version** — versión lógica del estado de un objeto. Está vinculada al `Object ID`, no al Container. Permite detectar deltas obsoletos y reordenar actualizaciones.
5. **Container sequence** — orden de transporte del Container **dentro de una Session**. Detecta pérdida y reordenamiento de Containers, no de estados.
6. **Session** — contexto persistente identificado por `session_id` con origen/destino comprimido (aliasing). Cada sesión tiene su propio espacio de `Object IDs`, `Container sequence` y `Object versions`.
7. **Identity** — DID derivado de clave pública, separado de endpoint/location.
8. **Integrity** — hash estructural (SHA-256) sobre el Container. No es autenticación ni confidencialidad.
9. **Path / MTU / Multipath** — descubrimiento de caminos, identificadores de path, métricas y MTU.
10. **Container schema / profile reference** — el Container transporta un `schema_id` o `profile_id` opaco. El Profile interpreta el esquema; el Core solo lo transporta.
11. **Channel / Priority / Reliability** — clasificación de entrega/transporte. El Core transporta `channel_id`, `priority`, `reliability` sin saber el significado.
12. **Fragmentation** — un Container puede dividirse en fragmentos con `container_id`, `fragment_id`, `fragment_count`. Los fragmentos no son Objects independientes.
13. **TTL / timestamp / ordering** — expiración para discovery, paths, mensajes y estados.
14. **Intent / propósito opaco** — `intent_id` numérico opaco para el Core; el Profile lo mapea a significado.
15. **ACK opcional** — `ACK_CONTAINER`, `ACK_OBJECT`, `NO_ACK` son primitivas transportadas por el Core; el Profile decide cuándo usarlas.
16. **Delta objects** — actualización parcial de un objeto existente sin retransmitir el estado completo.
17. **Snapshot / resync** — recuperación de estado completo cuando un receptor pierde deltas.

> **Esta especificación del Core está congelada para v0.1.** No se agregan más conceptos al Core. El siguiente paso es convertir estos 17 elementos en un wire format binario concreto.

---

## Resumen de lo implementado

### Core del mesh (`experimental/mesh/`)

- `tracker.py` — control plane provisional en Firebase (STUN, publicación, descubrimiento).
- `derp_relay.py` — relay DERP-like con TLS.
- `derp_client.py` — cliente DERP con TLS.
- `mesh_chat.py` — chat CLI sobre DERP.
- `magic_socket.py` — UDP directo + fallback DERP, PATH_MTU, nonce/anti-duplicado.
- `magic_chat.py` — chat CLI con MagicSocket.
- `magic_chat_web.py` — MagicChat para la web UI.
- `packet_v1.py` — wrapper de integridad SHA-256 sobre ContainerV1.
- `channels.py` — canales lógicos del Core (control, write, etc.).
- `cert_utils.py` — certificado autofirmado para TLS.

### Web UI

- `web_ui.py` soporta modo `--mesh` con tracker, DERP, chat, archivos y lista `/peers`.

### Transporte IPv7

- `ContainerV1`/`ObjectV1` estructural en `experimental/container_v1.py`.
- SHA-256 como objeto adicional de integridad del paquete.
- PATH_DISCOVER / PATH_RESPONSE para negociar `PATH_MTU`.
- Canales lógicos insertados como objeto de control en cada mensaje.

### Identidad

- `MagicChat` genera `did:ipv7:<clave publica>` por nodo.
- El DERP se registra y envía por DID.
- El tracker resuelve `label -> DID`.

### Pruebas que pasaron

```text
OK: DERP relay funciona
[n1] <- n2: hola n1
[a] <- b: hola a
PATH_MTU = 1280
{"type": "chat", "text": "hola b con DID y SHA"}
```

---

## Principios arquitectónicos a materializar

> Estos principios deben estar **documentados y, cuando sea posible, implementados**. Algunos no pueden materializarse completamente en v0.1 por falta de infraestructura; se marcan con *(documentar / futuro)*.

### 1. Core absolutamente agnóstico

- [x] Primer separación `Core → Profiles → Applications`.
- [ ] Formalizar regla: Core no conoce "chat", "archivo", "video", "sensor".
- [ ] Canales (`control`, `telemetry`, `query`, `write`, `emergency`) son **clasificación de entrega/transporte**, no semántica.
- [ ] Definir que `channels.py` pertenece al Core como **clase de tráfico**, no como perfil.

### 2. Object / Container como unidad central

- [x] Existe `ContainerV1`/`ObjectV1` estructural.
- [ ] Documentar que un Container es una **unidad estructural de transporte** con metadatos comunes y uno o más Objects.
- [ ] Soportar múltiples Objects heterogéneos en un mismo Container:
  ```text
  Container
   ├── Header/context
   ├── Object: temperatura
   ├── Object: posición
   ├── Object: estado
   ├── Object: timestamp
   ├── Object: delta
   └── Integrity
  ```
- [ ] Explorar `Container` dentro de `Container` para agregación.

### 3. Object IDTLV

- [ ] Recuperar y formalizar el formato:
  ```text
  Type (1 byte)
  Length (2 bytes)     # bytes de Object ID + Value
  Object ID (1 byte)   # ámbito = Session (256 IDs por sesión para v0.1)
  Value
  ```
- [ ] `Length` cubre `Object ID + Value` para permitir saltar el Object completo de forma determinista.
- [ ] `Object ID` es **local a la Session**, no al Container. Permite reutilizar y actualizar el mismo objeto en múltiples Containers.
- [ ] Separar **tipo estructural**, **identificación local del objeto** y **contenido**.
- [ ] Permitir reutilizar objetos y referenciarlos por ID para deltas/compresión.

### 4. Type ≠ Object ID

- [ ] `Type` describe la estructura; `Object ID` identifica la instancia.
- [ ] Ejemplo:
  ```text
  Type = TEMPERATURE
  Object ID = 04
  Value = 23.7
  ```
- [ ] Deltas referencian el `Object ID` sin volver a describir todo el objeto:
  ```text
  Object 04 → Δ +0.2
  ```

### 5. Versionado de Objects y Profiles

- [ ] Agregar `version` al Object:
  ```text
  Object:
    type
    version
    object_id
    length
    value
  ```
- [ ] Agregar versionado a Profiles:
  ```text
  Profile:
    profile_id
    version
    schema_id
  ```
- [ ] Ejemplos: `chat.v1`, `chat.v2`, `file.v1`, `media.v1`.

### 6. Container sequence vs Object version

- [ ] Tres dimensiones separadas:
  ```text
  session_id
  sequence         # Container sequence dentro de la Session
  object_id
  object_version   # estado lógico del objeto
  ```
- [ ] `Container sequence` = orden de transporte del Container dentro de una Session.
- [ ] `Object version` = estado lógico del objeto, vinculado al `Object ID`.
- [ ] No son lo mismo. Se usan para detectar pérdida, reordenamiento y deltas obsoletos.

### 7. Delta objects

- [ ] Diseñar modelo de actualización por delta:
  ```text
  Estado inicial
        ↓
  Objeto
        ↓
  Δ
        ↓
  Δ
  ```
- [ ] Aplicar a sensores, video, audio y sincronización.
- [ ] No es compresión; es un modelo de estado.

### 8. Object aggregation

- [ ] Agrupar muchos cambios pequeños en un solo Container:
  ```text
  Container
   ├─ Object A Δ
   ├─ Object B Δ
   ├─ Object C Δ
   └─ Object D Δ
  ```
- [ ] Reducir overhead de paquetes.

### 9. Snapshot / resync

- [ ] Mecanismo de recuperación de estado completo cuando un receptor pierde deltas.
- [ ] Ejemplo:
  ```text
  A → B: Δ83
  B → A: falta estado 81
  A → B: SNAPSHOT
  ```
- [ ] Especialmente importante en multimedia y sensores.

### 10. Object como entidad persistente

- [ ] Un Object puede representar una entidad que permanece durante una sesión.
- [ ] Ejemplo:
  ```text
  Object ID 15
    tipo = vehicle
    estado = ...
  Container 101 → Object 15 Δ
  Container 102 → Object 15 Δ
  Container 103 → Object 15 Δ
  ```
- [ ] Esto diferencia a IPv7 de IP: transporta actualizaciones de entidades, no solo paquetes aislados.

### 11. Container schema / profile reference

- [ ] El Container transporta un `schema_id` o `profile_id` opaco.
- [ ] Ejemplo de metadatos comunes del Container:
  ```text
  schema_id / profile_id
  session_id
  container_sequence
  channel_id
  priority
  reliability
  ttl
  ```
- [ ] El Profile interpreta el esquema; el Core solo lo transporta.
- [ ] Esto desacopla estructura de semántica y permite negociación de esquemas.

### 13. Schema / dictionary negotiation

- [ ] Definir negociación de esquemas entre nodos:
  ```text
  A: "¿conoces schema 37?"
  B: "sí"
  A: envía datos compactos
  ```
- [ ] Evaluar CBOR y IDs de esquema para no repetir estructuras.
- [ ] Conectar con versionado de Profiles.

### 14. Session ID + aliasing

- [ ] Usar `session_id` (uint32) en vez de repetir origen/destino.
- [ ] Comprimir identidad de sesión una vez establecida.

### 15. Seguridad separada

- [x] SHA-256 como integridad de paquete.
- [ ] Agregar firma / autenticidad del DID.
- [ ] Confidencialidad por WireGuard/AEAD.
- [ ] Anti-replay (sequence + timestamp + ventana).
- [ ] Documentar:
  ```text
  Integridad    → SHA-256
  Autenticidad  → firma / DID
  Confidencialidad → WireGuard / AEAD
  Anti-replay   → sequence + timestamp
  ```

### 16. Transporte agnóstico

- [ ] El Core no depende de un único transporte físico.
- [ ] Puede funcionar sobre UDP, WireGuard, QUIC, DERP, LAN, Internet y transportes futuros.
- [ ] `MagicSocket` debe poderse adaptar a nuevos data planes sin cambiar `ContainerV1`.

### 17. Control plane vs data plane

- [x] Firebase como control plane provisional.
- [ ] Diseñar control plane nativo IPv7 (discovery/federación) sin depender de Firebase.
- [ ] Mantener DERP/UDP/WireGuard como data plane intercambiables.

### 18. Path identity

- [ ] Cuando haya multipath, identificar caminos con `PATH_ID`.
- [ ] Asociar métricas por path:
  ```text
  PATH_ID
  MTU
  latency
  loss
  capacity
  state
  ```

### 19. Fragmentación

- [ ] Un Container se divide en fragmentos con:
  ```text
  container_id
  fragment_id
  fragment_count
  offset
  ```
- [ ] Los fragmentos pertenecen al Container, no son Objects independientes.
- [ ] No contaminan la semántica.

### 20. TTL / expiración

- [ ] TTL para discovery, paths, mensajes y estados.
- [ ] Evitar que información vieja permanezca indefinidamente.

### 21. ACK opcional

- [ ] Tres niveles: `ACK_CONTAINER`, `ACK_OBJECT`, `NO_ACK`.
- [ ] Algunos perfiles no necesitan ACK (telemetry); otros sí (file, control).
- [ ] El Core transporta el mecanismo; el Profile decide.

### 22. Profile vs Capability

- [ ] **Profile** = "sé interpretar este protocolo/semántica" (`chat.v1`, `file.v1`, `media.v1`).
- [ ] **Capability** = "puedo realizar esta función" (`INTERNET_GATEWAY`, `STORAGE`, `RELAY`).
- [ ] Un nodo puede soportar `file.v1` sin tener `STORAGE`.
- [ ] Un nodo puede tener `INTERNET_GATEWAY` sin ser un Profile de aplicación.
- [ ] Jerarquía:
  ```text
  Identity
      ↓
  Profile support
      ↓
  Capabilities
      ↓
  Selection
  ```

### 23. Capability discovery

- [ ] Un nodo anuncia sus Profiles y Capabilities en el tracker/control plane.
- [ ] Otro nodo puede descubrir y seleccionar un gateway u otro servicio.
- [ ] Distinguir **quién eres** (identidad) de **qué puedes hacer** (capacidad).

---

## Faltantes operativos ordenados por etapa

### 🔴 Etapa actual / cierre de v0.1

> Lo que bloquea llamar a IPv7 Mesh "funcional sin asteriscos".

1. **MagicSocket sin duplicados**  
   - [x] Agregar nonce y deduplicación en receptor.  
   - [ ] Validar en pruebas y quitar debug prints.

2. **MTU/fragmentación correcta**  
   - [ ] `MagicChat.send_file()` valida tamaño contra `PATH_MTU`.  
   - [ ] Si un paquete supera MTU, fragmentar o forzar DERP.  
   - [ ] No perder mensajes cuando `direct_confirmed` es True y UDP falla.

3. **Autenticidad real del nodo/DID**  
   - [ ] Firmar `Container` con clave privada.  
   - [ ] Verificar firma con `public_b64` del tracker.  
   - [ ] `did:ipv7:<public_b64>` debe ser verificable criptográficamente.

4. **Prueba entre dos PCs en redes distintas**  
   - [ ] Preparar instrucciones y scripts.  
   - [ ] Ejecutar validación real con NAT distinto.  
   - [ ] Confirmar DERP fallback cuando UDP directo falla.

### 🟠 Etapa siguiente / v0.2

> Funcionalidad de red avanzada; requiere que v0.1 esté estable.

1. **Multipath real**
   - [ ] No solo fallback; usar varios paths simultáneamente.
   - [ ] Distribuir fragmentos por UDP, DERP, WireGuard según latencia/pérdida.

2. **DERP multi-relay y federación**
   - [ ] Descubrir múltiples relays.
   - [ ] Failover entre relays.
   - [ ] Forwarding relay-to-relay.

3. **WireGuard como data plane**
   - [ ] Enviar/recibir tráfico IPv7 por túnel WireGuard.
   - [ ] Integrar `wintun` o similar.
   - [ ] Mantener IPv7 como estructura sobre el cifrado existente.

4. **Gateway automático y capability selection**
   - [ ] Anunciar `INTERNET_GATEWAY` en tracker.
   - [ ] Seleccionar gateway automáticamente.
   - [ ] Evitar loops.

5. **QoS / prioridad estructural**
   - [ ] Elige canal + prioridad sin saber el significado.
   - [ ] `control` y `emergency` deben poder tener precedencia.

6. **Trust / reputation engine**
   - [ ] Separar identidad de confianza.
   - [ ] Trust score, endorsements, anchors, `MIN_TRUST`, whitelists.
   - [ ] No es Core; es Profile.

### 🔵 Investigación futura / laboratorio

> No tocar hasta tener v0.1/v0.2 estable. Son ideas experimentales que no deben contaminar el Core.

1. **Red esférica / clave esférica**
   - [ ] Topología geométrica.
   - [ ] Distribución de potencia de transmisión.
   - [ ] "Internet como lluvia" de conectividad.

2. **Routing semántico / contextual**
   - [ ] Buscar nodo por capacidad/servicio/objeto.
   - [ ] Viven en Profiles, no en Core.

3. **Nodos especializados**
   - [ ] auditor, anchor, storage, compute, discovery.

4. **Plugin architecture**
   - [ ] Extensión del Core/Profiles mediante plugins.

---

## Checklist de prioridades sugeridas

- [ ] Limpiar debug prints de `magic_socket.py` y `magic_chat_web.py`.
- [ ] Validar que no haya duplicados en chat/file/PATH.
- [ ] Verificar MTU en send y corregir pérdida de mensajes.
- [ ] Agregar firma DID al Container.
- [ ] Probar dos PCs (validación real).
- [ ] Integrar WireGuard como data plane.
- [ ] Gateway automático con capability discovery.
- [ ] Multipath y multi-relay.
- [ ] Trust / reputation.
- [ ] Multimedia y perfiles formales.

---

## Notas

- El Core transporta estructura; Profiles aportan semántica; Applications deciden comportamiento.  
- `channels.py` pertenece al Core como **clasificación de entrega/transporte**, no como conocimiento de la aplicación.  
- IPv7 Core no depende de un único transporte físico: UDP, WireGuard, QUIC, DERP, LAN, Internet y futuros transportes son data planes.  
- WireGuard sigue siendo el transporte cifrado; IPv7 se concentra en estructura, sesiones, objetos y perfiles.  
- Firebase RTDB es un control plane provisional. El Core no depende de Firebase.  
- SHA-256 es integridad, no autenticidad ni confidencialidad.  
- `Type` ≠ `Object ID`: `Type` es estructura, `Object ID` es instancia local.  
- `Container sequence` ≠ `Object version`: una es transporte, la otra es estado.  
- Un Container es una unidad de transporte con metadatos comunes y múltiples Objects, con integridad propia.
