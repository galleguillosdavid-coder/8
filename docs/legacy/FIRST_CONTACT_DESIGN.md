# IPv7 — First Contact Design

> **Estado**: diseño conceptual. Sin código todavía.
>
> Esta fase parte de evidencia real: la validación A → B → C con
> PATH_DISCOVER, PATH_MTU, relay y entrega de DATA verificada por SHA-256
> (`ipv7_mvp/demo_3nodes.py`). No se asigna ningún wire format concreto
> todavía; el objetivo es definir qué información mínima se necesita,
> de dónde viene y cómo se mantiene viva.

---

## 1. Pregunta de partida

> Cuando A encuentra por primera vez a B, ¿cuál es la cantidad mínima de
> información que A necesita conocer de B para decidir qué hacer después?

No asumimos un formato de mensaje. Primero definimos la información, su
fuente, su grado de verdad y su vida útil.

---

## 2. Matriz de conocimiento mínimo

| Conocimiento            | Fuente                 | Tipo de verdad             | Vida útil      |
|-------------------------|------------------------|----------------------------|----------------|
| Identity                | B                      | DECLARED → VERIFIED        | larga          |
| Locator                 | red / B                | OBSERVED                   | corta          |
| Reachability            | PATH                   | OBSERVED                   | corta          |
| MTU                     | PATH                   | OBSERVED                   | variable       |
| Availability            | B + observación        | DECLARED + OBSERVED        | variable       |
| Capabilities            | B                      | DECLARED                   | variable       |
| Profiles                | B                      | DECLARED                   | variable       |
| RTT                     | A (propios paquetes)   | OBSERVED                   | muy corta      |
| Pérdida                 | A (propios paquetes)   | OBSERVED                   | corta          |
| Capacidad de procesamiento | Probe              | VERIFIED                   | variable       |

Observaciones:

* **Identity** comienza como declarada; la verificación (firma, DID,
  autenticación) viene después y es de larga vida.
* **Locator** puede provenir de una respuesta, de un caché o de una
  observación directa; caduca rápido porque un nodo puede moverse.
* **MTU** se obtiene del camino, no del nodo destino; cambia si cambia
  la ruta.
* **Availability** no es solo lo que B dice; es lo que B dice comparado
  con lo que A observa.
* **RTT / pérdida** son propiedad del observador, no requieren que B las
  declare.
* **Capacidad de procesamiento** solo se verifica mediante un probe
  opt-in; no es obligatoria para First Contact.

---

## 3. ¿Qué significa realmente "First Contact"?

No es una única operación. Depende de cuánto sabe A de B antes de
intentar comunicarse.

### Caso 1: A conoce el locator de B

```text
A ─────► B
     CONTACT
         ↓
   FIRST CONTACT RESPONSE
   (identity, capabilities, availability, profiles)
```

A ya sabe dónde enviar. Solo necesita aprender quién está al otro lado.

### Caso 2: A conoce la identidad de B

```text
A
│
└── RESOLVE identity → locator
        ↓
    CONTACT
        ↓
   FIRST CONTACT RESPONSE
```

A sabe quién busca pero no dónde. Primero resuelve el locator, luego
inicia contacto.

### Caso 3: A no conoce absolutamente nada

```text
A
│
└── DISCOVERY
       "¿quién conoce a X?" / "¿quiénes existen?"
        ↓
    posibles identidades + locators
        ↓
    CONTACT
        ↓
   FIRST CONTACT RESPONSE
```

A descubre primero que B existe y dónde podría estar.

---

## 4. Discovery, First Contact, Path y Session no son lo mismo

```text
DISCOVERY
"¿Dónde puedo encontrarlo?" / "¿Quién conoce a X?"
      │
      ↓
FIRST CONTACT
"¿Quién eres y qué puedes hacer?"
      │
      ↓
PATH
"¿Puedo comunicarme contigo y por qué camino?"
      │
      ↓
SESSION
"Establezcamos comunicación contextual."
      │
      ↓
KNOWLEDGE
"Esto es lo que actualmente sé de ti."
```

### 4.1 Discovery

