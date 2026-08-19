# IPv7 Core Wire Format v0.1

> Fecha: 2026-08-19  
> Estado: Borrador de especificación para congelación.  
> Alcance: estructura binaria mínima del Core IPv7, independiente de aplicación, perfil y transporte.

---

## Objetivo

Definir un wire format concreto, binario y versionado para el **Core IPv7 v0.1**.  
El Core transporta estructura, no semántica. Perfiles y aplicaciones se construyen encima.  
El transporte inferior es intercambiable.

---

## Reglas arquitectónicas fijas

1. **Object ID es de ámbito de Session, no de Container.**  
   - Permite referenciar y actualizar el mismo objeto en múltiples Containers.
   - v0.1: `Object ID` de 1 byte (256 IDs por sesión).

2. **Container sequence pertenece al Container.**  
   - Ordena el transporte de Containers dentro de una Session.

3. **object_version pertenece al Object.**  
   - Indica el estado lógico del objeto identificado por `Object ID`.

4. **Type ≠ Object ID.**  
   - `Type` describe la estructura (qué tipo de valor se transporta).  
   - `Object ID` identifica la instancia del objeto dentro de la sesión.

5. **Length = bytes de Object ID + Value.**  
   - Permite saltar un Object completo de forma determinista sin parsear su valor.

6. **Los fragments pertenecen al Container, no son Objects.**  
   - Un Container fragmentado se transporta en varios mensajes, cada uno con `fragment_id`.

7. **schema_id tiene una ubicación formal en el Container Header.**  
   - El Core lo transporta opacamente; el Profile lo interpreta.

8. **Profile y Capability son conceptos distintos.**  
   - `Profile`: protocolo/semántica soportada (`chat.v1`, `file.v1`).  
   - `Capability`: función que el nodo puede ofrecer (`INTERNET_GATEWAY`, `STORAGE`).

9. **El Core no interpreta chat, file, media, sensor, etc.**  
   - Solo transporta estructura.

10. **El transporte inferior es intercambiable.**  
    - UDP, WireGuard, QUIC, DERP, LAN, Internet, futuros transportes.

11. **Integridad, autenticidad, confidencialidad y anti-replay son mecanismos distintos.**  
    - Integridad: hash estructural (SHA-256).  
    - Autenticidad: firma / DID.  
    - Confidencialidad: WireGuard / AEAD.  
    - Anti-replay: sequence + timestamp + ventana.

12. **Los deltas representan cambios de estado, no simplemente compresión.**  
    - `Object ID 03` puede recibir `Δ +0.2` actualizando su versión lógica.

---

## Estructura general del mensaje IPv7

```text
┌────────────────────────────────────────────────────────────┐
│                  IPv7 Core Message                         │
├────────────────────────────────────────────────────────────┤
│  Container                                                 │
│    ├── Fixed Header (12+ bytes)                            │
│    ├── Optional Extension Header (variable)                │
│    ├── Objects[]                                           │
│    └── Container Integrity / Auth Trailer                  │
├────────────────────────────────────────────────────────────┤
│  Fragment Header (only when fragmented)                    │
│    ├── container_id                                        │
│    ├── fragment_id                                         │
│    └── fragment_count                                      │
├────────────────────────────────────────────────────────────┤
│  Data Plane Wrapper (depende del transporte)               │
│    └── nonce / path / channel / etc.                       │
└────────────────────────────────────────────────────────────┘
```

> El Container es la unidad de estructura.  
> El Data Plane Wrapper es mecanismo de transporte, no parte del Container.

---

## Fixed Header

| Campo            | Tamaño   | Descripción                                                |
|------------------|----------|------------------------------------------------------------|
| `version`        | 1 byte   | Versión del Core. `0x01` para v0.1.                        |
| `flags`          | 1 byte   | Flags generales del Container (fragmented, ack, etc.).     |
| `session_id`     | 4 bytes  | Identificador de sesión.                                   |
| `container_seq`  | 4 bytes  | Número de secuencia del Container dentro de la sesión.     |
| `schema_id`      | 2 bytes  | Referencia de esquema/perfil opaca.                       |
| `ttl`            | 1 byte   | Tiempo de vida del Container en saltos/segundos.          |
| `object_count`   | 1 byte   | Cantidad de Objects en el Container.                       |
| `payload_len`    | 2 bytes  | Longitud en bytes de la sección de Objects.                |

**Tamaño mínimo del Fixed Header:** `16 bytes`.

