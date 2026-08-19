# IPv7 — Container / Object Wire Format Design

> **Estado**: Fase 4 — diseño del modelo lógico e invariantes. Sin código
> todavía. No se fijan tamaños de campo ni layouts binarios concretos.
>
> Objetivo: definir qué debe poder expresar un `Container → Object` antes
> de decidir cuántos bytes ocupa cada campo.

---

## 1. Propósito

`Container → Object` es el mecanismo estructural del Core para
transportar información de manera que:

* El Core pueda parsear, validar, segmentar y reenviar sin saber qué
  representa cada objeto.
* Los Profiles puedan asignar significado a los objetos sin modificar el
  Core.
* El mismo mecanismo sirva para First Contact, Node Knowledge,
  Availability, Profiles, mediciones y probes.

---

## 2. Container es transporte estructural

El `Container` debe proporcionar al Core la información necesaria para
manejar objetos:

```text
Container
├── object count
├── byte boundaries
├── structural integrity boundary
└── local ID space
```

El Core necesita saber:

* Cuántos objetos contiene.
* Dónde empieza y termina cada objeto.
* Cuándo el contenedor está completo o corrupto.
* Que los IDs son locales a este contenedor.

El Core **no necesita saber**:

* Si un objeto es CPU, sensor, identidad, disponibilidad, relación o
  probe.
* El significado de los bytes dentro del `Value`.
* La semántica de cualquier relación entre objetos.

---

## 3. Object es la unidad semántica mínima

Cada objeto debe poder existir, parsearse y transportarse de forma
independiente:

```text
Object
├── ID
├── Type
├── Length
└── Value
```

* **ID**: identificador local dentro del contenedor.
* **Type**: categoría estructural que indica cómo parsear el valor.
* **Length**: tamaño del valor en bytes.
* **Value**: contenido opaco para el Core.

El `Type` dice al receptor cómo interpretar **estructuralmente** el
objeto (por ejemplo: bytes crudos, texto, número, lista de IDs,
contenedor anidado). No le dice al Core que esos bytes significan
"temperatura" o "capacidad de CPU".

---

## 4. El ID es local al Container

```text
Container
 ├─ Object ID=0
 ├─ Object ID=1
 ├─ Object ID=2
 └─ Object ID=3
```

Reglas:

* Un ID no identifica al nodo, no es una dirección, no es un DID.
* Es simplemente "el objeto número N dentro de este contexto".
* Permite que otros objetos dentro del mismo contenedor lo referencien.
* No requiere coordinación global.

La localidad del ID libera a IPv7 de tablas globales de direccionamiento
de objetos.

---

## 5. Las relaciones no son primitivas del Core

Un objeto puede referirse a otro mediante su ID local:

```text
Object 3
   Value: { references: [7] }
```

Pero la interpretación de esa referencia pertenece al Profile:

* "Esta medición corresponde a este recurso."
* "Esta capacidad fue verificada por este probe."
* "Este dato depende de este otro dato."

El Core solo ve IDs locales y estructura. El Profile ve relaciones.

Esto evita que `RELATION` se convierta en una primitiva semántica
obligatoria del Core.

---

## 6. KNOWLEDGE debe poder componerse

No creamos tipos especiales del Core como `CPU_KNOWLEDGE_OBJECT` o
`LATENCY_KNOWLEDGE_OBJECT`.

En su lugar, un objeto de conocimiento es un objeto genérico cuyo valor
puede contener propiedades, source, truth, confidence y lifetime:

```text
Object
   ├── property / value
   ├── source
   ├── truth
   ├── confidence
   └── expiry
```

Ejemplos de objetos de conocimiento transportables:

```text
cpu_cores = 8
mtu = 1280
latency = 14 ms
availability = scheduled
profile = sensor.v1
```

El mismo mecanismo genérico sirve para cualquier dimensión de Node
Knowledge, incluso para conceptos que todavía no hemos imaginado.

---

## 7. Un Container puede transportar conocimiento parcial

First Contact es progresivo. Un solo Container no necesita contener el
perfil completo de un nodo.

Primer contacto:

```text
Container
 ├── Identity
 ├── Locator
 ├── MTU
 ├── Latency
 └── Profile
```

Segundo contacto:

```text
Container
 ├── CPU
 ├── Memory
 ├── Capability
 └── Availability
```

Más tarde:

```text
Container
 └── Verified Capability
```

El conocimiento crece incrementalmente a través de múltiples Containers.

---

## 8. Container anidados

Un objeto de tipo "container anidado" permitiría agrupar objetos
relacionados sin romper el modelo:

```text
Container
 ├── Object: knowledge-group
 │    └── Value: Container
 │         ├── Object: cpu declared
 │         ├── Object: cpu observed
 │         └── Object: cpu verified
 │
 └── Object: another-group
      └── Value: Container
           ├── Object: latency
           └── Object: throughput
```

Esto es opcional. La Fase 4 debe decidir si los contenedores anidados
añaden complejidad innecesaria o si simplifican la representación de
perfiles y grupos de conocimiento.

---

## 9. Object ordering

El orden de los objetos dentro de un Container debe ser relevante solo
para el parser estructural, no para la semántica.

Regla:

> Un receptor no debe asumir que el primer objeto es siempre la
> identidad o que cierto tipo de objeto aparece en una posición fija.
> Cada objeto se identifica por su Type y, si es necesario, por
> relaciones explícitas dentro del Container.

Esto permite reconstruir conocimiento parcial y reordenado sin perder
significado.

---

## 10. Optional objects

Cualquier objeto debe poder omitirse sin romper el Container.

Ejemplo: un contacto mínimo puede contener solo identidad y locator;
CPU, availability y profiles pueden estar ausentes.

```text
Container
 ├── Object: identity
 └── Object: locator
```

Regla:

> La ausencia de un objeto no implica ausencia del conocimiento. Solo
> implica que este Container no lo transporta.

---

## 11. Unknown objects

Un receptor debe poder ignorar objetos cuyo Type no reconozca.

Regla:

> Forward compatibility: tipos desconocidos se omiten, no rechazan el
> Container completo.

Esto permite que nuevos Profiles y nuevas capacidades evolucionen sin
romper nodos antiguos.

---

## 12. Extension mechanism

El mecanismo de extensión no debe requerir una versión central del
protocolo. Opciones a evaluar:

1. **Tipos numerados**: el Type indica el parser estructural. Los
   perfiles acuerdan el significado fuera de banda.
2. **Namespace + Type**: un objeto identifica su namespace, permitiendo
   que distintos Profiles usen tipos sin colisionar.
3. **Tipo genérico + descriptor interno**: un solo Type estructural para
   "objeto de conocimiento", cuyo Value contiene un descriptor semántico
   interpretado por el Profile.

La Fase 4 debe comparar estas opciones antes de congelar el wire format.