* Resuelve **identidad ↔ locator**.
* Puede ser dirigido (preguntar a un nodo conocido), broadcast bajo
  demanda, o consulta a un caché local.
* No es heartbeat. No prueba vida. Solo busca información.

### 4.2 First Contact

* Ocurre una vez que A sabe a dónde enviar o a quién preguntar.
* Devuelve información de identidad, capacidades, disponibilidad y
  perfiles reconocidos.
* No exige verificación de capacidad. Es presentación, no examen.

### 4.3 Path

* Ocurre una vez que A conoce un locator.
* Descubre si existe una ruta, cuál es el MTU, y qué nodos
  intermedios participan.
* Es observación pura: los paquetes PATH_DISCOVER miden el camino.

### 4.4 Session

* Contexto temporal de comunicación.
* Puede existir incluso si el nodo no está permanentemente alcanzable.

### 4.5 Knowledge

* Estado acumulado sobre el nodo.
* Tiene temporalidad y grado de certeza.

---

## 5. Flujo completo posible

```text
A no sabe nada de B
        │
        ▼
    DISCOVERY
        │
        ▼
    locator de B
        │
        ▼
    FIRST CONTACT
        │
        ▼
    identity + capabilities + availability + profiles
        │
        ▼
    PATH_DISCOVER
        │
        ▼
    PATH_MTU + reachability
        │
        ▼
    SESSION
        │
        ▼
    KNOWLEDGE (construido progresivamente)
```

No todos los pasos son obligatorios:

* Si A ya conoce el locator, salta Discovery.
* Si solo necesita saber si B responde, Path puede preceder a un
  First Contact completo.
* Si B es un nodo dormido, First Contact puede dejar un conocimiento
  parcial hasta que B despierte.

---

## 6. Ciclo de vida del conocimiento

Node Knowledge no es una tabla estática. Cada ítem puede:

```text
KNOWLEDGE
   │
   ├── stale     (caducó, ya no se confía)
   ├── refresh   (se solicita actualización)
   ├── update    (se recibe nueva información)
   ├── expire    (se descarta)
   └── verify    (se somete a un procedimiento de verificación)
```

Reglas:

* **Identity** se vuelve stale rara vez; se verifica mediante
  autenticación.
* **Locator** se vuelve stale rápidamente; se refresca con cada
  comunicación o mediante Discovery.
* **Path** se invalida ante cambio de ruta; se recalcula con
  PATH_DISCOVER.
* **Metrics** (RTT, pérdida) se actualizan continuamente con cada
  intercambio.
* **Availability** se compara con observaciones; si B declara
  "always-listening" pero no responde, el conocimiento se marca como
  inconsistente, no como "nodo muerto".

---

## 7. Conocimiento inicial mínimo tras First Contact

Tras el primer intercambio exitoso, A debería poder construir:

```text
Node Knowledge for B
│
├── Identity (declared, no verificada todavía)
├── Locator (observed / declared)
├── Protocol version (declared)
├── Capabilities (declared)
├── Profiles (declared)
├── Availability (declared)
└── Reachability + PATH_MTU (observed, si se hizo Path)
```

Aún sin verificación, A ya puede decidir:

* ¿Intento establecer una sesión?
* ¿Espero a la ventana de disponibilidad declarada?
* ¿Necesito un probe de capacidad antes de enviar muchos datos?

---

## 8. Decisiones abiertas para la siguiente sesión de diseño

1. **¿First Contact es un mensaje del Core o un objeto de Profile?**
   * Opción A: tipo de mensaje básico en el Core (`FIRST_CONTACT_REQUEST` /
     `FIRST_CONTACT_RESPONSE`).
   * Opción B: objeto transportado por `Container` con un perfil de
     control (`control_profile`).
   * Opción C: reutilizar `DISCOVER` ampliado.

2. **¿Cómo se transporta la matriz de conocimiento?**
   * ¿Cada ítem es un objeto IDTLV separado?
   * ¿Hay un objeto compuesto `node_knowledge`?
   * ¿Se separan declaraciones, observaciones y verificaciones?