```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| version       | flags         |           session_id            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       container_seq                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           schema_id           | ttl           | object_count  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           payload_len         |                                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

> **Nota:** todos los campos multibyte son big-endian.

---

## Objects (IDTLV)

Cada Object dentro del Container sigue el formato:

```text
Type (1 byte)
Length (2 bytes)     # bytes de Object ID + Value
Object ID (1 byte)   # ámbito de Session
Value (N bytes)
```

| Campo       | Tamaño   | Descripción                                       |
|-------------|----------|---------------------------------------------------|
| `type`      | 1 byte   | Tipo estructural del valor.                       |
| `length`    | 2 bytes  | Longitud de `Object ID + Value`.                  |
| `object_id` | 1 byte   | ID del objeto dentro de la sesión.                |
| `value`     | N bytes  | Valor opaco. Interpretado por el Profile.         |

### Reglas de Object

- `object_id` se asigna por sesión.  
  Ejemplo: `Object 03` puede representar una temperatura que dura toda la sesión.
- `object_version` no viaja en el Object IDTLV básico; se transporta como un Object de control adicional o como extensión del Value.
- Un `Container` puede contener hasta `255` Objects.
- El parser Core puede saltar cualquier Object sin conocer su significado.

---

## Fragmentación

Un Container que supere el `PATH_MTU` se divide en fragmentos:

```text
Fragment Header:
  container_id  (4 bytes)
  fragment_id   (1 byte)
  fragment_count (1 byte)
  offset        (2 bytes)
```

Cada fragmento contiene un subconjunto del payload del Container. El receptor reensambla antes de parsear Objects.

### Reglas

- Los fragmentos pertenecen al Container, no son Objects.
- El `container_id` identifica todos los fragmentos de un mismo Container.
- El `fragment_id` es local al Container; el `fragment_count` indica el total.
- Solo se fragmenta el `payload` del Container; el Fixed Header se repite en cada fragmento.

---

## Container Integrity / Auth Trailer

El trailer se calcula sobre **todo el Container** (header + objects). Se coloca al final del mensaje completo.

```text
Trailer:
  hash_alg      (1 byte)    # 0x01 = SHA-256
  hash          (32 bytes)  # SHA-256 del Container
  sig_alg       (1 byte)    # 0x00 = none, 0x01 = Ed25519
  signature     (variable)  # opcional
```

### Reglas

- `hash` es obligatorio: integridad estructural.
- `signature` es opcional: autenticidad del emisor.
- El hash **no** provee autenticidad. Sin firma, cualquier atacante puede recalcular el hash.
- La confidencialidad se delega al transporte inferior (WireGuard, etc.).

---

## Data Plane Wrapper

El transporte inferior añade su propio wrapper, **no forma parte del Container**.

Ejemplo para UDP/IPv7 experimental:

```text
Nonce (4 bytes)  # anti-replay / deduplicación a nivel de transporte
IPv7 Container Message
```

Ejemplo para DERP:

```text
DERP Frame:
  type
  src
  dst
  payload (IPv7 Container Message)
```

El Core no conoce el wrapper. Solo ve el Container.

---

## Session

```text
Session:
  session_id (4 bytes)
  origin (DID)
  destination (DID)
  state:
    object_id_space
    container_seq
    object_versions
    schema_negotiated
```

- La sesión comprime identidades: una vez establecida, los Containers solo llevan `session_id`.
- Cada sesión tiene su propio espacio de `Object IDs`.
- `container_seq` es por sesión.
- `object_version` es por `object_id` dentro de la sesión.

---

## Ejemplo: Container con un chat

```text
Fixed Header:
  version = 0x01
  flags = 0x00
  session_id = 0x0000002A
  container_seq = 0x00000007
  schema_id = 0x0001     # chat.v1 (opaco para el Core)
  ttl = 0x40
  object_count = 0x02
  payload_len = 0x0014

Objects:
  [0] type=0x01 (channel)   length=0x0002   object_id=0x00   value=0x03 (write)
  [1] type=0x64 (chat=100)  length=0x0010   object_id=0x01   value="hola"

Trailer:
  hash_alg = 0x01
  hash = SHA-256(container)
  sig_alg = 0x00
  signature = <none>
```

El Core transporta todo sin saber que `0x64` significa "chat" ni que `0x0001` es un esquema conversacional.

---

## Perfiles y Capabilities (fuera del wire)

El wire format del Container solo transporta `schema_id` y `object types` estructurales.  
La interpretación es responsabilidad del Profile:

```text
Profile:
  profile_id    # chat, file, media, sensor, gateway
  version       # v1, v2
  schema_id     # referencia al esquema

Capability:
  capability_id # INTERNET_GATEWAY, STORAGE, RELAY, COMPUTE
  metadata      # disponibilidad, costo, confianza
```

Un nodo anuncia soportes de Profile y Capabilities en el control plane, no en cada Container.

---

## Próximos pasos de implementación

1. Reemplazar `ContainerV1` por `IPv7Container` que implemente este wire format.
2. Implementar `IPv7Object` con IDTLV real.
3. Implementar sesiones con `session_id` y aliasing de origen/destino.
4. Implementar fragmentación de Container.
5. Implementar trailer de integridad con hash opcional y firma.
6. Adaptar `MagicChat` y `MagicSocket` para enviar/recibir el nuevo wire format.
7. Definir perfiles de ejemplo: `chat.v1`, `file.v1`.

---

## Notas

- El Core congela v0.1 aquí. No se agregan más conceptos.
- Cualquier semántica adicional (chat, file, sensor, gateway) va en Profiles.
- Cualquier transporte adicional va en Data Plane wrappers.