---

## 13. Fragmentation

Un objeto o Container completo puede exceder PATH_MTU.

Decisiones pendientes:

* ¿El Core fragmenta Containers o es responsabilidad del Profile/
  aplicación?
* ¿Un objeto puede cruzar límites de paquetes?
* ¿Se permite referenciar un objeto fragmentado por ID?

Para el MVP inicial se puede optar por: "el Container completo debe
entrar en un paquete"; la fragmentación avanzada se pospone. Pero el
formato no debe impedirla en el futuro.

---

## 14. Integrity boundaries

El Container define una unidad de integridad estructural:

* Si el Container está corrupto o incompleto, el receptor lo descarta.
* Si un objeto interno está corrupto, el receptor puede descartar ese
  objeto o todo el Container.
* El Core valida integridad estructural; el Profile valida integridad
  semántica.

El SHA-256 del paquete (ya existente) protege el Container durante el
transporte. Si se necesita integridad por objeto en el futuro, será un
Profile concern.

---

## 15. Container limits

Límites conceptuales a decidir:

* Tamaño máximo de un Container (determinado por PATH_MTU o por
  política).
* Número máximo de objetos por Container.
* Tamaño máximo de un Object.
* Rango de IDs locales.

Estos límites afectan directamente la eficiencia y la escalabilidad, pero
dejan de ser urgentes hasta que se fije el wire format.

---

## 16. Knowledge representation

Representación lógica de un ítem de Node Knowledge:

```text
Object: knowledge-item
├── name        (ej. "cpu_cores", "latency")
├── value       (8, "14 ms", "sensor.v1")
├── source      (B, A, probe-3)
├── truth       (declared / observed / verified)
├── confidence  (low / medium / high)
└── expiry      (timestamp o lifetime)
```

El Core ve un objeto con Type y Value. El Profile interpreta cada campo.

Esto permite transportar:

```text
Container
 ├── Object: identity
 ├── Object: locator
 ├── Object: availability
 ├── Object: mtu measurement
 ├── Object: latency measurement
 ├── Object: cpu declared
 └── Object: profile declared
```

---

## 17. First Contact representation

First Contact se representa como un Container con un subconjunto mínimo
inicial de objetos:

```text
Container (first contact)
 ├── Object: identity
 ├── Object: locator
 ├── Object: protocol version
 ├── Object: supported channels
 └── Object: available profiles
```

Opcionalmente puede incluir observaciones iniciales:

```text
 ├── Object: mtu measurement
 └── Object: latency measurement
```

Nunca requiere probes ni verificaciones en el primer intercambio.

---

## 18. Profile representation

Un Profile se describe mediante objetos estándar de conocimiento:

```text
Container (profile declaration)
 ├── Object: profile name
 ├── Object: profile version
 ├── Object: supported object types
 └── Object: capability requirements
```

El Core transporta estos objetos como cualquier otro. El Profile los
interpreta como "este nodo entiende el perfil sensor.v1".

---

## 19. Probe representation

Un probe se representa como intercambio de Containers:

```text
A → B
    Container
     ├── Object: probe request
     │     ├── probe type
     │     ├── algorithm
     │     ├── difficulty
     │     └── constraints

B → A
    Container
     ├── Object: probe accept / refuse
     │
     └── (si acepta)
          Object: probe result
                ├── algorithm
                ├── work
                ├── elapsed
                └── timestamp
```

El resultado vuelve a almacenarse como Knowledge Object con
`truth = verified`.

---

## 20. Availability representation

Availability es un ítem de conocimiento más:

```text
Container
 └── Object: availability
       ├── value      = scheduled
       ├── source     = B
       ├── truth      = declared
       ├── confidence = medium
       └── expiry     = 3600 s
```

Esto conecta directamente con la Sección 35 de
`ARQUITECTURA_NUEVO_INTERNET.md`: Availability se transporta como objeto
estructurado, sin requerir un tipo de mensaje ad-hoc del Core.

---

## 21. Nodo no-IPv7 representation

Un nodo no-IPv7 no produce Containers IPv7, pero IPv7 puede registrarlo
como Knowledge:

```text
Node Knowledge for external IPv4 node
 ├── Object: protocol observed = IPv4
 ├── Object: locator observed = 192.168.x.x
 ├── Object: transport observed = UDP
 ├── Object: availability observed = reachable
 ├── Object: latency observed = 4.2 ms
 └── Object: path_mtu observed = 1280
```

Cada ítem lleva `truth = observed` y su propia fuente.

---

## 22. Compatibility

Reglas para evitar que evoluciones futuras rompan nodos existentes:

* Objetos desconocidos se ignoran.
* Nuevos Types no invalidan Containers antiguos.
* Nuevos campos dentro de un Value deben ser opcionales.
* Eliminación de Types obsoletos es responsabilidad del Profile, no del
  Core.

---

## 23. Forward compatibility

El formato debe permitir que un nodo antiguo reciba un Container con
objetos de tipos que no entiende y aun así:

1. Parsear el Container estructuralmente.
2. Extraer los objetos que sí reconoce.
3. Reenviar o ignorar los objetos desconocidos.

Esto requiere que el Type permita al parser saltar el objeto sin saber su
semántica.

---

## 24. Security implications

* El Core valida integridad estructural (límites, tamaños, IDs locales).
* El Profile valida semántica y confianza.
* Un objeto malicioso no debería poder hacer que el Core consuma
  recursos arbitrarios (bucles, buffers gigantes, IDs fuera de rango).
* `Length` debe verificarse antes de reservar memoria.
* Objetos anidados o referencias circulares deben tener límite de
  profundidad si se permiten contenedores anidados.

---

## 25. Canonical encoding

Para tests, firmas y comparaciones, puede ser útil definir una
representación canónica del Container:

* Orden de objetos normalizado.
* Campos en orden fijo.
* Sin padding opcional.

Esto es una decisión de implementación, no necesariamente una propiedad
obligatoria del wire format.

---

## 26. Wire-format invariants (resumen)

Cualquier wire format concreto debe garantizar:

1. **Container como unidad estructural**: el Core puede parsearlo sin
   conocer semántica.
2. **Object independiente**: cada objeto tiene ID, Type, Length, Value.
3. **ID local**: los IDs son índices dentro del Container.
4. **Relaciones por Profile**: las referencias entre objetos son opacas
   para el Core.
5. **Knowledge componible**: cualquier ítem de Node Knowledge se
   representa como un objeto genérico.
6. **Conocimiento parcial**: un Container puede omitir objetos sin
   romperse.
7. **Tipos desconocidos ignorables**: forward compatibility.
8. **Extensibilidad**: nuevos Profiles añaden tipos sin cambiar el Core.
9. **Integridad estructural**: límites, tamaños y IDs verificables.
10. **No semántica de aplicación en el Core**: el Core nunca interpreta
    CPU, sensor, vehicle, etc.

