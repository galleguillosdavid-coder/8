# IPv7 — Node Knowledge

> **Estado**: diseño conceptual. Sin código todavía.
> 
> `Node Knowledge` no es una primitiva del Core. Es el conocimiento que un
> nodo construye progresivamente sobre las primitivas del Core y las
> observaciones de red.

---

## 1. Principio rector

```text
IPv7 does not require trust before communication;
it progressively builds knowledge through communication.
```

Un nodo no tiene que demostrar nada para que otro nodo le hable por
primera vez. Pero a medida que interactúan, el observador construye un
modelo del otro: quién es, dónde podría estar, qué dice poder hacer,
qué realmente hace, y bajo qué condiciones puede responder.

---

## 2. Relación con el Core

```text
                  APPLICATION
                       │
                    PROFILE
                       │
              ┌────────▼────────┐
              │      CORE       │
              │                 │
              │ Identity        │
              │ Channel         │
              │ Session         │
              │ Path            │
              │ Container       │
              │ Object / IDTLV  │
              │ Security        │
              └────────┬────────┘
                       │
                 NETWORK STATE
                       │
                       ▼
                NODE KNOWLEDGE
```

Regla de diseño:

> **Core transporta estructura; Profiles y Node Knowledge interpretan.**

El Core no mantiene una tabla semántica de "qué tan rápido es este nodo"
o "cuándo puede despertar". Mantiene las primitivas mínimas (`Identity`,
`Channel`, `Session`, `Path`, `Container`, `Object`) que permiten
construir, transportar y validar ese conocimiento.

---

## 3. Tres niveles de verdad

### 3.1 Declared

Lo que el nodo dice de sí mismo.

```text
"Soporto los profiles sensor y telemetry"
"Mi MTU es 1280"
"Mi disponibilidad es scheduled"
```

* Se acepta provisionalmente.
* No es verdad absoluta.
* Es información.

### 3.2 Observed

Lo que la red mide con sus propios paquetes.

```text
RTT = 12 ms
packet loss = 0%
MTU = 1280
response time = 8 ms
session stability = normal
```

* Funciona incluso si el otro no es IPv7.
* No requiere cooperación del nodo remoto.
* Es evidencia, pero también contextual.

### 3.3 Verified

Lo que un procedimiento definido ha demostrado.

```text
CAPABILITY_PROBE
    algorithm = X
    work factor = Y
    elapsed = 37 ms
    result = accepted
```

* Es opt-in.
* Pertenece a Profile/Capability, no al Core.
* No se llama `Proof of Work`, porque el objetivo no es castigar al nodo
  por existir, sino medir capacidad cuando sea útil.

### 3.4 Tres categorías de conocimiento

No todo lo que aprendemos es del mismo tipo:

```text
KNOWLEDGE
 ├── Observation
 │     └── lo que hemos visto
 │
 ├── Measurement
 │     └── un valor cuantificado de lo observado
 │
 └── Capability
       └── una propiedad demostrada mediante una prueba
```

* **Observation**: "B respondió a un paquete.", "B usa IPv4.", "B no
  respondió durante 10 minutos."
* **Measurement**: `RTT = 12 ms`, `packet loss = 0.3 %`,
  `PATH_MTU = 1280`.
* **Capability**: resultado de un probe opt-in, como `computational
  probe = 82 units/s`.

Regla:

> **Observation describe behavior. Measurement quantifies it.
> Capability establishes demonstrated properties.**

### 3.5 Ejemplo combinado

```text
CPU:
    value      = 8 cores
    source     = B
    truth      = declared
    expiry     = 3600 s
    confidence = low

CPU:
    value      = medium (tiempo de respuesta promedio)
    source     = A (observador)
    truth      = observed
    expiry     = 300 s
    confidence = high

CPU:
    value      = X work units / s
    source     = probe-3
    truth      = verified
    expiry     = 86400 s
    confidence = high
```

---

## 4. First Contact

### 4.1 No es ping/pong

Paradigma antiguo:

```text
A → B  "¿estás?"
B → A  "sí"
```

