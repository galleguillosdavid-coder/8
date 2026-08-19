IPv7 — ARQUITECTURA, PRINCIPIOS Y PLAN DE EVOLUCIÓN
0. Principio rector

IPv7 no debe ser simplemente:

IPv6 con direcciones más grandes

ni:

TCP/IP con más puertos

La investigación busca una arquitectura donde:

IDENTIDAD
    │
    ├── LOCALIZACIÓN
    │
    ├── DISPONIBILIDAD
    │
    ├── SESIÓN
    │
    ├── CANAL
    │
    ├── CONTENEDOR
    │
    ├── OBJETO
    │
    └── CONTEXTO

sean conceptos independientes pero composables.

La pregunta arquitectónica fundamental es:

¿Cuál es la abstracción mínima necesaria para construir una red global escalable, eficiente, segura y extensible sin introducir semántica de aplicaciones dentro del Core?

1. Arquitectura fundamental

La arquitectura se divide en tres niveles:

┌──────────────────────────┐
│      APPLICATIONS        │
│                          │
│ aplicaciones concretas   │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│         PROFILES         │
│                          │
│ semántica y reglas       │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│           CORE           │
│                          │
│ primitivas universales   │
└────────────┬─────────────┘
             │
             ▼
      IPv4 / IPv6 / UDP
      QUIC / otros medios
Regla fundamental

El Core transporta estructura; los Profiles aportan semántica.

El Core puede saber:

CHANNEL
SESSION
OBJECT
CONTAINER
IDENTITY
PATH
AVAILABILITY
SECURITY
TTL
SEQUENCE

Pero no debe saber:

temperatura
vehículo
imagen
archivo
música
humedad
presión

Eso pertenece a los Profiles y Applications.

2. Identidad ≠ localización ≠ disponibilidad

Esta separación debe quedar explícita.

Un error conceptual sería:

IDENTIDAD
    =
DIRECCIÓN
    =
CONECTIVIDAD
    =
SERVICIO

IPv7 debe separar:

Identity
   │
   ├── ¿Quién es?
   │
   ├── Location
   │      ¿Dónde puede encontrarse?
   │
   ├── Availability
   │      ¿Cuándo/cómo puede responder?
   │
   ├── Session
   │      ¿Existe una comunicación activa?
   │
   └── Health
          ¿Qué tan estable es la comunicación?

Esto permite movilidad, dispositivos dormidos, sensores de muy bajo consumo y nodos con disponibilidad extremadamente diferente.

3. NUEVO PRINCIPIO: AVAILABILITY
IPv7 SHOULD LISTEN, NOT SHOUT

La red no debe generar tráfico periódico únicamente para comprobar que un nodo continúa existiendo.

La existencia de un nodo no debería depender de que este envíe:

HELLO
HELLO
HELLO
HELLO
...

cada segundo.

Esto sería especialmente ineficiente para dispositivos diseñados para comunicarse muy ocasionalmente.

Ejemplo

Un sensor puede estar diseñado para transmitir:

1 medición por año

Durante los restantes 364 días puede permanecer:

radio apagada
CPU dormida
sin sesión activa
sin transmitir

Eso no significa necesariamente que haya abandonado la red.

Puede conservar:

Identity
Membership
Profile
Capabilities
Availability declaration
Last known location

y despertar únicamente cuando corresponda.

4. Pertenencia no significa conexión permanente

Debemos distinguir al menos:

MEMBERSHIP
    ↓
¿El nodo pertenece/conoce la red?


AVAILABILITY
    ↓
¿En qué condiciones puede responder?


REACHABILITY
    ↓
¿Puede alcanzarse ahora?


SESSION
    ↓
¿Existe una comunicación activa?


HEALTH
    ↓
¿Qué tan estable es esa comunicación?

Por tanto:

Nodo conocido
≠
Nodo actualmente alcanzable
≠
Nodo con sesión activa

Esto es fundamental.

5. Estados de disponibilidad

No conviene llamar a todo simplemente:

CONNECTED
DISCONNECTED

porque esa clasificación es demasiado pobre.

Una primera abstracción podría ser:

AVAILABLE
DORMANT
SCHEDULED
ON_DEMAND
UNREACHABLE
UNKNOWN

Pero estos nombres todavía deben evaluarse.

Lo importante es que el Core tenga la capacidad estructural de representar:

availability_state
response_capability
expected_response
wake_window
communication_mode

sin obligar al Core a interpretar el significado de cada aplicación.

6. Capacidad de respuesta

Un nodo puede declarar algo parecido a:

Availability:


response capability:
    immediate
    delayed
    scheduled
    event-driven
    none-until-wakeup


expected latency:
    10 ms
    1 s
    1 min
    1 hour
    unknown


wake window:
    every 24 h
    every month
    once/year
    event triggered


communication mode:
    always-listening
    intermittent
    sleeping
    scheduled
    opportunistic

Pero estos valores deben tratarse como información de disponibilidad, no como semántica de sensores.

El Core no necesita saber:

“Este nodo es un sensor que despierta una vez al año”.

Solo necesita saber:

“Este identificador tiene una determinada capacidad/disponibilidad declarada”.

El Profile/Application puede interpretar el significado.

7. La ausencia de respuesta NO debe significar automáticamente "desconectado"

Este es uno de los cambios arquitectónicos más importantes.

Actualmente muchos sistemas hacen:

PING
   ↓
no responde
   ↓
TIMEOUT
   ↓
DEAD

IPv7 debería evitar esta conclusión automática.

La interpretación debe considerar:

Availability
+
Expected response time
+
Communication mode
+
Last known state
+
Path
+
Session
+
Health

Por ejemplo:

Nodo A
availability = ALWAYS_LISTENING
expected_response = 100 ms

Si no responde durante varios segundos:

sospecha de fallo ↑
Nodo B
availability = SCHEDULED
wake_window = cada 24 horas

No responder durante 10 minutos:

no necesariamente es fallo
Nodo C
availability = ON_DEMAND
response = solamente después de wake request

No responder espontáneamente:

comportamiento esperado
Nodo D — sonda espacial

Podría declarar:

availability = DELAYED
expected_response = variable

y su ausencia durante minutos u horas no debería provocar aislamiento automático.

La arquitectura debe ser capaz de soportar incluso:

segundos
minutos
horas
días
meses
años

sin confundir ausencia de tráfico con inexistencia.

8. Discovery: escuchar antes que transmitir

El discovery debe evolucionar desde:

BROADCAST
   ↓
TODOS RECIBEN
   ↓
TODOS PROCESAN

hacia:

LISTEN
   ↓
QUERY
   ↓
RESPUESTA RELEVANTE

La regla:

IPv7 SHOULD LISTEN, NOT SHOUT.

No significa que el broadcast deba desaparecer.

Puede existir como mecanismo:

bootstrap
LAN
emergency
discovery inicial

pero no debería convertirse en un requisito periódico para demostrar vida.

9. Membership / Presence

Debe existir conceptualmente una diferencia entre:

PRESENCE

y:

HEARTBEAT

Un nodo puede haber declarado previamente:

I belong to network X
My identity is Y
My profile is Z
My availability is scheduled
My expected response behavior is ...

y luego permanecer silencioso.

Por tanto, la red puede conservar:

last_known_presence

sin exigir:

heartbeat every N seconds
10. Availability no debe confundirse con Health

Esta separación es especialmente importante.

Availability

Describe:

Cuándo y cómo espera comunicarse el nodo.

Health

Describe:

Qué tan bien está funcionando realmente la comunicación.

Por ejemplo:

Sensor:
availability = once/year
health = NORMAL

Puede estar perfectamente sano aunque lleve 11 meses sin transmitir.

En cambio:

availability = always-listening
health = UNSTABLE

significa que debería estar disponible pero presenta:

packet loss
timeouts
latency
retries
11. Adaptive Stability Controller

El sistema de estabilidad propuesto debe permanecer separado de Availability.

Arquitectura:

                 IPv7 Core
                     │
       ┌─────────────┼──────────────┐
       │             │              │
   Availability    Session        Path
       │                            │
       │                         PATH_MTU
       │                            │
       └───────────┬────────────────┘
                   │
                Health
                   │
                   ▼
        Adaptive Stability
              Controller

El sistema de estabilidad protege a la red de:

pérdida
timeouts
retries
latencia
rutas inestables
errores
MTU inconsistentes

pero no debe interpretar automáticamente la ausencia de tráfico como fallo.

12. Estados de estabilidad

Mantener inicialmente:

NORMAL
DEGRADED
UNSTABLE
RESTRICTED
ISOLATED

con recuperación:

ISOLATED
    ↓
PROBE
    ↓
RECOVERING
    ↓
DEGRADED
    ↓
NORMAL

Estos estados corresponden a Health/Stability, no a Availability.

13. Recursos adaptativos

Valores iniciales configurables:

NORMAL       100%
DEGRADED      50%
UNSTABLE      20%
RESTRICTED     5%
ISOLATED       0%

La finalidad es:

proteger la estabilidad global de la red antes que insistir indefinidamente en una comunicación problemática.

14. Aislamiento reversible

ISOLATED no significa:

eliminar nodo

Significa:

no utilizar normalmente para tráfico de datos

pero mantener:

DISCOVERY
PROBE
PATH_RECALCULATION
RECOVERY
CONTROL

cuando la Availability del nodo indique que puede responder.

15. Canales

Los canales siguen siendo primitivas del Core:

0 = control
1 = telemetry
2 = query
3 = write
4 = emergency

Pero el Core no interpreta su semántica de aplicación.

Por ejemplo:

Core:
"Existe channel 2."


Sensor Profile:
"Para sensores, channel 2 puede utilizarse para consultas."


Application:
"Consultar temperatura del sensor X."
16. Session

Una sesión representa una comunicación activa o contexto temporal.

Conceptualmente:

OPEN
   ↓
SESSION
   ↓
CHANNEL
   ↓
CONTAINER
   ↓
OBJECT
   ↓
CLOSE

Una sesión activa no implica que el nodo tenga que permanecer conectado indefinidamente.

Un nodo puede:

tener identidad
+
pertenecer a la red
+
tener disponibilidad programada
+
no tener ninguna sesión

y seguir siendo un miembro válido.

17. Object / IDTLV

La estructura continúa:

TYPE | LENGTH | ID | VALUE

donde:

TYPE
1 byte

Define estructura, no semántica global.

LENGTH
2 bytes

Longitud del bloque.

ID

Identificador local del objeto dentro del contenedor.

No es:

DID
IP
dirección
puerto
identidad global
VALUE

Contenido.

18. Containers
PACKET
   │
   └── CONTAINER
        ├── OBJECT
        ├── OBJECT
        ├── OBJECT
        └── OBJECT

Permite:

agregación
reducción de overhead
relaciones
deltas
multiplexación
19. Identity

La identidad debe evolucionar hacia una identidad criptográfica persistente:

Identity
   ↓