---

## 27. Comparación de alternativas de wire format

### 27.1 Cuatro candidatos

| Alternativa | Estructura | Ventaja principal | Problema |
|-------------|------------|-------------------|----------|
| 1. IDTLV heredado | TYPE + LENGTH + ID + VALUE | Simple, compacto, compatible con lo existente | El Container queda poco definido |
| 2. TLV + ID local | TYPE + LENGTH + ID + VALUE dentro de Container | Muy flexible, streaming natural | Hay que definir claramente límites del Container |
| 3. Header + Offset Table | Header → tabla de offsets → objetos | Acceso aleatorio extremadamente rápido | Más complejidad, menos natural para streaming |
| 4. Container + IDTLV híbrido | Container Header → Objects IDTLV | Conserva simplicidad + estructura explícita | Algo más de overhead |

### 27.2 Candidato inicial: alternativa 4

El candidato inicial es el **híbrido Container + IDTLV** porque separa
dos problemas diferentes:

```text
CONTAINER
   │
   │ estructura del conjunto
   ▼
OBJECT
   │
   │ estructura individual
   ▼
VALUE
   │
   │ significado
   ▼
PROFILE
```

El Core entiende Container y Object. El Profile entiende Value.

Esto encaja exactamente con:

> Core entiende estructura. Profile entiende significado.

### 27.3 ¿ID universal o condicional?

Opción A: todos los objetos tienen ID.

```text
Container
 ├── Object ID=0  Identity
 ├── Object ID=1  Locator
 ├── Object ID=2  MTU
 └── Object ID=3  Latency
```

Opción B: distinguir `referenced` / `unreferenced`.

```text
Object
 ├── referenced    → tiene ID
 └── unreferenced  → sin ID, ahorra bytes
```

Inclinación inicial: **mantener ID universal**.

Razones:

* La uniformidad simplifica parser, tests y razonamiento.
* El byte ahorrado no compensa la complejidad de tener dos formatos.
* Cualquier objeto puede necesitar ser referenciado más tarde, incluso
  aquel que hoy parece aislado.
* Forward compatibility mejora si todos los objetos tienen el mismo
  esqueleto.

### 27.4 El Container como contexto

```text
Container #1
 ├── Object 0
 ├── Object 1
 ├── Object 2
 └── Object 3
```

Los IDs solo tienen significado dentro de ese Container. Por tanto:

```text
ID = 3
```

no significa nada fuera de `Container X`.

Esto permite que las relaciones sean locales y efímeras:

```text
Object 0 = Node
Object 1 = CPU
Object 2 = Measurement
Object 3 = Probe Result
```

Un Profile puede interpretar:

```text
Object 2  → describes → Object 1
Object 3  → verifies  → Object 1
```

El Core jamás necesita saber qué significan `describes` o `verifies`.

### 27.5 Offset Table: opcional, no fundamento

La alternativa 3 es atractiva para acceso aleatorio:

```text
Container
│
├── Header
├── Offset[0]
├── Offset[1]
├── Offset[2]
├── ...
│
├── Object 0
├── Object 1
└── Object 2
```

Pero introduce dependencia de una tabla global del Container antes de
poder recorrer los objetos. Esto perjudica propiedades más importantes
para IPv7:

* streaming;
* procesamiento incremental;
* dispositivos pequeños;
* routers transparentes que no interpretan contenido;
* Containers parcialmente recibidos;
* fragmentación futura;
* forwarding sin reconstrucción.

Conclusión: **Offset Table se deja como extensión opcional, no como
fundamento del formato**.

---

## 28. Prueba de fuego: ¿un solo mecanismo para todo?

Antes de elegir bytes, el formato debe poder representar todos estos
casos sin que el Core conozca los conceptos:

### Caso A — First Contact

```text
CONTACT
Identity
Locator
Transport capability
```

### Caso B — nodo desconocido

```text
Observation
Observed protocol
Observed response
Observed latency
```

### Caso C — Node Knowledge

```text
CPU = 8
truth   = declared
confidence = medium
expiry  = ...
```

### Caso D — medición

```text
Latency = 12.4 ms
truth  = observed
source = measurement
```

### Caso E — capability

```text
AES-GCM throughput = X
truth = verified
source = probe
```

### Caso F — Availability

```text
awake
available_for = telemetry
wake_window = ...
```

### Caso G — Profile

```text
Profile = sensor
Version = 3
```

### Caso H — nodo no-IPv7

```text
Observed endpoint
Observed protocol
Observed behavior
```

Si el formato requiere un tipo especial de paquete para alguno de estos
casos, el diseño está fallando.

---

## 29. Evidence: referencias entre objetos

Cada ítem de conocimiento lleva:

```text
value
source
truth
confidence
expiry
```

Pero cuando algo está verificado, conviene poder preguntar: **¿verificado
por qué?**

La respuesta puede ser otra referencia local:

```text
Object 1
CPU = 8
truth = verified

Object 2
Probe Result

Object 1 ← Object 2  (evidence)
```

El Core solo ve IDs locales. El Profile decide que Object 2 constituye
evidence de Object 1.

Esto permite construir una cadena progresiva sin convertirla en
obligación:

```text
DECLARED
   ↓
OBSERVED
   ↓
MEASURED
   ↓
PROBED
   ↓
VERIFIED
```

Y recuerda:

> VERIFIED no es necesariamente el siguiente escalón de DECLARED.
> Son estados epistemológicos independientes que pueden coexistir.

---

## 30. Reglas congeladas antes de decidir bytes

### Container

Debe proporcionar:

```text
count
length
objects
local namespace
structural integrity
```

### Object

Debe proporcionar:

```text
ID
TYPE
LENGTH
VALUE
```

### ID

Debe ser:

```text
local
unique within Container
non-addressing
non-identity
referenceable
```

### Type

Debe definir:

```text
cómo interpretar estructuralmente el Object
```

pero no obligar al Core a conocer su semántica.

### Value

Debe ser opaco para el Core.

### Unknown Types

El Core debe poder:

```text
parse → validate → skip → continue
```

### Ordering

La orden de los objetos no debe tener significado implícito.

### Nesting

Debe ser posible, pero no obligatorio.

### Fragmentation

El formato no puede depender de recibir el Container completo de una
vez.

### Canonicalization

Debe existir una representación determinística cuando un Profile
necesite firmar o generar un commitment.

---

## 31. Matriz de estrés

