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
│              IPv7 CORE                   │
│ Objects / Containers / Sessions          │
│ Routing / Paths / MTU / Channels         │
│ Identity / Integrity / Fragmentation     │
├──────────────────────────────────────────┤
│             DATA PLANE                   │
│ UDP / WireGuard / QUIC / DERP / etc.     │
├──────────────────────────────────────────┤
│             EXISTING NETWORK             │
│ Ethernet / Wi-Fi / 4G / 5G / Internet    │
└──────────────────────────────────────────┘
```

> **Regla de oro:** el Core conoce estructura, direccionamiento, sesión, transporte, fragmentación, integridad y control. El Profile conoce significado. La Application conoce comportamiento.

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
- [ ] Canales (`control`, `telemetry`, `query`, `write`, `emergency`) son mecanismos de transporte, no semántica.
- [ ] Definir que `channels.py` pertenece al Core como **clase de tráfico**, no como perfil.

### 2. Object / Container como unidad central

- [x] Existe `ContainerV1`/`ObjectV1` estructural.
- [ ] Documentar que IPv7 transporta **Containers compuestos por Objects**.
- [ ] Soportar múltiples Objects heterogéneos en un mismo Container:
  ```text
  Container
   ├── Object: temperatura
   ├── Object: posición
   ├── Object: estado
   ├── Object: timestamp
   └── Object: delta
  ```
- [ ] Explorar `Container` dentro de `Container` para agregación.

### 3. Object IDTLV

- [ ] Recuperar y formalizar el formato:
  ```text
  Type (1 byte)
  Length (2 bytes)
  Object ID (1 byte)
  Value
  ```
- [ ] Separar **tipo estructural**, **identificación local del objeto** y **contenido**.
- [ ] Permitir reutilizar objetos y referenciarlos por ID para deltas/compresión.

### 4. Delta objects

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

### 5. Object aggregation

- [ ] Agrupar muchos cambios pequeños en un solo Container:
  ```text
  Container
   ├─ Object A Δ
   ├─ Object B Δ
   ├─ Object C Δ
   └─ Object D Δ
  ```
- [ ] Reducir overhead de paquetes.

### 6. Schema / dictionary negotiation

- [ ] Definir negociación de esquemas entre nodos:
  ```text
  A: "¿conoces schema 37?"
  B: "sí"
  A: envía datos compactos
  ```
- [ ] Evaluar CBOR y IDs de esquema para no repetir estructuras.

### 7. Session ID + aliasing

- [ ] Usar `session_id` (uint32) en vez de repetir origen/destino.
- [ ] Comprimir identidad de sesión una vez establecida.

### 8. Seguridad separada

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

### 9. Control plane vs data plane

- [x] Firebase como control plane provisional.
- [ ] Diseñar control plane nativo IPv7 (discovery/federación) sin depender de Firebase.
- [ ] Mantener DERP/UDP/WireGuard como data plane intercambiables.

### 10. Capability discovery

- [ ] Un nodo anuncia capacidades (`chat`, `file`, `gateway`, `sensor`, ...).
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
- `channels.py` pertenece al Core como **clasificación de transporte**, no como conocimiento de la aplicación.  
- WireGuard sigue siendo el transporte cifrado; IPv7 se concentra en estructura, sesiones, objetos y perfiles.  
- Firebase RTDB es un control plane provisional. El Core no depende de Firebase.  
- SHA-256 es integridad, no autenticidad ni confidencialidad.