Public Key
   ↓
DID

con posibilidades futuras de:

Ed25519
ML-DSA / PQC
key rotation
binding
signatures
AEAD

Pero no todas estas tecnologías deben introducirse simultáneamente en el MVP.

20. Seguridad

Evolución:

IDENTITY
    ↓
AUTHENTICATION
    ↓
HANDSHAKE
    ↓
KEY DERIVATION
    ↓
AEAD
    ↓
ANTI-REPLAY
    ↓
PQC

Cada etapa debe probarse antes de agregar la siguiente.

21. Routing

IPv7 debe mantener separadas:

IDENTITY
LOCATION
ROUTING
SERVICE
OBJECT
AVAILABILITY

Una ruta puede considerar:

destination
path
MTU
health
availability
latency

pero no convertir inmediatamente todos estos elementos en una métrica gigantesca.

Primera implementación:

routing_table = {
    node_id: address
}

Después:

multi-hop
path discovery
route selection
adaptive routing
22. PATH_MTU

El trabajo ya realizado queda incorporado como una capacidad del Core.

Una ruta:

A → B → C → D

puede producir:

B = 1400
C = 1280
D = 1500


PATH_MTU = 1280

Si cambia la ruta:

PATH_CHANGED
     ↓
invalidate PATH_MTU
     ↓
PATH_DISCOVER
     ↓
new PATH_MTU

Importante:

Un error de MTU no debe interpretarse automáticamente como un nodo defectuoso.

Puede ser simplemente:

cambio de ruta
23. Discovery + Availability + Health

Estos tres mecanismos deben trabajar juntos, pero no confundirse:

DISCOVERY
¿Quién existe / dónde podría estar?


AVAILABILITY
¿Cuándo y cómo puede responder?


HEALTH
¿Qué tan bien está funcionando la comunicación?

Ejemplo:

Nodo X


Identity:
    conocida


Availability:
    despierta una vez al año


Session:
    ninguna


Health:
    NORMAL


Last presence:
    8 meses atrás

Esto puede ser completamente válido.

24. Ejemplo extremo: sonda espacial

IPv7 debería poder representar conceptualmente:

Identity:
    probe-001


Availability:
    delayed


Expected response:
    variable


Communication mode:
    scheduled


Last known location:
    ...


Session:
    inactive


Health:
    unknown

No debería producir:

PING
PING
PING
PING
PING
...

ni declarar:

NODE DEAD

simplemente porque no respondió inmediatamente.

La red debe comprender que:

la capacidad de respuesta es una propiedad contextual del nodo.

25. Arquitectura Core actualizada

La estructura conceptual queda mejor así:

IPv7 CORE
│
├── Identity
│
├── Channel
│
├── Session
│
├── Path
│   └── PATH_MTU
│
├── Object / IDTLV
│
├── Container
│
├── Availability
│   ├── membership
│   ├── availability state
│   ├── response capability
│   ├── expected response
│   ├── wake window
│   └── communication mode
│
├── Security
│
├── Sequencing / TTL
│
└── Transport
       │
       ├── UDP
       ├── IPv4
       ├── IPv6
       └── otros medios

Y alrededor:

                    APPLICATIONS
                         │
                    ─────┼─────
                         │
                      PROFILES
                         │
                    ─────┼─────
                         │
                      CORE
                         │
              ┌──────────┴──────────┐
              │                     │
          Availability           Health
              │                     │
              └──────────┬──────────┘
                         │
                       Path
                         │
                       MTU
                         │
                     Transport
26. Lo que NO debe hacer el Core

No convertir Availability en un sistema semántico gigantesco.

No introducir:

TEMPERATURE_SENSOR_SLEEP_MODE
SPACE_PROBE_MODE
VEHICLE_MODE
CAMERA_MODE
...

El Core debe proporcionar estructura para describir disponibilidad, mientras que el Profile/Application puede establecer las reglas concretas.

27. Principio de eficiencia energética

IPv7 debe permitir que un dispositivo optimice:

ENERGY
BANDWIDTH
RADIO TIME
CPU
MEMORY

sin ser considerado automáticamente desconectado.

Esto abre una posibilidad importante:

La ausencia de tráfico puede ser una característica de diseño, no una falla.

Un dispositivo extremadamente eficiente podría transmitir muy poco durante años y continuar formando parte de la arquitectura.

28. Discovery futuro

La evolución prevista es:

Nivel 1 — Bootstrap
DISCOVER → HERE
Nivel 2 — Directed discovery
QUERY → RESPONSE
Nivel 3 — Availability-aware discovery
QUERY
   ↓
¿Puede responder ahora?
   ↓
¿cuándo puede responder?
   ↓
¿cómo debe contactarse?
Nivel 4 — Context-aware discovery
Identity
+
Availability
+
Location
+
Profile
+
Object

sin convertir toda esa semántica en parte del Core.

29. Regla de diseño revisada

Cada nueva funcionalidad debe responder:

¿Es estructuralmente universal?
→ CORE
¿Describe el significado de los datos?
→ PROFILE
¿Es comportamiento específico de una aplicación?
→ APPLICATION
¿Describe cuándo/cómo puede responder un participante?
→ AVAILABILITY en el Core
¿Describe qué tan saludable está una comunicación?
→ HEALTH / STABILITY

Esta última separación evita mezclar:

"no responde porque está dormido"

con:

"no responde porque está fallando".
30. Plan de implementación
NO implementar todavía Availability ni Adaptive Stability.

Primero documentarlos como requisitos arquitectónicos futuros.