| Requisito | IDTLV | TLV+ID | Offset Table | Híbrido |
|-----------|-------|--------|--------------|---------|
| Streaming | ✅ | ✅ | ⚠️ | ✅ |
| Forward compatibility | ✅ | ✅ | ✅ | ✅ |
| Fragmentación | ✅ | ✅ | ⚠️ | ✅ |
| Referencias locales | ✅ | ✅ | ✅ | ✅ |
| Parser mínimo | ✅ | ✅ | ❌ | ✅ |
| Acceso aleatorio | ⚠️ | ⚠️ | ✅ | ⚠️ |
| Bajo overhead | ✅ | ✅ | ❌ | ✅ |
| Routers transparentes | ✅ | ✅ | ⚠️ | ✅ |
| Containers parciales | ✅ | ✅ | ⚠️ | ✅ |
| Profiles extensibles | ✅ | ✅ | ✅ | ✅ |

### Lectura de la matriz

* **Híbrido Container + IDTLV** no gana en acceso aleatorio, pero
  conserva todas las propiedades que IPv7 prioriza: streaming,
  fragmentación, parser mínimo, routers transparentes, Containers
  parciales.
* **Offset Table** gana en acceso aleatorio, pero pierde en simplicidad,
  streaming y procesamiento parcial.
* **IDTLV heredado** y **TLV+ID** son viables, pero dejan menos
  estructura explícita al Container.

---

## 32. Fase 4.2 — Prueba de fuego del modelo

Objetivo: intentar romper el modelo antes de congelar bytes. Si el
candidato híbrido sobrevive a estos casos, podemos proceder al layout
binario con confianza.

Candidato:

```text
PACKET
└── CONTAINER
    ├── OBJECT
    │   ├── ID
    │   ├── TYPE
    │   ├── LENGTH
    │   └── VALUE
    ├── OBJECT
    └── OBJECT
```

### 32.1 A. First Contact mínimo

```text
Container
 ├─ Object ID=1  Type=CONTACT
 │      Value=...
 └─ Object ID=2  Type=...
        Value=...
```

Pregunta crítica: ¿puede el Core transportar esto sin saber qué
significa `CONTACT`?

Respuesta: **sí**. El Core solo ve `Container → Objects → estructura
válida`. El Profile interpreta `Type=CONTACT`.

### 32.2 B. Nodo completamente desconocido

```text
Object ID=7
Type=0x91
Length=...
Value=...
```

El receptor debe poder:

1. Validar que el objeto está estructuralmente bien formado.
2. Conservarlo si quiere.
3. Ignorarlo si no reconoce el Type.
4. Continuar procesando los demás objetos.
5. Reenviarlo sin comprenderlo.

Propiedad fundamental:

> **Unknown ≠ Invalid.** Un objeto desconocido puede ser perfectamente
> válido.

### 32.3 C. Node Knowledge

```text
Container
 ├─ Object 1  property
 ├─ Object 2  value
 ├─ Object 3  source
 ├─ Object 4  truth
 ├─ Object 5  confidence
 └─ Object 6  expiry
```

Pregunta: ¿necesitamos que cada campo sea un Object separado?

Respuesta: **no siempre**. Podemos tener un Knowledge Object cuyo
Value contiene una estructura interna definida por el Profile:

```text
Knowledge Object
 ├── property
 ├── value
 ├── source
 ├── truth
 ├── confidence
 └── expiry
```

Regla:

> **Object es la unidad semántica externa; su Value puede contener una
> estructura interna definida por el Profile.**

Esto evita inflar el Container con objetos que nunca necesitarán ser
referenciados por separado.

### 32.4 D. Measurement

```text
Object
 ├─ Type = Measurement
 └─ Value = Profile-defined
```

Dentro del Value:

```text
property = cpu_response_time
value    = 4.8
unit     = ms
source   = observation
truth    = observed
confidence = ...
expiry   = ...
```

La misma maquinaria sirve para CPU, memoria, MTU, latencia, pérdida,
throughput, criptografía, sensores, almacenamiento.

### 32.5 E. Capability Probe

```text
PROBE_REQUEST
       ↓
     Node B
       ↓
PROBE_RESULT
       ↓
KNOWLEDGE
```

Resultado posible:

```text
Capability:
    cpu.compute.class = X
    crypto.ed25519 = supported
    max_container = Y
```

Distinción clave:

* **Measurement**: valor temporal observado.
* **Capability**: propiedad demostrada bajo condiciones concretas.

`CPU = 73 %` es una measurement. "Puede ejecutar algoritmo X bajo
condiciones Y" es una capability.

### 32.6 F. Availability

```text
AVAILABLE_FOR = telemetry
WINDOW = 18:00–22:00
MODE = intermittent
```

No se inventa otro protocolo. Es otro conjunto de Objects interpretados
por un Profile. Por tanto:

* Node Knowledge
* Availability
* Probe
* Measurement
* Profile
* First Contact

pueden viajar dentro de la misma infraestructura `Container → Object`.

### 32.7 G. Evidence

```text
Object 10
    capability = crypto.ed25519
    truth = verified

Object 11
    evidence → Object 15

Object 15
    probe-result = ...
```

```text
10 ─────► 15
```

El Core solo sabe que Object 10 referencia Object 15. El Profile decide
que Object 15 constituye evidence de Object 10.

Esto confirma:

> **Las relaciones pertenecen al modelo de objetos/Profile, no al
> Core.**

### 32.8 H. Nodo no-IPv7

B es un nodo IPv4. A observa y registra:

```text
source = observation
truth = observed

UDP reachable = true
latency = 8.2 ms
MTU = 1500
response behavior = ...
```

Node Knowledge no equivale necesariamente a IPv7 Node Knowledge. IPv7
puede conocer el mundo exterior sin exigir que el mundo sea IPv7.

### 32.9 I. Forward compatibility extrema

Caso especialmente duro:

> Un nodo antiguo recibe un Container creado por un nodo futuro que
> contiene 20 tipos de objetos que jamás ha visto. Debe poder
> reenviarlo, ignorar lo desconocido y seguir funcionando correctamente.

Si el diseño pasa esto, tenemos algo más importante que un TLV eficiente:
un mecanismo de evolución del protocolo.

---

## 33. Reducción del Core

¿Podemos eliminar todos estos nombres del Core?

```text
CONTACT
KNOWLEDGE
CPU
SENSOR
AVAILABILITY
PROBE
PROFILE
CAPABILITY
MEASUREMENT
```

Y dejar al Core solamente:

```text
Packet
Container
Object
ID
Type
Length
Value
Reference
```

Si la respuesta es sí, la arquitectura es extraordinariamente limpia:

```text
                 CORE
                   │
        ┌──────────┴──────────┐
        │                     │
     STRUCTURE             TRANSPORT
        │                     │
 Packet / Container / Object / ID
        │
        ▼
     PROFILE
        │
   ┌────┼─────┬──────┬───────┐
   ▼    ▼     ▼      ▼       ▼
Contact Knowledge Probe Availability ...
```

### 33.1 Type no es semántica del Core

El Core necesita saber que `Type = 37` es un tipo estructuralmente
válido. No necesita saber que 37 significa CPU, Probe o Availability.