Paradigma IPv7:

```text
A → B  FIRST CONTACT (probe mínimo)

B → A  IDENTITY
       CAPABILITIES
       PROFILE_INFO
       AVAILABILITY
       LOCATOR
       PATH_INFO
       OBSERVABLE METRICS
```

A aprende progresivamente quién está al otro lado, sin exigir un
interrogatorio completo.

### 4.2 Preguntas que resuelve

```text
¿Quién eres?
¿Eres IPv7?
¿Qué versión soportas?
¿Qué primitivas entiendes?
¿Qué perfiles reconoces?
¿Cuál es tu MTU?
¿Qué tan rápido respondes?
¿Puedes mantener una sesión?
¿Qué capacidad de procesamiento declaras?
¿Cuándo puedes responder?
¿Eres permanente, intermitente o dormido?
```

### 4.3 Progresivo

```text
FIRST CONTACT
     ↓
minimal response
     ↓
knowledge grows progressively
     ↓
optional capability probes
     ↓
verified knowledge
```

No todos los datos viajan en el primer mensaje. El conocimiento crece
según sea necesario.

---

## 5. Componentes de Node Knowledge

```text
Node Knowledge
│
├── Identity
│     └── quién es (persistent)
│
├── Locator
│     └── dónde podría encontrarse (perishable)
│
├── Reachability
│     └── existe una ruta usable ahora (perishable)
│
├── Availability
│     └── cuándo y cómo puede responder (declared + observed)
│
├── Capabilities
│     └── qué dice poder hacer (declared) / qué demuestra (verified)
│
├── Profiles
│     └── qué perfiles reconoce (declared)
│
├── Path
│     └── ruta descubierta y PATH_MTU (perishable)
│
└── Metrics
      └── observaciones: RTT, pérdida, jitter, latencia, etc.
```

Ninguno de estos componentes es una primitiva del Core. Son
construcciones de conocimiento que se mantienen en cada nodo y pueden
transportarse como objetos a través del Core.

Cada ítem de conocimiento debe registrar procedencia, certeza y vida:

```text
knowledge item
├── value
├── source       (quién lo aportó)
├── truth        (declared / observed / verified)
├── expiry       (cuándo deja de ser válido)
└── confidence   (qué tan fiable es en este contexto)
```

Ejemplo:

```text
CPU:
    value      = 8 cores
    source     = B
    truth      = declared
    expiry     = 3600 s
    confidence = low

CPU:
    value      = medium (tiempo de respuesta promedio)
    source     = A (observador)
    truth      = observed
    expiry     = 300 s
    confidence = high

CPU:
    value      = X work units / s
    source     = probe-3
    truth      = verified
    expiry     = 86400 s
    confidence = high
```

---

## 6. Niveles de conocimiento

```text
UNKNOWN
   ↓
OBSERVED
   ↓
IDENTIFIED
   ↓
CAPABILITIES_KNOWN
   ↓
PROFILE_KNOWN
   ↓
PATH_KNOWN
   ↓
SESSION_ESTABLISHED
```

Cada nivel puede caducar de forma independiente:

```text
Identity      → años (persistent)
Locator       → segundos/minutos (perishable)
Capability    → minutos/horas (perishable)
Path          → segundos/minutos (perishable)
Availability  → dinámica
Metrics       → histórica, decae con el tiempo
Session       → temporal
```

### Ciclo de vida de cada ítem

```text
Knowledge
   │
   ├── fresh     → usable
   ├── stale     → caducó, requiere refresh antes de confiar
   ├── refresh   → se solicita actualización
   ├── update    → se recibe nueva información
   ├── expire    → se descarta
   └── verify    → se somete a un procedimiento de verificación
```

Transiciones:

```text
fresh ──(time)──► stale ──(no refresh)──► expired
  ▲                    │
  └────── refresh ─────┘
```

---

## 7. Métricas observables

No necesitan cooperación explícita del otro nodo. Funcionan incluso
contra nodos que no hablen IPv7.