La implementación actual debe mantenerse:

FUNCIONALIDAD
      ↓
SIMPLICIDAD
      ↓
PRUEBAS
      ↓
EVOLUCIÓN

Y conservar el criterio:

ANTES → funciona
DESPUÉS → sigue funcionando

Los 9/9 tests actuales deben permanecer en verde antes de avanzar.

31. Roadmap actualizado

La escalera puede quedar:

FASE 0
Python + UDP
        ↓
FASE 1
Packet
        ↓
FASE 2
Node
        ↓
FASE 3
Discovery
        ↓
FASE 4
Identity
        ↓
FASE 5
Channel
        ↓
FASE 6
Session
        ↓
FASE 7
IDTLV
        ↓
FASE 8
Container
        ↓
FASE 9
Profiles
        ↓
FASE 10
Encryption
        ↓
FASE 11
Anti-replay
        ↓
FASE 12
Routing
        ↓
FASE 13
P2P avanzado
        ↓
FASE 14
Availability
        ↓
FASE 15
Adaptive Stability
        ↓
FASE 16
Optimización

Availability debería preceder a Stability, porque no podemos evaluar correctamente la salud de un nodo sin saber primero cuál era su comportamiento de disponibilidad esperado.

32. Criterio de éxito futuro

IPv7 no debería considerarse maduro simplemente porque:

A → PING → B → PONG

funciona.

También debería poder demostrar:

Nodo A
   │
   ├── siempre disponible
   │
   ├── nodo B
   │      └── disponible cada 24 h
   │
   ├── nodo C
   │      └── disponible bajo demanda
   │
   └── nodo D
          └── disponible una vez al año

sin necesidad de:

HELLO × 100 por segundo

y sin interpretar automáticamente el silencio como fallo.

33. Regla arquitectónica nueva

IPv7 no debe preguntar constantemente "¿estás vivo?" cuando ya sabe que un nodo no está diseñado para responder constantemente.

En cambio:

IPv7 debe conocer la capacidad y expectativa de respuesta del participante y utilizar esa información para decidir cuándo escuchar, cuándo preguntar y cuándo considerar realmente anómala la ausencia de respuesta.

Esto conduce a una arquitectura mucho más interesante:

        ¿QUIÉN?
          │
       IDENTITY
          │
        ¿DÓNDE?
          │
       LOCATION
          │
      ¿CUÁNDO?
          │
    AVAILABILITY
          │
       ¿CÓMO?
          │
      CHANNEL
          │
       ¿PARA QUÉ?
          │
       PROFILE
          │
       ¿QUÉ?
          │
       OBJECT
          │
       ¿ESTÁ BIEN?
          │
        HEALTH
          │
      ¿POR DÓNDE?
          │
        ROUTING

Y todo esto puede coexistir sin convertir el Core en una gigantesca tabla de semántica.

34. INSTRUCCIÓN PARA LA OTRA IA

Puedes entregarle directamente esta instrucción:

NO IMPLEMENTAR TODAVÍA AVAILABILITY NI ADAPTIVE STABILITY.

Primero documentar ambos conceptos como requisitos arquitectónicos futuros.

En particular, incorporar al diseño la separación explícita entre:

Identity
Membership
Location
Availability
Reachability
Session
Health

No asumir que un nodo sin sesión activa está desconectado.

No asumir que un nodo que no responde inmediatamente está muerto.

No implementar heartbeats o broadcasts periódicos como requisito universal de pertenencia a la red.

La arquitectura debe permitir nodos:

always-listening
intermittent
scheduled
on-demand
dormant
delayed-response

incluyendo dispositivos extremadamente esporádicos, de bajo consumo y sondas con latencias de comunicación muy grandes.

El principio arquitectónico es:

IPv7 SHOULD LISTEN, NOT SHOUT.

La ausencia de respuesta debe interpretarse según la disponibilidad declarada, la capacidad de respuesta esperada, el contexto de la ruta y el estado de la comunicación.

Separar Availability de Health:

Availability = cómo/cuándo debería poder responder.
Health       = qué tan bien está funcionando la comunicación.

No introducir semántica de aplicación en el Core.

El Core debe proporcionar únicamente las primitivas estructurales necesarias para representar disponibilidad y utilizarla en discovery/routing/session management.

No modificar todavía el código.

Primero actualizar la documentación arquitectónica, identificar contradicciones con el diseño actual y proponer la mínima estructura necesaria para implementar Availability en una fase posterior.

Mantener los 9/9 tests actuales como criterio de no regresión.

Y haría una corrección conceptual adicional a todo lo anterior: yo no llamaría “estado de conexión” al nuevo mecanismo. Lo llamaría Availability o capacidad de comunicación.

Porque una sesión puede estar cerrada, el radio puede estar apagado y el nodo puede estar dormido, pero el nodo sigue siendo miembro conocido de la red.

Eso nos permite pasar de la vieja lógica:

¿Está conectado?
    SÍ / NO

a una mucho más potente:

¿Quién es?
    ↓
¿Pertenece?
    ↓
¿Puede responder?
    ↓
¿Cuándo puede responder?
    ↓
¿Por qué medio?
    ↓
¿Cuánto debemos esperar?
    ↓
¿La ausencia de respuesta es realmente anómala?

Creo que esta separación encaja muy bien con la idea original de IPv7 de que la red “escucha, no grita”, y además evita que el futuro sistema de estabilidad castigue erróneamente a dispositivos que simplemente fueron diseñados para estar dormidos.

---