Eso pertenece al Profile/namespace correspondiente.

---

## 34. Recién después: bytes

Cuando el modelo supere la prueba de fuego, se puede congelar:

```text
Container Header
Object Header
ID
Type
Length
Value
Reference
```

Y comparar layouts como:

```text
Alternativa 1:  TYPE | LENGTH | ID | VALUE
Alternativa 2:  ID   | TYPE   | LENGTH | VALUE
Alternativa 3:  TYPE | ID     | LENGTH | VALUE
```

Criterios de evaluación:

```text
tamaño mínimo
alineación
streaming
parsing incremental
fragmentación
nesting
canonicalización
límites
MTU
forward compatibility
relay sin interpretar
almacenar/reconstruir objetos
coste de CPU
```

No se elige el orden por intuición. Se mide contra los casos A–I.

---

## 35. Fase 4.3 — Prueba formal A–I

Hipótesis de trabajo:

```text
PACKET
└── CONTAINER
    ├── OBJECT
    │   ├── ID
    │   ├── TYPE
    │   ├── LENGTH
    │   └── VALUE
    ├── OBJECT
    └── OBJECT
```

Con:

* **ID** = índice local al Container.
* **TYPE** = clasificación estructural / namespace.
* **LENGTH** = tamaño de VALUE.
* **VALUE** = opaco para el Core.
* **REFERENCE** = relación local por ID.

Regla de oro:

> El Core solo puede responder: "¿está estructuralmente bien formado?"
> Nunca: "¿qué significa?"

---

### 35.1 A — CONTACT

```text
Container #1
│
└── Object #1
    Type = CONTACT
    Value = {...}
```

El Core verifica:

```text
✓ Container válido
✓ Object válido
✓ Type codificado correctamente
✓ Length consistente con Value
✓ Value transportable
```

El Core no necesita saber qué es `CONTACT`.

**Veredicto: PASS.**

---

### 35.2 B — UNKNOWN

```text
Container
├── Object #1  Type=CONTACT
├── Object #2  Type=0xA7
└── Object #3  Type=0xB2
```

El nodo antiguo no conoce `0xA7` ni `0xB2`.

Flujo del Core:

```text
parse
 ↓
validate structure
 ↓
unknown type
 ↓
ignore / preserve / forward
```

Nunca:

```text
unknown → malformed
```

**Invariante I-11: Unknown preservation**

> Un relay transparente debe poder transportar Objects desconocidos.

**Invariante I-12: Unknown type ≠ invalid object**

> Un Type desconocido no invalida el Object ni el Container.

**Veredicto: PASS.**

---

### 35.3 C — KNOWLEDGE

```text
Object
└── Value
    ├── property
    ├── value
    ├── source
    ├── truth
    ├── confidence
    └── expiry
```

No es necesario que cada campo sea un Object separado. El Profile define
la estructura interna del Value.

Regla:

> **Object es la unidad semántica externa; su Value puede contener una
> estructura interna definida por el Profile.**

**Veredicto: PASS.**

---

### 35.4 D — MEASUREMENT

```text
Object
Type = Measurement
Value =
    metric = latency
    value  = 4.82
    unit   = ms
```

Mañana puede ser:

```text
metric = cpu
metric = memory
metric = mtu
metric = throughput
metric = packet_loss
```

El transporte no cambia.

**Veredicto: PASS.**

---

### 35.5 E — PROBE / CAPABILITY

```text
PROBE_REQUEST
       ↓
PROBE_RESULT
       ↓
Measurement or Capability
       ↓
Knowledge
```

Distinción:

* "Tardó 12 ms en ejecutar X" → **Measurement**.
* "Puede ejecutar X bajo estas condiciones" → **Capability**.

El probe produce un objeto; el Profile decide si se trata de una
measurement o una capability.

**Veredicto: PASS.**

---

### 35.6 F — Availability

```text
Object
Type = Availability
Value =
    channel = telemetry
    mode    = intermittent
    window  = ...
```

El Core no sabe qué es Availability. El Profile sí. No se requiere un
mecanismo especial.

**Veredicto: PASS.**

---

### 35.7 G — Evidence

```text
Container
│
├── Object #4
│   capability = X
│
└── Object #7
    evidence → #12

Object #12
    probe-result = ...
```

La referencia `#4 → #12` es estructural. El Profile interpreta:

> "El objeto #12 constituye evidence del objeto #4."

**Veredicto: PASS.**

---

### 35.8 H — Nodo no-IPv7

A observa a B (IPv4) y registra:

```text
B
├── IPv4 reachable
├── UDP response
├── MTU ≈ 1500
├── latency ≈ 8 ms
└── behavior = ...
```

B no necesita conocer IPv7. A puede construir Node Knowledge basándose
exclusivamente en observaciones.

Implicación:

> **Node Knowledge no equivale a IPv7 Node Knowledge.**

IPv7 puede construir conocimiento sobre entidades que no participan del
protocolo.

**Veredicto: PASS.**

---

### 35.9 I — Nodo futuro

Nodo viejo `Core v1` recibe:

```text
Container
├── Type 1
├── Type 2
├── Type 87
├── Type 104
├── Type 155
├── ...
└── Type 230
```

El nodo viejo conoce solo `Type 1` y `Type 2`.

Debe poder:

```text
parse
validate
ignore unknown
forward
```

sin romper el Container.

Condición adicional:

> Un relay que no interpreta un Object no debe necesitar reconstruir su
> contenido semántico para reenviarlo.

Esto favorece al diseño híbrido: el relay puede operar a nivel de bytes
estructurales.

**Veredicto: PASS.**

---

## 36. Parse ≠ Interpret

El Core **parsea**. El Profile **interpreta**.

```text
CORE
 parse
 validate structure
 skip unknown
 forward

PROFILE
 interpret Type
 interpret Value
 build Knowledge
 run Probes
```

Reglas:

* **Parse** = reconocer estructura.
* **Interpret** = asignar significado.
* Un relay puede parsear sin interpretar.

---

## 37. Relay vs. Terminator

### 37.1 Nodo terminador

```text
receive
  ↓
parse
  ↓
interpret
  ↓
process
```

Puede descartar objetos desconocidos si no los necesita.

### 37.2 Nodo relay

```text
receive
  ↓
validate structure
  ↓
forward
```

No debería necesitar interpretar Value.

### 37.3 Implicación

El formato debe permitir que un relay opere sin conocer ningún Type
específico. Esto es esencial para routers transparentes y forwarding sin
reconstrucción.

---

## 38. Invariantes del wire format (versión ampliada)

