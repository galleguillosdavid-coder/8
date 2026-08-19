# IPv7 — Invariantes de Contact, Knowledge, Truth, Lifetime y Probe

> **Estado**: diseño conceptual cerrado. Sin código todavía.
>
> Estas invariantes deben regir cualquier wire format futuro de First
> Contact y Node Knowledge. El objetivo es evitar que un formato
> aparentemente eficiente rompa la arquitectura semántica que estamos
> construyendo.

---

## 0. Invariante fundamental

> **El Core transporta forma. Los Profiles aportan significado.**

Cualquier formato futuro debe permitir que:

* El Core reconozca estructuras (`Container`, `Object`, `IDTLV`) sin
  saber qué representan.
* Los Profiles interpreten el valor de cada objeto sin que el Core
  necesite conocerlos.

---

## 1. CONTACT

### 1.1 CONTACT debe ser mínimo y universal

CONTACT es una operación primitiva del Core que inicia una relación de
comunicación. No debe contener:

* CPU
* Perfiles específicos
* Semántica de sensores, vehículos, archivos, etc.
* Métricas detalladas
* Requisitos de prueba de capacidad

### 1.2 CONTACT debe permitir determinar qué sigue

Un CONTACT válido del Core puede transportar únicamente:

```text
CONTACT
 ├─ quién inicia
 ├─ identificador disponible
 ├─ contexto mínimo
 ├─ capacidades de transporte
 └─ posibilidad de continuar
```

* **Quién inicia**: identidad disponible (puede ser provisional).
* **Identificador disponible**: algo que permite referirse al contacto.
* **Contexto mínimo**: versión de protocolo, canal de inicio, flags de
  transporte.
* **Capacidades de transporte**: MTU soportado, formatos de objeto,
  seguridad disponible.
* **Posibilidad de continuar**: indicación de si se acepta continuar.

### 1.3 CONTACT no exige verificación

Un nodo puede responder a CONTACT sin demostrar nada. La verificación es
opt-in y ocurre después, a través de PROBE transportado como objeto.

---

## 2. KNOWLEDGE

### 2.1 Todo conocimiento es un objeto independiente

Cada ítem de conocimiento debe poder existir como un objeto separado con
su propia metadata:

```text
Knowledge Object
├─ value
├─ source
├─ truth
├─ confidence
└─ lifetime
```

### 2.2 Múltiples verdades sobre el mismo hecho pueden coexistir

Un nodo puede tener simultáneamente:

```text
CPU:
    value      = 8 cores
    source     = B
    truth      = declared
    confidence = low

CPU:
    value      = 73 units/s
    source     = probe-7
    truth      = verified
    confidence = high
```

Ninguna entrada destruye a la otra. La información se acumula y el
observador decide cuál usar según contexto.

### 2.3 Knowledge es contextual, no global

Cada nodo mantiene su propio Node Knowledge. No hay una tabla de
conocimiento global obligatoria. Dos nodos pueden tener modelos
razonablemente diferentes del mismo nodo remoto.

---

## 3. TRUTH

### 3.1 Tres estados epistemológicos independientes

```text
DECLARED  → lo que el otro nodo dice
OBSERVED  → lo que este nodo mide
VERIFIED  → lo que un procedimiento definido demuestra
```

### 3.2 No hay escalera obligatoria

No se exige:

```text
declared → observed → verified
```

Son estados que coexisten. Cada uno aporta información distinta.

Combinaciones válidas:

```text
declared + observed
declared + verified
observed
verified
declared + observed + verified
```

### 3.3 Una declaración puede ser correcta sin estar verificada

```text
B dice: CPU = 8 cores  (declared)
A mide: CPU probe = 73  (verified)
```

Ambas pueden ser ciertas. El número de cores declarado no se invalida
por la medición de rendimiento.

---

## 4. LIFETIME

### 4.1 El conocimiento no desaparece porque expire

```text
FRESH
  ↓
STALE
  ↓
EXPIRED
```

### 4.2 Expired no significa false

```text
Expired = "ya no podemos asumir que sigue vigente"
False   = "hemos demostrado que es incorrecto"
```

Un ítem expirado puede permanecer almacenado como experiencia histórica.
Solo se marca como no confiable para decisiones actuales.

### 4.3 Cada ítem tiene su propia vida útil