# 35. AVAILABILITY — REFINAMIENTO (consolidación tras validación multiproceso Fase 2.5)

> ⚠️ **Sigue sin implementarse.** Esta sección refina las Secciones 2–11 y 23–25.
> No modifica el estado del código: `ipv7_mvp/` y `src/core/` permanecen en
> 9/9 tests unitarios + 5/5 validaciones multiproceso, sin regresiones.

## 35.1 Árbol de Availability ampliado

`Availability` no es un estado binario ni una simple enumeración. Se
descompone en siete dimensiones independientes:

```text
IPv7 Core
│
├── Identity
├── Channel
├── Session
├── Path
│    └── PATH_MTU
│
└── Availability
      │
      ├── Membership             ¿pertenece a la red?
      ├── Presence                ¿hay un "last known" reciente?
      ├── Response Capability     ¿puede responder en principio?
      ├── Expected Latency        ¿cuánto se espera que tarde?
      ├── Communication Window    ¿en qué ventana temporal puede escuchar/responder?
      ├── Wake Pattern            ¿con qué periodicidad despierta?
      └── Communication Mode      always-listening / intermittent / scheduled / on-demand / sleeping
```

Distinción clave (Sección 4 la introduce; aquí se formaliza):

```text
Presence ≠ Reachability ≠ Responsiveness
```

* **Presence**: el nodo declaró membresía y un último estado conocido.
* **Reachability**: existe una ruta/PATH_MTU utilizable ahora mismo.
* **Responsiveness**: el nodo, si se le contacta dentro de su ventana
  declarada, efectivamente responde.

Un nodo puede tener presencia sin ser alcanzable ahora, y ser alcanzable
sin tener ninguna sesión activa. Estas tres propiedades son independientes
y el Core debe poder representarlas por separado, sin colapsarlas en un
único booleano `connected`.

## 35.2 AVAILABLE_FOR — declaración por canal, no global

En lugar de una disponibilidad única por nodo, un nodo puede declarar
disponibilidad **por canal**, reutilizando la primitiva `Channel` ya
existente en el Core (Sección 15):

```text
Node X

AVAILABLE_FOR
├── control
├── query
└── emergency

NOT_AVAILABLE_FOR
└── bulk-data
```

```text
Sensor X

AVAILABLE_FOR
└── telemetry

WAKE
└── every 6 hours
```

El Core solo transporta la declaración (`channel_id → disponible/no
disponible + patrón`). No interpreta qué significa "bulk-data" o
"telemetry" — eso sigue siendo responsabilidad del Profile.

## 35.3 Integración con el Adaptive Stability Controller (Sección 11)

Antes de que el `Adaptive Stability Controller` compute o modifique un
`stability_score`, debe evaluarse una pregunta previa basada en
`Availability`:

```text
¿Debía responder según su Availability declarada?
        │
        ├── NO  → esperar (no se evalúa fallo, no afecta score)
        │
        └── SÍ
             │
             ▼
       ¿Respondió dentro de Expected Latency / Communication Window?
             │
             ├── SÍ → saludable (score se mantiene o mejora)
             │
             └── NO → recién aquí se evalúa como posible fallo
                        (pérdida, timeout, retry → Secciones 6–9)
```

Esto evita que el sistema de estabilidad (NORMAL → DEGRADED → UNSTABLE →
RESTRICTED → ISOLATED, Sección 12) castigue a un nodo que simplemente no
estaba obligado a responder todavía. `Availability` actúa como una guarda
(*gate*) que se evalúa **antes** de tocar `Health`/`stability_score`.

## 35.4 Principio arquitectónico de cierre

> **IPv7 no define cuándo un nodo está conectado. Define cómo puede
> participar en la comunicación.**

Un sensor anual, un teléfono móvil, un servidor permanente, un vehículo y
una sonda espacial pueden pertenecer a la misma red sin fingir que todos
están "conectados" de la misma manera. La red conoce membresía,
disponibilidad declarada y patrón esperado, y escucha — respondiendo
cuando corresponde, en lugar de preguntar constantemente "¿estás vivo?".

## 35.5 Dependencias antes de implementar

`Availability` sigue sin poder implementarse hasta que existan
`Container/Object` (para transportar la declaración de Availability como
un objeto estructurado, sin inventar un tipo de mensaje ad-hoc) e
`Identity` (para que `Membership` tenga sentido con un DID estable, no un
`node_id` efímero). El diseño de Container/Object (Sección 36) debe
revisarse teniendo en cuenta esta sección, para que `Availability` pueda
representarse más adelante como información estructurada sin contaminar
el Core con semántica de sensores, vehículos o satélites.

---

# 36. CONTAINER / OBJECT — FASE DE DISEÑO (NO IMPLEMENTAR TODAVÍA)

> ⚠️ **Solo diseño.** No escribir código de `Container`/`Object` hasta
> cerrar esta fase. `IDTLV` (`TYPE | LENGTH | ID | VALUE`, Sección 17) es
> el punto de partida heredado, **no** la decisión final.

## 36.1 Objetivo de esta fase

Antes de fijar el wire format de `TYPE | LENGTH | ID | VALUE`, responder
desde cero — sin asumir que el diseño heredado es correcto:

1. ¿Qué información mínima necesita el Core para transportar un objeto
   sin comprender su semántica?
2. ¿El `ID` es realmente necesario en todos los objetos?
3. ¿Todos los objetos necesitan `TYPE`?
4. ¿`LENGTH` puede reducirse o derivarse implícitamente?
5. ¿Un objeto puede referenciar otro objeto (por su `ID` local) sin
   introducir semántica en el Core?