1. Container como unidad estructural.
2. Object con ID, Type, Length, Value.
3. ID local al Container.
4. Relaciones por Profile, no por Core.
5. Knowledge componible.
6. Conocimiento parcial permitido.
7. Tipos desconocidos ignorables.
8. Extensibilidad sin cambiar el Core.
9. Integridad estructural verificable.
10. No semántica de aplicación en el Core.
11. **Unknown preservation**: relay transparente transporta Objects
    desconocidos.
12. **Semantic opacity**: el Core nunca interpreta Value.
13. **Structural validation**: el Core valida solo estructura,
    límites, IDs y referencias.
14. **Interpretation isolation**: toda interpretación semántica pertenece
    a Profile / Application.

---

## 39. Candidatos byte-level

Una vez congeladas las reglas, se pueden comparar layouts:

### 39.1 Formato A

```text
TYPE | LENGTH | ID | VALUE
```

### 39.2 Formato B

```text
ID | TYPE | LENGTH | VALUE
```

### 39.3 Formato C

```text
TYPE | ID | LENGTH | VALUE
```

### 39.4 Cuarta posibilidad: tabla de IDs

```text
Container
├── Header
├── Object table
│   ├── ID → offset
│   ├── ID → offset
│   └── ID → offset
│
└── Object data
```

Parecía peor para streaming, pero no se descarta sin medir. Puede
existir como extensión opcional sin contaminar el formato base.

---

## 40. Fase 4.4 — Comparación byte-level

Regla metodológica:

> No optimicemos primero para ahorrar bytes. Optimicemos primero para
> que el formato sea inequívoco, parseable en streaming, extensible y
> extremadamente barato de procesar. Después comprimimos lo que
> corresponda.

---

### 40.1 Layouts candidatos

```text
A:  TYPE | LENGTH | ID | VALUE
B:  ID   | TYPE   | LENGTH | VALUE
C:  TYPE | ID     | LENGTH | VALUE
D:  Container + ID/Offset Table + Objects
```

### 40.2 LENGTH debe aparecer temprano

El parser del Core debe poder hacer:

```text
leer header
   ↓
obtener LENGTH
   ↓
saltar VALUE
   ↓
leer siguiente Object
```

Esto respeta `Parse ≠ Interpret`: el Core no toca VALUE.

Cualquier diseño donde LENGTH quede después de información que obligue a
interpretar el objeto se descarta.

### 40.3 Análisis de A, B y C

**A — TYPE | LENGTH | ID | VALUE**

El parser conoce inmediatamente:

* qué clasificación tiene (`TYPE`);
* cuánto ocupa (`LENGTH`);
* cuál es su ID (`ID`).

Pequeña desventaja: `ID` queda después de `LENGTH`. No es grave.

**B — ID | TYPE | LENGTH | VALUE**

Expresa naturalmente: "objeto número X, de tipo Y, de tamaño Z". El ID
local aparece inmediatamente, pero `TYPE` y `LENGTH` quedan desplazados.

**C — TYPE | ID | LENGTH | VALUE**

El parser conoce rápidamente:

* qué es estructuralmente (`TYPE`);
* quién es dentro del Container (`ID`);
* cuánto mide (`LENGTH`).

Luego puede decidir `skip(LENGTH)` sin tocar VALUE.

**Candidato provisional: C.** Todavía no congelado.

### 40.4 Tamaños de campos

Propuesta inicial conservadora:

```text
TYPE   = 1 byte   (0..255 tipos estructurales)
ID     = 1 byte   (0..254 objetos locales; 255 = reserved)
LENGTH = 2 bytes  (0..65535 bytes de VALUE)
```

Total por Object header: **4 bytes**.

Ventajas:

* Extremadamente simple.
* 255 objetos por Container es suficiente para la mayoría de los casos.
* 64 KB de VALUE por Object cubre la mayoría de las cargas útiles.
* El ID es local, nunca global; no necesita UUID ni hash.

Si en el futuro se necesitan más objetos o valores más grandes, se define
un Type de extensión (por ejemplo, `EXTENDED_ID` o `EXTENDED_LENGTH`) en
lugar de agrandar todos los headers.

### 40.5 El espacio de ID es local y limitado por el Container

```text
Object count ≤ 255  →  ID ∈ [0, 254]
```

Las referencias son baratísimas:

```text
Object 17
   │
   └────► Object 42
```

La referencia puede ser simplemente `42`, no un UUID, hash o dirección.

### 40.6 Container Header

```text
CONTAINER
┌──────────────────────────────┐
│ VERSION / FLAGS              │
│ OBJECT_COUNT                 │
│ PAYLOAD_LENGTH               │
├──────────────────────────────┤
│ OBJECT 0                     │
│ OBJECT 1                     │
│ OBJECT 2                     │
│ ...                          │
└──────────────────────────────┘
```

No se incluye tabla de offsets en el formato base. El flujo natural es:

```text
read Object
   ↓
read Length
   ↓
skip Value
   ↓
next Object
```

La tabla de offsets queda como extensión opcional para acceso aleatorio.

### 40.7 Fragmentación: Container, no Object

```text
Container = 3000 bytes
MTU       = 1280
```

El Container se fragmenta en múltiples packets:

```text
Packet 1  → fragment of Container
Packet 2  → fragment of Container
Packet 3  → fragment of Container
```

El receptor reconstruye el Container y recién después interpreta Objects.

Regla:

> **Packet ≠ Container ≠ Object.**

El fragmenta el Container, no el Object semánticamente. El Profile nunca
ve fragmentos.

### 40.8 Canonicalización

Dos representaciones pueden ser semánticamente equivalentes sin tener
el mismo orden:

```text
Object 1, Object 2, Object 3  ≡  Object 3, Object 1, Object 2
```

Para firmas, hashes y commitments se define una representación canónica
separada:

```text
NORMAL:    orden puede variar
CANONICAL: Objects ordenados por regla determinista (ej. ID ascendente)
```

El transporte normal no paga el coste de ordenar. La canonicalización se
usa solo cuando se requiere determinismo criptográfico.

### 40.9 Matriz de evaluación preliminar

| Propiedad | A | B | C | Offset Table |
|-----------|---|---|---|--------------|
| Parsing rápido | ★★★★★ | ★★★★★ | ★★★★★ | ★★★ |
| Streaming natural | ★★★★★ | ★★★★★ | ★★★★★ | ★★ |
| Unknown types fácil | ★★★★★ | ★★★★★ | ★★★★★ | ★★★ |
| Relay transparente | ★★★★★ | ★★★★★ | ★★★★★ | ★★★ |
| Fragmentación | ★★★★★ | ★★★★★ | ★★★★★ | ★★ |
| Simplicidad | ★★★★★ | ★★★★★ | ★★★★★ | ★★★ |
| Acceso aleatorio | ★★★ | ★★★ | ★★★ | ★★★★★ |
| Overhead mínimo | ★★★★★ | ★★★★★ | ★★★★★ | ★★ |
| Forward compatibility | ★★★★★ | ★★★★★ | ★★★★★ | ★★★ |
| Coste CPU | ★★★★★ | ★★★★★ | ★★★★★ | ★★★ |