```text
TRANSPORTE
    RTT
    jitter
    packet loss
    retransmissions
    throughput
    MTU
    path quality

PROCESAMIENTO
    request_response_time
    object_processing_time
    computational_probe (solo si se acepta)

DISPONIBILIDAD
    last_seen
    response_window
    expected_latency
    wake_window
    communication_mode

PROTOCOLO
    protocol_version
    supported_channels
    supported_object_formats
    supported_security

COMPORTAMIENTO
    timeouts
    invalid_responses
    stability
```

---

## 8. Capacidades declaradas

Ejemplo de lo que un nodo podría declarar:

```text
IPv7 version: 0.x
Profiles:
    sensor
    telemetry
Channels:
    control
    query
    telemetry
MTU: 1280
Availability: scheduled
Communication mode: intermittent
Expected response: < 100 ms
Processing capability: medium
```

La declaración es información. No se confunde con la observación ni con la
verificación.

---

## 9. Capability Probes (opt-in)

Si una aplicación o ruta necesita conocer capacidad real, puede
solicitar un probe:

```text
CHALLENGE
   │
   ▼
[trabajo definido]
   │
   ▼
RESPONSE
   │
   ▼
observed elapsed_time
```

```text
CAPABILITY_PROBE
    algorithm = X
    work_factor = Y
    timestamp = ...
    environment = ...
    result = ...
    elapsed = 37 ms
```

Reglas:

* No son obligatorios.
* No son `Proof of Work` en el Core.
* Su semántica pertenece a Profile/Capability.
* El Core solo transporta el objeto.

---

## 10. Conocimiento de nodos no-IPv7

IPv7 puede observar y registrar nodos que no hablen IPv7:

```text
IPv7 response      → negociar IPv7
IPv4 / TCP / UDP   → external node
HTTP / otro        → external service
silencio           → observar, no asumir fallo
```

Esto permite que IPv7 actúe como capa de conocimiento de la red, no solo
como otro protocolo de transporte.

---

## 11. Reglas de diseño

1. **Progressive.** El conocimiento crece según se necesita.
2. **Contextual.** Una métrica incluye valor, unidad, timestamp,
   observador y contexto.
3. **Perishable.** Cada tipo de conocimiento caduca a su propia velocidad.
4. **Non-mandatory.** No se exige verificación para poder comunicarse.
5. **Core-agnostic.** El Core transporta estructura; Profiles definen
   significado y probes.
6. **Trust-later.** No se requiere confianza previa; se construye
   progresivamente.

---

## 12. Separación conceptual clave

```text
"Soy este nodo"       → Identity / authentication
"Soy capaz de X"      → Capability (declared)
"Realmente hice X"    → Verification (observed/proved)
```

La autenticidad de identidad no es lo mismo que la capacidad declarada.
Un nodo puede ser auténtico y no poder cumplir lo que dice. `Node
Knowledge` mantiene esas dimensiones separadas.

---

## 13. Próximo paso

Diseñar el wire format de `First Contact` y `Node Knowledge`, pero sin
implementarlo todavía. El objetivo es descubrir si se puede construir
casi completamente con las primitivas que ya existen (`Identity`,
`Channel`, `Session`, `Path`, `Container/Object`) o si realmente se
necesitan nuevos campos en el Core.

## 14. Documentos complementarios

* **First Contact Design** (`FIRST_CONTACT_DESIGN.md`): flujo de contacto
  inicial, tres situaciones según lo que A sabe de B, separación entre
  `Discovery`, `First Contact`, `Path`, `Session` y `Knowledge`, y ciclo
  de vida del conocimiento.
* **Contact / Knowledge Invariants** (`CONTACT_KNOWLEDGE_INVARIANTS.md`):
  reglas que debe respetar cualquier wire format futuro de `CONTACT`,
  `KNOWLEDGE`, `TRUTH`, `LIFETIME` y `PROBE`.
* **Container / Object Wire Format Design**
  (`CONTAINER_OBJECT_WIREFORM_DESIGN.md`): modelo lógico e invariantes
  del formato que transportará First Contact y Node Knowledge.