6. ¿Cómo se representan deltas (cambios respecto a un objeto anterior)?
7. ¿Cómo se representan objetos fragmentados (mayores que `PATH_MTU`)?
8. ¿Cómo se relacionan los objetos dentro de un `Container`?
9. ¿Puede existir un `Container` sin `Object`s?
10. ¿Puede un `Object` existir fuera de un `Container`?
11. ¿El `Container` debe pertenecer obligatoriamente a una `Session`?
12. ¿Cuánto overhead mínimo se necesita para transportar 1, 10, 100 o
    255 objetos?
13. ¿Qué ocurre cuando un objeto (o el `Container` completo) supera
    `PATH_MTU`?
14. ¿Cómo se valida la integridad de objetos individuales, versus la
    integridad del paquete completo (SHA-256 ya existente, Sección 20)?
15. ¿Qué parte de todo esto pertenece al Core y cuál al Profile?

## 36.2 Método: comparar al menos 3 alternativas de wire format

No elegir un formato antes de comparar como mínimo **tres** alternativas
(la actual `IDTLV` puede ser una de ellas) según estos criterios:

```text
overhead            (bytes por objeto / por container)
flexibilidad         (¿admite tipos nuevos sin romper el parser?)
extensibilidad       (¿campos opcionales, versión de formato?)
fragmentación        (¿cómo se parte un objeto > PATH_MTU?)
delta / referencias  (¿puede un objeto referenciar o modificar otro?)
parsing              (complejidad de encode/decode en Python)
seguridad            (¿facilita o dificulta validar integridad parcial?)
MTU                  (comportamiento cuando el Container no cabe)
```

Documentar la comparación en una tabla antes de decidir.

## 36.3 Restricción de diseño (no negociable)

* **No** introducir semántica de aplicación (`temperature`, `vehicle`,
  `image`, etc.) en `Container`/`Object`. Esa separación (Sección 1,
  "Regla fundamental") se mantiene sin excepción.
* **No** escribir código hasta que este diseño esté cerrado.
* Mantener los 9/9 tests unitarios + 5/5 validaciones multiproceso como
  criterio de no regresión una vez que la implementación comience.
* Revisar la Sección 35 (Availability) antes de cerrar este diseño: el
  formato de `Container/Object` elegido debe poder transportar más
  adelante una declaración de `Availability` sin requerir un tipo de
  mensaje especial fuera de esta estructura.

---

# 37. Fase 3 — Diseño: Node Knowledge, Discovery y Availability

> No escribir código todavía. Esta fase es puramente de diseño.

La prueba real de dos nodos (A en UDP 9010, B en UDP 9011) demostró que:

* UDP, `route`, `path`, `sessions` y `channels` funcionan.
* `ping`/`send` fallan porque exigen que el destino esté en `peers`.
* `discover` falla por falta de `SO_BROADCAST` y apunta a un puerto fijo (`9000`).

Esto no es un conjunto de bugs a corregir con parches. Es evidencia
arquitectónica de que los conceptos de `peers`, `routes`, `identity` y
`availability` están mezclados.

## 37.1 Cuatro conceptos separados

IPv7 no debe confundir identidad, ubicación, alcanzabilidad y disponibilidad:

```text
¿QUIÉN ES?                  → IDENTITY
¿DÓNDE PODRÍA ESTAR?        → NODE KNOWLEDGE / LOCATOR
¿PUEDO LLEGAR HASTA ALLÍ?   → PATH / REACHABILITY
¿CUÁNDO Y CÓMO RESPONDE?    → AVAILABILITY
```

`PATH` ya resuelve alcanzabilidad. `DISCOVER` debe resolver búsqueda de
información de nodo, no presencia.

## 37.2 Node Knowledge

No debería mantenerse `peers` y `routes` como estructuras paralelas que se
contradicen.

```text
Node Knowledge
│
├── Identity
├── Locator
├── Membership
├── Path information
└── Availability
```

`ping`/`send` deberían resolver el destino mediante `Node Knowledge`, no
exigir un `peers` poblado por un broadcast de discovery.

## 37.3 Discovery = consulta, no heartbeat

`DISCOVER` no es "¿hay alguien ahí?". Es "estoy buscando a X" o
"¿quién conoce un locator para X?".

Las respuestas pueden provenir de:

* caché local;
* otro nodo;
* broadcast bajo demanda;
* query dirigida.

No hay broadcast periódico. El silencio no implica fallo.

## 37.4 Availability

Reemplaza el concepto binario `connected`:

```text
MEMBER       = YES
IDENTITY     = KNOWN
LOCATOR      = KNOWN
PATH         = POSSIBLE
AVAILABILITY = SCHEDULED
MODE         = SLEEP
WAKE_WINDOW  = ...
```

La red escucha. Cuando el nodo despierta y transmite, se entrega. La ausencia
de respuesta se compara contra el modelo de disponibilidad declarado.

## 37.5 Regla arquitectónica

> **Silence is not failure.** La ausencia de respuesta solo puede
> interpretarse como fallo cuando es inconsistente con el modelo de
> disponibilidad conocido, el contexto de comunicación y el tiempo de
> respuesta esperado.

## 37.6 Pregunta de diseño abierta

Si `PATH_DISCOVER → PATH_RESPONSE` ya demuestra que un nodo existe y es
alcanzable, ¿qué problema resuelve `DISCOVER` que `PATH` no pueda resolver?