3. **¿Cómo se expresa la vida útil y el estado stale/refresh/expire?**
   * ¿Timestamp absoluto?
   * ¿TTL por ítem?
   * ¿Versión de conocimiento?

4. **¿Cómo se inicia First Contact cuando solo se conoce la identidad?**
   * ¿El resolver es parte de Discovery o es un servicio separado?
   * ¿Puede otro nodo responder en nombre de B (proxy/cache)?

5. **¿Cómo se mantiene la observación sin heartbeats?**
   * Las métricas se actualizan solo cuando hay tráfico.
   * Si no hay tráfico, el conocimiento simplemente envejece hasta stale,
     sin declarar al nodo muerto.

---

## 9. Separación: mecanismo de contacto vs. información intercambiada

El Core puede entender que un nodo quiere establecer contacto y
continuar una comunicación, sin necesidad de entender qué se intercambia
durante ese contacto.

```text
CORE
 │
 ├── CONTACT
 │     ├── quién
 │     ├── dónde responder
 │     ├── capacidades estructurales mínimas
 │     └── cómo continuar la comunicación
 │
 └── transporte del intercambio
          │
          ▼
      OBJECTS
          │
          ▼
       PROFILES
```

El Core transporta el mecanismo de contacto y los objetos. Los Profiles
interpretan el contenido de esos objetos.

Regla:

> El Core sabe que un nodo quiere comunicarse. No sabe si es un sensor,
> un servidor o un vehículo.

## 10. First Contact no siempre es IPv7

Si B no habla IPv7, el concepto sigue siendo útil:

```text
        FIRST CONTACT
             │
      ┌──────┴──────┐
      │             │
   IPv7          UNKNOWN
      │             │
      ▼             ▼
  CONTACT       OBSERVE
      │             │
      └──────┬──────┘
             ▼
       NODE KNOWLEDGE
```

* **IPv7**: negociar contacto con primitivas del protocolo.
* **UNKNOWN**: observar lo que sea observable (RTT, MTU, respuesta,
  silencio).

First Contact es una operación conceptual de la red, no un paquete
específico.

## 11. Estructura de un ítem de conocimiento

No basta con almacenar `latency = 12 ms`. Cada conocimiento debe
registrar procedencia, certeza y vida:

```text
Knowledge
│
├── identity
│    └── value
│         ├── source       (quién lo aportó)
│         ├── truth        (declared / observed / verified)
│         └── expiry       (cuándo deja de ser válido)
│
├── locator
│    └── value
│         ├── source
│         ├── truth
│         └── expiry
│
├── capability
│    └── value
│         ├── source
│         ├── truth
│         └── expiry
│
└── metric
     └── value
          ├── source
          ├── truth
          └── expiry
```

Ejemplo:

```text
CPU:
    value = 8 cores
    source = B
    truth = declared
    expiry = 3600 s

CPU:
    value = medium (tiempo de respuesta promedio)
    source = A (observador)
    truth = observed
    expiry = 300 s

CPU:
    value = X work units / s
    source = probe-3
    truth = verified
    expiry = 86400 s
```

Los tres datos coexisten. No se decide cuál "es la verdad"; cada uno
sirve para distintos propósitos.

## 12. Declarations describe possibilities; observations describe behavior; verifications establish capabilities

```text
B says:  CPU = 8 cores
         → DECLARATION (possibility)

A sees:  response time = 15 ms
         → OBSERVATION (behavior)

A runs: probe result = X work units / s
         → VERIFICATION (capability)
```

Regla:

> **Declarations describe possibilities. Observations describe behavior.
> Verifications establish capabilities.**

## 13. Knowledge has a lifetime

Un conocimiento verificado ayer no necesariamente sigue siendo cierto
hoy.

```text
Knowledge state
│
├── fresh    → usable
├── stale    → caducó, requiere refresh antes de confiar
└── expired  → se descarta; requiere redescubrimiento
```

Transiciones:

```text
fresh ──(time)──► stale ──(no refresh)──► expired
  ▲                    │
  └────── refresh ─────┘
```

Cada ítem tiene su propia vida útil:

```text
Identity      → años
Locator       → segundos/minutos
Path/MTU      → segundos/minutos
Availability  → dinámica
RTT/pérdida   → segundos
Capability    → horas/días
```

## 14. Heartbeat no es un requisito universal

No hay interrogatorio periódico:

```text
"¿Sigues vivo?" → "Sí" → "¿Sigues vivo?" → "Sí" → ...
```

La red aprende del tráfico real:

```text
B → A DATA
        ↓
   A sabe que B está disponible

A → B DATA
B → A RESPONSE
        ↓
   A mide RTT y observa disponibilidad
```

El heartbeat es solo una herramienta opcional cuando se necesita
verificar algo que el tráfico normal no demuestra.

## 15. Cinco piezas para cerrar antes del wire format

Antes de decidir bytes, debemos cerrar el significado:

```text
1. CONTACT
   ↓
2. KNOWLEDGE
   ↓
3. TRUTH
   DECLARED / OBSERVED / VERIFIED
   ↓
4. LIFETIME
   fresh / stale / expired
   ↓
5. PROBE
   optional / profile-defined
   ↓
6. WIRE FORMAT  (recién aquí)
```

Regla:

> Si diseñamos primero el wire format, podemos terminar optimizando bytes
> de algo cuya semántica todavía no hemos terminado de entender.

## 16. Principios que regirán el wire format

1. **First Contact es progresivo.** No se exige un solo mensaje con toda
   la información.
2. **Declarado ≠ observado ≠ verificado.** El formato debe poder
   transportar ambos sin confundirlos.
3. **Nada es obligatorio para comunicar.** Un nodo puede responder solo
   con identidad y protocolo; el resto se aprende después.
4. **No semántica de aplicación en el Core.** El Core transporta el
   mecanismo de contacto y los objetos; Profiles interpretan contenido.
5. **Knowledge es perishable.** El formato debe permitir expresar
   temporalidad y caducidad.
6. **First Contact es conceptual, no solo un paquete.** Funciona también
   contra nodos que no hablen IPv7.

---

## 18. CONTACT como primitiva del Core

`CONTACT` no es simplemente un mensaje. Es una operación primitiva del
Core que permite a un nodo expresar:

```text
"Quiero establecer comunicación contigo."
```

El Core define el acto de contactar. Los objetos transportados durante
el contacto contienen el conocimiento. Los Profiles definen cómo
interpretar ese conocimiento.

```text
CORE
 │
 ├── CONTACT          (operación primitiva)
 │
 ├── OBJECT transport  (lo que se intercambia)
 │
 └── PROFILE         (quién interpreta el contenido)
```

Regla:

> El Core sabe que dos nodos están intentando comunicarse. No sabe qué
> se están diciendo.

Esto permite que `First Contact` sea barato: primero se establece la
comunicación, después se decide qué conocimiento intercambiar.

## 19. CONTACT → OBSERVE → KNOWLEDGE → PROBE → VERIFIED

Proceso completo conceptual:

```text
UNKNOWN
   │
   ▼
CONTACT
   │
   ├── no response ──────────────► UNKNOWN
   │
   ├── legacy response ──────────► OBSERVE
   │        (IPv4, TCP, UDP, HTTP, TLS, etc.)
   │
   └── IPv7 response ──────────► ESTABLISH
            │
            ▼
        KNOWLEDGE
            │
            ▼
        OPTIONAL PROBES
            │
            ▼
        VERIFIED
```

* **UNKNOWN**: no sabemos nada del nodo.
* **CONTACT**: intentamos comunicarnos.
* **OBSERVE**: si el nodo no habla IPv7, medimos lo que sea observable.
* **ESTABLISH**: si el nodo habla IPv7, comenzamos a construir
  conocimiento estructurado.
* **KNOWLEDGE**: acumulamos información con source, truth, expiry,
  confidence.
* **OPTIONAL PROBES**: si es necesario, solicitamos una prueba de
  capacidad.
* **VERIFIED**: registramos el resultado del probe como conocimiento
  verificado.

Regla:

> CONTACT debe ser barato. No se exige verificación de capacidad en el
> primer intercambio.