A/B/C son prácticamente equivalentes en propiedades estructurales. La
decisión no debe hacerse por gusto estético, sino por una razón más
profunda:

> ¿Qué orden de campos permite evolucionar el header sin romper el
> parser?

### 40.10 Posible header extendido (para el futuro)

Quizás el header final podría ser:

```text
TYPE | FLAGS | ID | LENGTH
```

donde `FLAGS` permita:

```text
HAS_REFERENCE
HAS_EXTENDED_TYPE
HAS_EXTENDED_LENGTH
NESTED
...
```

Pero **no se agrega FLAGS todavía**. Sería fácil caer en "pongamos
campos por si algún día sirven", lo cual contradice la filosofía del
diseño.

### 40.11 Prueba definitiva antes del Byte Freeze

Antes de congelar el header, intentar representar todos estos casos con
el mismo Object Header:

```text
First Contact
Node Knowledge
Measurement
Capability
Probe
Availability
Evidence
Legacy node
Future object
Nested object
Fragmented container
Signed container
```

Si todos funcionan sin excepciones con:

```text
TYPE | ID | LENGTH | VALUE
```

entonces tenemos un candidato extremadamente fuerte.

---

## 41. Fase 4.5 — Byte Freeze V1

> **Congelamos la primera versión del wire format, no la arquitectura
> para siempre.** La arquitectura debe poder evolucionar sin romper el
> Core.

---

### 41.1 Formato V1 congelado

#### Packet → Container → Object → Value

```text
PACKET
└── IPv7 Header (existente)
    └── CONTAINER
        ├── Container Header (5 bytes)
        └── OBJECT × N
            ├── Object Header (4 bytes)
            └── VALUE (0..65535 bytes)
```

#### Container Header V1

```text
┌─────────┬─────────┬──────────────┬────────────────┐
│ VERSION │ FLAGS   │ OBJECT_COUNT │ PAYLOAD_LENGTH │
│ 1 byte  │ 1 byte  │ 1 byte       │ 2 bytes        │
└─────────┴─────────┴──────────────┴────────────────┘
```

* **VERSION** = `0x01` para V1.
* **FLAGS** = `0x00` reservado para V1.
* **OBJECT_COUNT** = número de Objects en el Container.
* **PAYLOAD_LENGTH** = suma de los tamaños de todos los Objects (header +
  value).

Total Container Header: **5 bytes**.

#### Object Header V1

```text
┌────────┬────────┬──────────┬─────────────────────┐
│ TYPE   │   ID   │ LENGTH   │ VALUE               │
│ 1 byte │ 1 byte │ 2 bytes  │ 0..65535 bytes      │
└────────┴────────┴──────────┴─────────────────────┘
```

Total Object Header: **4 bytes** de overhead.

### 41.2 Decisiones congeladas

#### 41.2.1 Endianness

Network byte order / Big Endian para todos los campos multi-byte
(`PAYLOAD_LENGTH`, `LENGTH`).

#### 41.2.2 Rangos de ID

```text
0..254  = IDs válidos de objetos dentro del Container
255     = reservado (posible escape / extended-ID en el futuro)
```

`OBJECT_COUNT` puede ser `0..255`, pero un ID de objeto nunca será `255`.

#### 41.2.3 Rangos de TYPE

```text
0     = reservado
1..254 = disponibles para perfiles/namespaces
255    = reservado para extensión futura
```

El Core no asigna significado a ningún TYPE. Los valores son ejemplos de
uso por Profiles.

#### 41.2.4 LENGTH = 0 permitido

Un objeto con `LENGTH = 0` es válido. Puede usarse como marcador,
presencia, capability o estructura definida por un Profile.

#### 41.2.5 Tamaños máximos V1

```text
Objects por Container:    255
Bytes por Object Value:   65535
Payload del Container:    limitado por PATH_MTU o política
```

### 41.3 Tabla de niveles de conocimiento del formato

| Nivel | Conoce | No conoce |
|-------|--------|-----------|
| Packet | transporte | semántica |
| Container | estructura del conjunto | significado |
| Object | Type/ID/Length/Value | significado de Value |
| Profile | significado | transporte físico |
| Application | uso | reglas del Core |

### 41.4 Ejemplos hexadecimales V1

> Los valores de TYPE en los ejemplos son ilustrativos y pertenecen a
> Profiles/Namespaces de ejemplo. El Core no los interpreta.

#### Ejemplo 1: First Contact mínimo

```text
Container Header:
  VERSION       = 0x01
  FLAGS         = 0x00
  OBJECT_COUNT  = 0x01
  PAYLOAD_LENGTH= 0x0004

Object 1:
  TYPE   = 0x01  (ejemplo: CONTACT)
  ID     = 0x01
  LENGTH = 0x0000

Hex:
01 00 01 00 04 01 01 00 00
```

#### Ejemplo 2: Node Knowledge (CPU declarado)

Supongamos un Profile que codifica:

```text
property = "cpu"
value    = "8"
source   = "declared"
truth    = "declared"
```

como Value de un objeto de tipo Knowledge.

```text
Container Header:
  VERSION       = 0x01
  FLAGS         = 0x00
  OBJECT_COUNT  = 0x01
  PAYLOAD_LENGTH= 0x0018  (4 header + 20 value)

Object 1:
  TYPE   = 0x03  (ejemplo: KNOWLEDGE)
  ID     = 0x01
  LENGTH = 0x0014
  VALUE  = "cpu:8:declared:declared" (20 bytes ASCII)

Hex:
01 00 01 00 18 03 01 00 14 63 70 75 3a 38 3a 64 65 63 6c 61 72 65 64 3a 64 65 63 6c 61 72 65 64
```

#### Ejemplo 3: Measurement (latencia)

```text
VALUE = "latency:4.82:ms:observed"
```

```text
Container Header:
  VERSION       = 0x01
  FLAGS         = 0x00
  OBJECT_COUNT  = 0x01
  PAYLOAD_LENGTH= 0x001e

Object 1:
  TYPE   = 0x04  (ejemplo: MEASUREMENT)
  ID     = 0x01
  LENGTH = 0x001a
  VALUE  = "latency:4.82:ms:observed"

Hex:
01 00 01 00 1e 04 01 00 1a 6c 61 74 65 6e 63 79 3a 34 2e 38 32 3a 6d 73 3a 6f 62 73 65 72 76 65 64
```

#### Ejemplo 4: Capability Probe result

```text
VALUE = "cpu.compute:class-X"
```