La respuesta probable es: `DISCOVER` resuelve búsqueda de `locator`/`identity`
antes de conocer la ruta; `PATH` resuelve alcanzabilidad una vez se conoce el
locator. Si ambos se unifican bajo `Node Knowledge`, `DISCOVER` puede
convertirse en un mecanismo de consulta, no en un mensaje especial del Core.

## 37.7 Plan de Fase 3

1. Container/Object: cerrar el diseño del wire format.
2. Relaciones entre objetos sin introducir semántica en el Core.
3. Node Knowledge: unificar identidad, locator, ruta y disponibilidad.
4. Discovery: diseñar como consulta dirigida, no heartbeat.
5. Availability: formalizar como objeto transportado por el Core.
6. Decidir qué parte pertenece a Core, Profile o Application.

No implementar hasta que el modelo esté cerrado.

---

## 37.8 Node Knowledge — Conocer por identidad, observar por comportamiento

IPv7 no debe asumir que conoce a un nodo porque este lo declara. Debe
construir conocimiento progresivamente a partir de identidad, capacidades
declaradas y comportamiento observado.

### Tres pilares

```text
                         NODE KNOWLEDGE
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
      IDENTITY             DECLARATION          OBSERVATION
          │                    │                    │
      quién es            qué dice poder       qué demuestra
```

* **Identity**: ¿quién es? (puede evolucionar a DID, Ed25519, PQC).
* **Declaration**: ¿qué dice que puede hacer? No es verdad absoluta.
* **Observation**: ¿qué hemos visto realmente? Depende del contexto.

### Regla arquitectónica

> **Declared capability is information. Observed capability is evidence.**

Una declaración como `CPU = 16 cores` es información.
Una medición como `computational_probe = 37 ms` es evidencia.
Ninguna de las dos es verdad absoluta.

### Las métricas deben tener contexto

Una métrica no es un número. Conceptualmente incluye:

```text
metric:
    value
    unit
    timestamp
    observer
    context
```

### Cinco categorías conceptuales

```text
TRANSPORTE        latency, jitter, packet loss, retransmissions,
                  throughput, MTU
PROCESAMIENTO     request_response_time, object_processing_time,
                  computational_probe
DISPONIBILIDAD    last_seen, response_window, expected_latency,
                  wake_window, communication_mode
PROTOCOLO         protocol_version, supported_channels,
                  supported_object_formats, supported_security
COMPORTAMIENTO    timeouts, invalid responses, stability
```

Estas son categorías conceptuales. No significa que debamos crear cinco
sistemas.

### Primer contacto

No `HELLO, HELLO, HELLO`. Es:

```text
A
│ CONTACT
▼
B
│ BASIC RESPONSE
▼
A obtiene: identity, locator, capabilities, protocol info
```

Solo si lo necesita, A puede solicitar mediciones:

```text
A → METRIC REQUEST
B → METRIC RESPONSE
```

Muchas métricas se obtienen sin paquete adicional:

```text
A ───── request ─────> B
A <──── response ───── B
       RTT = observado
```

### Probes opt-in y mínimas

No benchear todo por defecto. Una métrica solo se obtiene si tiene utilidad:

* MTU → sí, para construir paquetes.
* Latencia → probablemente.
* Capacidad computacional → solo si la aplicación/ruta lo necesita.

### Computational Capability Probe

No `Proof of Work`. Es un probe de capacidad:

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
tiempo observado
```

Se puede reportar como `work_units / second`, pero siempre con:
`algorithm`, `work factor`, `timestamp` y `environment`.

### Conocimiento temporal

```text
Knowledge
│
├── current
├── recent
└── expired
```

La identidad puede ser persistente; el locator es temporal; la observación
es todavía más temporal.

### Modelo completo

```text
                         IDENTITY
                            │
                            ▼
                     NODE KNOWLEDGE
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
          LOCATOR       CAPABILITY     OBSERVATION
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                        DISCOVERY
                            │
                            ▼
                           PATH
                            │
                  ┌─────────┴─────────┐
                  ▼                   ▼
             REACHABILITY        PATH_MTU
                  │
                  ▼
             AVAILABILITY
                  │
                  ▼
               SESSION
                  │
                  ▼
               CHANNEL
                  │
                  ▼
              CONTAINER
                  │
                  ▼
                OBJECT
                  │
                  ▼
               PROFILE
                  │
                  ▼
             APPLICATION
```

### ¿Node Knowledge es un objeto?

Como modelo de información, sí. Como estructura obligatoria del Core, no.

```text
Profile / Control Plane
       │
       ▼
Node Knowledge
       │
       ▼
IDTLV Objects
       │
       ▼
Core transporta estructura, no interpreta conocimiento
```

### Principio distintivo

> **NETWORKS LEARN, THEY DO NOT ASSUME.**

Una red IPv7 no asume que:

* `address = identity`
* `silence = failure`
* `declaration = capability`
* `reachable = available`
* `available = permanently connected`

En cambio:

```text
IDENTITY
   +
OBSERVATION
   +
CONTEXT
   +
TIME
   ↓