## 20. Tres categorías de conocimiento

No todo lo que aprendemos es lo mismo. Se separan tres categorías:

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

### 20.1 Observation

```text
"B respondió a un paquete."
"B usa IPv4."
"B responde en el puerto 80."
"B no responde durante 10 minutos."
```

No requiere cooperación explícita de B.

### 20.2 Measurement

```text
RTT = 12 ms
packet loss = 0.3 %
PATH_MTU = 1280
response latency = 8 ms
throughput = 85 Mbps
```

Son observaciones cuantificadas.

### 20.3 Capability

```text
computational probe result = 82 units/s
crypto probe result = fast
memory probe result = large dataset processed in 45 ms
```

Requiere un procedimiento opt-in y un Profile que defina el probe.

Regla:

> **Observation describe behavior. Measurement quantify it. Capability
> establishes demonstrated properties.**

## 21. Capability Probe

No es `Proof of Work`. Es un procedimiento definido por un Profile para
medir una capacidad específica.

```text
A → B
    PROBE
      type = computational
      algorithm = X
      difficulty = Y
      constraints = Z

B decide si acepta.

B → A
    RESULT
      algorithm = X
      work = Y
      elapsed = T
      timestamp = ...
```

El Core solo ve:

```text
OBJECT
PROBE
RESULT
```

El Profile `computational-capability` define:

```text
probe
measurement
unit
interpretation
```

Variedad posible de probes:

```text
CPU integer
CPU vector
crypto
memory
serialization
compression
network
```

Regla:

> El resultado es un perfil de comportamiento, no un número absoluto.

## 22. Conocimiento de nodos no-IPv7

IPv7 no rechaza a los nodos que hablan otros protocolos. Los observa y
aprende:

```text
Node: B

identity
    declared: unknown

locator
    observed: 192.168.x.x

protocol
    observed: IPv4

transport
    observed: UDP

availability
    observed: reachable

latency
    observed: 4.2 ms

path_mtu
    observed: 1280

ipv7
    verified: false
```

Si más tarde B habla IPv7:

```text
ipv7
    verified: true

identity
    declared: did:ipv7:...

profiles
    declared: sensor.v1
```

El conocimiento evoluciona. No se borra lo anterior; se actualiza con
nuevas entradas que tienen su propia source, truth, expiry y
confidence.

## 23. Confidence como propiedad del conocimiento

Cada ítem de conocimiento lleva una confianza relativa, no una verdad
absoluta:

```text
knowledge item
    value
    source
    truth
    expiry
    confidence
```

Ejemplos:

```text
CPU cores = 8
source = remote declaration
truth = declared
confidence = low

CPU performance = 82
source = computational probe
truth = verified
confidence = high

RTT = 12 ms
source = A's own measurement
truth = observed
confidence = high
```

`confidence` es contextual. No es una probabilidad matemática
obligatoria; es una etiqueta que ayuda a decidir qué conocimiento usar.

## 24. Implicación para routing futuro

Con Node Knowledge, el routing deja de ser solo "¿hay camino?". Puede
llegar a ser:

```text
PATH
    MTU >= 1400
    latency < 20 ms
    reliability > 99%
    computational capability >= X
```

Eso convierte a IPv7 en algo muy diferente de un protocolo de
direccionamiento tradicional.

Pero esa evolución pertenece a Fases posteriores. Ahora solo la
documentamos como motivación.

## 25. Invariantes cerradas

Las invariantes de diseño para `CONTACT`, `KNOWLEDGE`, `TRUTH`,
`LIFETIME` y `PROBE` están documentadas en
`CONTACT_KNOWLEDGE_INVARIANTS.md`. Cualquier wire format futuro debe
respetarlas para no romper la arquitectura semántica construida hasta
aquí.

## 26. Próximo paso

Diseñar el modelo lógico y wire format concreto de `Container → Object`
que permita representar `First Contact` y `Node Knowledge` respetando
las invariantes de `CONTACT_KNOWLEDGE_INVARIANTS.md`. Ver
`CONTAINER_OBJECT_WIREFORM_DESIGN.md`.