```text
Identity      → años
Locator       → segundos/minutos
Path / MTU    → segundos/minutos
Availability  → dinámica
RTT / pérdida → segundos
Capability    → horas/días
```

### 4.4 El tiempo enriquece la red

La red aprende de su experiencia sin necesidad de preguntar
constantemente. El envejecimiento del conocimiento es una característica,
no un error.

---

## 5. PROBE

### 5.1 Probe es siempre opt-in

Un nodo nunca está obligado a demostrar una capacidad solo porque otro
nodo lo solicite.

### 5.2 Probe como procedimiento de Profile

```text
A → B
    PROBE REQUEST
      type = computational
      algorithm = X
      difficulty = Y
      constraints = Z

B decide: ACCEPT / REFUSE

B → A
    PROBE RESULT
      algorithm = X
      work = Y
      elapsed = T
      timestamp = ...
```

### 5.3 Probe no crea una segunda clase de información

El resultado de un probe vuelve a ingresar como Knowledge Object con
`s truth = verified` y su propia lifetime.

```text
PROBE RESULT ──► Knowledge Object ──► Node Knowledge
```

### 5.4 El Core no entiende el probe

El Core solo transporta:

```text
OBJECT
  PROBE_REQUEST
  PROBE_ACCEPT
  PROBE_REFUSE
  PROBE_RESULT
```

La interpretación pertenece al Profile (`computational-capability`,
`crypto-capability`, etc.).

---

## 6. Ciclo completo

```text
                 ┌──────────────┐
                 │    UNKNOWN   │
                 └──────┬───────┘
                        │
                     CONTACT
                        │
          ┌─────────────┼──────────────┐
          │             │              │
       NO RESPONSE    LEGACY          IPv7
          │             │              │
          ▼             ▼              ▼
       UNKNOWN       OBSERVE        ESTABLISH
                        │              │
                        └──────┬───────┘
                               ▼
                           KNOWLEDGE
                               │
                       ┌───────┴───────┐
                       │               │
                  experiencia       PROBE
                       │               │
                       │          ┌────┴────┐
                       │        REFUSE   RESULT
                       │                  │
                       └────────┬─────────┘
                                ▼
                             KNOWLEDGE
                                │
                         lifetime changes
                                │
                     FRESH → STALE → EXPIRED
                                │
                              REFRESH
                                │
                                └──────► KNOWLEDGE
```

### 6.1 Propiedades del ciclo

* El tráfico normal produce observaciones.
* Los contactos producen conocimiento.
* Los probes producen verificaciones.
* El tiempo modifica la validez.
* Las rutas producen nuevas observaciones.
* Todo vuelve al mismo `Node Knowledge`.

Regla:

> **Networks learn from experience, not from interrogation.**

---

## 7. Conexión con Container / Object / IDTLV

Una vez que estas invariantes están cerradas, el wire format puede
diseñarse sobre `Container → Object`:

```text
Container
│
├── Object #1  → Contact
├── Object #2  → Identity
├── Object #3  → Locator
├── Object #4  → Observation
├── Object #5  → Measurement
├── Object #6  → Capability
├── Object #7  → Lifetime
└── Object #8  → Probe
```

Cada objeto sigue la estructura mínima:

```text
TYPE    → estructura del objeto
LENGTH  → tamaño
ID      → índice local dentro del container
VALUE   → contenido
```

Los objetos pueden referenciarse entre sí por `ID`. El Core interpreta
estructura. Los Profiles interpretan semántica.

### 7.1 Reglas del formato futuro

* Debe permitir que cualquier objeto de conocimiento tenga `source`,
  `truth`, `confidence` y `lifetime`.
* Debe permitir múltiples objetos sobre el mismo tema con distintos
  valores de `truth`.
* Debe permitir objetos vacíos o parciales (un contacto mínimo no
  requiere todos los campos).
* Debe permitir referencias entre objetos sin introducir semántica en el
  Core.
* Debe permitir que un Profile defina un probe cuyo resultado se almacene
  como otro objeto de conocimiento.

---

## 8. Próximo paso

Diseñar el modelo lógico y wire format concreto de `Container/Object`
compatible con estas invariantes, y verificar que `First Contact`, `Node
Knowledge`, Availability, Profiles, Probes y nodos no-IPv7 puedan
representarse con las primitivas existentes. Ver
`CONTAINER_OBJECT_WIREFORM_DESIGN.md`. Recién entonces implementar.