NETWORK KNOWLEDGE
```

---

# 38. NODE KNOWLEDGE — MODELO REFINADO (First Contact y tres niveles de verdad)

> No escribir código todavía. Esta sección consolida el diseño conceptual
> que emerge de la validación real A → B → C (Sección 37 / Fase 2.5).
> `Node Knowledge` no es una nueva primitiva obligatoria del Core; es el
> conocimiento que un nodo construye **sobre** las primitivas del Core y
> las observaciones de red.

## 38.1 Relación con el Core

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

`Node Knowledge` vive fuera del Core. El Core transporta estructura;
`Node Knowledge` es la interpretación progresiva que un nodo —o la red—
hace sobre esa estructura, combinada con mediciones observadas.

Regla de diseño:

> **Core transporta estructura; Profiles y Node Knowledge interpretan.**

El Core no contiene una tabla semántica de "qué tan rápido es este nodo"
o "cuándo puede despertar". Mantiene las primitivas mínimas que permiten
construir y transportar ese conocimiento.

## 38.2 Tres niveles de verdad

Para evitar confiar ciegamente en lo que declara un nodo, y también para
no exigir pruebas obligatorias como condición previa a la comunicación,
IPv7 separa el conocimiento en tres niveles:

```text
DECLARED
   │
   ├── lo que el nodo dice de sí mismo
   ├── se acepta provisionalmente
   └── puede ser información, no verdad absoluta
   │
   ▼
OBSERVED
   │
   ├── lo que la red mide con sus propios paquetes
   ├── RTT, MTU, pérdida, latencia de respuesta, estabilidad
   └── funciona incluso si el otro no es IPv7
   │
   ▼
VERIFIED
   │
   └── lo que un procedimiento definido ha demostrado
```

Ejemplo:

```text
CPU:
    declared  = high
    observed  = medium (tiempo de respuesta promedio)
    verified  = probe-3 (CAPABILITY_PROBE concreto)
```

Reglas:

* **Declared is what a node says.**
* **Observed is what the network measures.**
* **Verified is what a defined procedure has demonstrated.**

## 38.3 Separación entre identidad, capacidad y verificación

```text
"Soy este nodo"       → Identity / authentication
"Soy capaz de X"      → Capability (declared)
"Realmente hice X"    → Verification (observed/proved)
```

La autenticidad de identidad no es lo mismo que la capacidad declarada.
Un nodo puede ser auténtico y no poder cumplir lo que dice. El sistema de
conocimiento debe mantener esas dimensiones separadas.

## 38.4 Principio de First Contact

First Contact no es un ping/pong. Es una presentación/sondeo inicial que
permite conocer progresivamente qué hay al otro lado.

```text
A → B
    FIRST CONTACT
    (probe mínimo)

B → A
    IDENTITY
    CAPABILITIES
    PROFILE_INFO
    AVAILABILITY
    LOCATOR
    PATH_INFO
    OBSERVABLE METRICS
```

A aprende, sin exigir nada:

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

Pero nada de esto es un examen obligatorio. `First Contact` devuelve lo
que B está dispuesto a compartir; A puede completar el conocimiento con
observaciones posteriores.

## 38.5 First Contact es progresivo

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

No se exige que todos los datos viajen en un único mensaje, ni que todos
los nodos respondan todo. El conocimiento crece según sea necesario.

## 38.6 Componentes de Node Knowledge

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

Ninguno de estos componentes es una primitiva del Core. Son construcciones
de conocimiento que se mantienen en cada nodo y pueden transportarse como
objetos a través del Core.

## 38.7 Knowledge levels

El conocimiento puede estar en distintos estados:

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

## 38.8 Métricas observables vs. declaradas vs. verificadas

### Observables (funcionan incluso contra nodos no-IPv7)

```text
RTT
packet loss
MTU
response time
handshake time
processing time observable
path quality
session stability
```

### Declaradas (lo que el nodo dice)

```text
IPv7 version: 0.x
Profiles: sensor, telemetry
Channels: control, query, telemetry
MTU: 1280
Availability: always / intermittent / scheduled / event-driven
Response capability: realtime / delayed / opportunistic
Expected response: < 100 ms
Processing capability: high
Communication mode: always-listening / sleeping
```

### Verificadas (mediante procedimiento opt-in)

```text
CAPABILITY_PROBE
    algorithm = X
    work factor = Y
    start → finish → elapsed_time
```

No se llama `Proof of Work` en el Core, porque no se busca castigar al
nodo por existir, sino medir capacidad cuando la aplicación/ruta lo
necesite. El procedimiento pertenece a Profile/Capability, no a Core.

## 38.9 Observable metrics funcionan contra cualquier nodo

A puede detectar:

```text
IPv7 response      → negociar IPv7
IPv4 / TCP / UDP     → registrar como external node
HTTP / otro protocolo → registrar como external service
silencio             → observar, no asumir fallo
```

Incluso un nodo que no hable IPv7 puede dejar mediciones observables.
Esto permite que IPv7 actúe como capa de conocimiento de red, no solo
como otro protocolo de transporte.

## 38.10 Reglas de diseño para Node Knowledge

1. **Progressive:** el conocimiento crece según se necesita, no exige un
   interrogatorio inicial.
2. **Contextual:** una métrica incluye valor, unidad, timestamp, observador
   y contexto.
3. **Perishable:** cada tipo de conocimiento caduca a su propia velocidad.
4. **Non-mandatory:** no se exige verificación para poder comunicarse.
5. **Core-agnostic:** el Core transporta estructura; Profiles definen qué
   significa cada medición y cómo ejecutar probes especializados.
6. **Trust-later:** `IPv7 does not require trust before communication; it
   progressively builds knowledge through communication.`

## 38.11 Próximo paso

Diseñar el wire format de `First Contact` y `Node Knowledge`, pero sin
implementarlo todavía. El objetivo de ese diseño será descubrir si se
puede construir casi completamente con las primitivas que ya existen
(`Identity`, `Channel`, `Session`, `Path`, `Container/Object`) o si
realmente se necesitan nuevos campos en el Core.