```text
Container Header:
  01 00 01 00 18

Object 1:
  TYPE   = 0x05  (ejemplo: CAPABILITY)
  ID     = 0x01
  LENGTH = 0x0014
  VALUE  = "cpu.compute:class-X"

Hex:
01 00 01 00 18 05 01 00 14 63 70 75 2e 63 6f 6d 70 75 74 65 3a 63 6c 61 73 73 2d 58
```

#### Ejemplo 5: Availability

```text
VALUE = "telemetry:intermittent:18:00-22:00"
```

```text
Container Header:
  01 00 01 00 22

Object 1:
  TYPE   = 0x06  (ejemplo: AVAILABILITY)
  ID     = 0x01
  LENGTH = 0x001e
  VALUE  = "telemetry:intermittent:18:00-22:00"

Hex:
01 00 01 00 22 06 01 00 1e 74 65 6c 65 6d 65 74 72 79 3a 69 6e 74 65 72 6d 69 74 74 65 6e 74 3a 31 38 3a 30 30 2d 32 32 3a 30 30
```

#### Ejemplo 6: Evidence (referencia local)

```text
Object 1: Capability (ID=0x01)
Object 2: Evidence (ID=0x02) con VALUE que contiene referencia 0x01
```

```text
Container Header:
  VERSION       = 0x01
  FLAGS         = 0x00
  OBJECT_COUNT  = 0x02
  PAYLOAD_LENGTH= 0x001c  (8 + 12 + 4)

Object 1:
  TYPE   = 0x05  (ejemplo: CAPABILITY)
  ID     = 0x01
  LENGTH = 0x0004
  VALUE  = "ed25519"

Object 2:
  TYPE   = 0x07  (ejemplo: EVIDENCE)
  ID     = 0x02
  LENGTH = 0x0005
  VALUE  = "ref:01"

Hex:
01 00 02 00 1c 05 01 00 04 65 64 32 35 35 31 39 07 02 00 05 72 65 66 3a 30 31
```

#### Ejemplo 7: Nodo no-IPv7 observado

```text
Object 1: observed protocol IPv4
Object 2: observed latency
```

```text
Container Header:
  01 00 02 00 1c

Object 1:
  TYPE   = 0x10  (ejemplo: OBSERVED_PROTOCOL)
  ID     = 0x01
  LENGTH = 0x0004
  VALUE  = "IPv4"

Object 2:
  TYPE   = 0x11  (ejemplo: OBSERVED_LATENCY)
  ID     = 0x02
  LENGTH = 0x0006
  VALUE  = "8.2:ms"

Hex:
01 00 02 00 1c 10 01 00 04 49 50 76 34 11 02 00 06 38 2e 32 3a 6d 73
```

#### Ejemplo 8: Container anidado (opcional)

Un Object de TYPE especial contiene un sub-Container completo en su
VALUE. El Core lo trata como un Value opaco; el Profile decide parsearlo
como Container anidado.

```text
Object N:
  TYPE   = 0x0A  (ejemplo: NESTED_CONTAINER)
  ID     = 0x05
  LENGTH = 0x0009
  VALUE  = [sub-Container de 9 bytes]
```

El Core no sabe que es un sub-Container; solo transporta 9 bytes.

#### Ejemplo 9: Container fragmentado

```text
Container original = 3000 bytes
MTU                = 1280 bytes
```

El Container se divide en fragments transportados por múltiples Packets.
Cada fragment es opaco para el Core hasta reconstruirse:

```text
Packet 1 → Fragment 1 (Container bytes 0..1279)
Packet 2 → Fragment 2 (Container bytes 1280..2559)
Packet 3 → Fragment 3 (Container bytes 2560..2999)
```

El receptor reensambla el Container y recién entonces parsea Objects.

#### Ejemplo 10: Signed Container

```text
Container
├── Object 1  (TYPE=Data, VALUE=...)
└── Object 2  (TYPE=Signature, VALUE=firma sobre hash canónico)
```

La canonicalización (por ejemplo, objetos ordenados por ID ascendente)
se aplica para generar el hash que se firma. El transporte normal no
requiere ordenación.

### 41.5 Propiedad fundamental confirmada

El Core puede saltar un objeto desconocido sin comprender absolutamente
nada de su contenido:

```text
read TYPE
read ID
read LENGTH
offset += 4 + LENGTH
```

Eso es exactamente `Parse ≠ Interpret`.

### 41.6 Casos que deben caber en V1

Antes de declarar V1 válido, verificar conceptualmente que estos casos
funcionan sin excepciones:

```text
☑ First Contact
☑ Node Knowledge
☑ Measurement
☑ Capability Probe
☑ Availability
☑ Evidence
☑ Legacy / non-IPv7 observation
☑ Future unknown object
☑ Nested Container
☑ Fragmented Container
☑ Signed Container
```

Si alguno requiriese un segundo mecanismo estructural, el diseño falla.
Si todos caben, tenemos un formato realmente genérico.

### 41.7 Ataque al formato ya congelado

Antes de pasar a implementación, intentar romper V1 con casos extremos:

1. **Objeto con LENGTH > PAYLOAD_LENGTH**: el Container es corrupto.
2. **OBJECT_COUNT = 0**: Container vacío, debe ser válido.
3. **OBJECT_COUNT que no coincide con los objetos parseables**: corrupto.
4. **ID duplicado**: no prohibido por el formato; el Profile decide qué
   hacer.
5. **Referencias a ID inexistente**: no prohibido por el formato; el
   Profile decide.
6. **TYPE desconocido**: el Core lo salta; el Profile lo ignora.
7. **Container de exactamente PATH_MTU bytes**: debe caber en un packet.
8. **Container > PATH_MTU**: debe poder fragmentarse.
9. **VALUE con bytes nulos o no imprimibles**: válido, opaco.
10. **Referencia circular entre objetos**: no prohibida por el formato; el
    Profile detecta si es relevante.

### 41.8 Próximo paso

**Fase 4.6 — Implementación experimental**: construir el encoder/decoder
V1 en Python sin integrarlo todavía al flujo del nodo. Validar con tests
que los hex dumps de los ejemplos se parsean correctamente, que objetos
conocidos e unknown se procesan según las reglas, y que la integridad
estructural se valida. Solo después integrar con el nodo y mantener los
9/9 tests + 5/5 multiproceso PASS.

---

## 42. Resumen del wire format V1

```text
Container Header (5 bytes)
  VERSION        1 byte
  FLAGS          1 byte
  OBJECT_COUNT   1 byte
  PAYLOAD_LENGTH 2 bytes (big endian)

Object Header (4 bytes)
  TYPE           1 byte
  ID             1 byte
  LENGTH         2 bytes (big endian)

Value
  0..65535 bytes opacos para el Core

ID:     0..254 válidos, 255 reservado
TYPE:   0 reservado, 1..254 disponibles, 255 reservado
LENGTH: 0..65535, 0 válido
Endianness: big endian
```

Especificación congelada para V1.





