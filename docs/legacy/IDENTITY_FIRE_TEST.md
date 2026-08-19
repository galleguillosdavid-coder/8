# IPv7 — Identity Fire Test (Fase 5.2)

> **Estado**: Fase 5.2 — prueba de fuego adversarial. Sin criptografía
> concreta, sin Byte Freeze de Identity.
>
> **Objetivo explícito de este documento: intentar demostrar que la
> hipótesis de Fase 5.1 es FALSA.** No es una demostración
> complaciente. Si algún caso obliga a introducir un campo nuevo en
> `Packet`, `Container` u `Object` que el Core de Fase 4 no necesitaba,
> la hipótesis falla y se debe volver a `IDENTITY_ARCHITECTURE.md`
> antes de continuar.

---

## 0. Hipótesis bajo prueba

```text
H: Identity puede representarse completamente mediante
   Container/Object V1 (TYPE | ID | LENGTH | VALUE),
   sin modificar el Core, y sin que un relay necesite
   conocer su significado para transportarla intacta.
```

Regla de falsación:

> Si para representar cualquiera de los casos A–P es necesario agregar
> un campo al `Packet Header`, al `Container Header` o al `Object
> Header` definidos en `CONTAINER_OBJECT_WIREFORM_DESIGN.md` Sección
> 41, la hipótesis se declara **FALSA** y Fase 5 vuelve a diseño
> arquitectónico.

Los `TYPE` usados abajo son **ilustrativos** (namespace de ejemplo,
igual que en la Sección 41.4 del wireform design). El Core nunca les
asigna significado.

---

## 1. Reglas congeladas antes de la prueba (heredadas de Fase 5.1)

```text
Identity ≠ Authentication
Identity ≠ Trust
Identity ≠ Authorization
Identity ≠ Locator
Identity ≠ Node
DECLARED / OBSERVED / VERIFIED no son una escalera
Revocation ≠ Expiration ≠ False
Delegation no transfiere identidad, la extiende
Rotación no destruye continuidad histórica
El Core no necesita comprender el significado de Identity
```

Estas reglas no se re-discuten aquí. Se usan como criterio de
aceptación de cada caso.

---

## 2. Casos A–P

### A — Identity presentada por primera vez

```text
Container
 └── Object ID=1  TYPE=IDENTITY_DECLARED
       VALUE = <identificador/clave pública, opaco>
```

El Core ve un Object más. No necesita saber que es una identidad.

**Veredicto: PASS.**

---

### B — Identity desconocida (TYPE no reconocido por el receptor)

```text
Container
 ├── Object ID=1  TYPE=1        (conocido)
 └── Object ID=2  TYPE=0xE1     (Identity de un Profile futuro, desconocido)
```

Se aplica exactamente la invariante `Unknown ≠ Invalid` ya demostrada
en Fase 4.6/4.7. El receptor salta el objeto usando `LENGTH`, sin
necesitar entender que era una identidad.

**Veredicto: PASS.** (Reutiliza mecanismo existente, cero código nuevo
en el Core.)

---

### C — Identity observada pero no verificada

```text
Object
 TYPE = IDENTITY_KNOWLEDGE
 VALUE =
     identity  = "X"
     truth     = observed
     source    = A (observador)
     confidence = medium
```

Igual que cualquier Knowledge Object (`CONTAINER_OBJECT_WIREFORM_DESIGN.md`
Sección 6): el Value interno es definido por el Profile. El Core no
distingue este caso de una medición de latencia.

**Veredicto: PASS.**

---

### D — Identity verificada (con evidencia)

```text
Container
 ├── Object ID=1  TYPE=IDENTITY_DECLARED   VALUE="X"
 └── Object ID=2  TYPE=EVIDENCE            VALUE="ref:01;challenge-response ok"
```

Reutiliza el mecanismo de `Evidence` ya validado en
`CONTAINER_OBJECT_WIREFORM_DESIGN.md` Sección 29 y Ejemplo 6 (Sección
41.4). La referencia `#2 → #1` es local y opaca para el Core.

**Veredicto: PASS.**

---

### E — Dos identidades en el mismo nodo

```text
Container
 ├── Object ID=1  TYPE=IDENTITY_DECLARED  VALUE="X-sensor"
 └── Object ID=2  TYPE=IDENTITY_DECLARED  VALUE="X-control"
```

Nada en el formato limita cuántos Objects del mismo `TYPE` puede haber
en un Container. `OBJECT_COUNT` ya soporta hasta 255.

**Veredicto: PASS.**

---

### F — Misma identidad observada por distintos nodos

Este caso no es un problema de wire format: cada nodo mantiene su
propio `Node Knowledge` (`CONTACT_KNOWLEDGE_INVARIANTS.md` Sección
2.3). No requiere coordinación ni estado compartido a nivel de Core.

**Veredicto: PASS (fuera del alcance del Core por diseño).**

---

### G — Rotación de identidad

```text
Container
 ├── Object ID=1  TYPE=IDENTITY_DECLARED     VALUE="Key-B (nueva)"
 └── Object ID=2  TYPE=IDENTITY_ROTATION     VALUE="firma de Key-A sobre Key-B; ref:01"
```

El Core transporta el Object de rotación como cualquier otro. No
necesita validar la firma ni entender qué es una "rotación".

**Veredicto: PASS.**

---

### H — Revocación

```text
Object
 TYPE = IDENTITY_REVOCATION
 VALUE = "ref:01; revoked-at=<t>; reason=opaque-to-core"
```

Mismo mecanismo que Evidence/Rotation: una referencia local y un blob
opaco.

**Veredicto: PASS.**

---

### I — Delegación

```text
Container
 ├── Object ID=1  TYPE=IDENTITY_DECLARED   VALUE="A"
 ├── Object ID=2  TYPE=IDENTITY_DECLARED   VALUE="B"
 └── Object ID=3  TYPE=IDENTITY_DELEGATION VALUE="from:01;to:02;scope=telemetry;expiry=..."
```

El Core no interpreta `scope` ni valida que `B` efectivamente actúe
dentro de él. Eso es responsabilidad de Profile/Application (I-13).

**Veredicto: PASS.**

---

### J — Identity anónima/pseudónima

```text
Container
 └── Object ID=1  TYPE=CONTACT   VALUE=...   (sin ningún Object de identidad)
```

`CONTACT_KNOWLEDGE_INVARIANTS.md` Sección 1.3 ya establece que CONTACT
no exige verificación; este caso extiende eso a "no exige identidad en
absoluto". Un Container sin Object de identidad es válido
(`CONTAINER_OBJECT_WIREFORM_DESIGN.md` Sección 10, Optional objects).

**Veredicto: PASS.**

---

### K — Nodo legacy sin Identity IPv7

Un nodo no-IPv7 no produce ningún `Container`. No hay Object de
identidad que transportar; el conocimiento se construye por
observación pura (`CONTACT_KNOWLEDGE_INVARIANTS.md` Sección 22).

**Veredicto: PASS (no aplica al wire format; confirma que el Core no
necesita ningún campo de "modo legacy").**

---

### L — Identity futura con campos internos desconocidos

```text
Object
 TYPE = IDENTITY_DECLARED
 VALUE = <estructura interna con campos nuevos que el Profile actual no
          reconoce, p. ej. un nuevo tipo de curva criptográfica>
```

El Core nunca mira dentro de `VALUE` (Semantic opacity, invariante 12
de `CONTAINER_OBJECT_WIREFORM_DESIGN.md` Sección 38). La evolución de
la estructura interna es un problema exclusivo del Profile, ya cubierto
por Sección 22-23 del wireform design (Compatibility / Forward
compatibility).

**Veredicto: PASS.**

---

### M — Identity maliciosa (objeto corrupto u oversized)

```text
Object
 TYPE = IDENTITY_DECLARED
 LENGTH = 0xFFFF
 VALUE  = <trunco>
```

Ya cubierto exhaustivamente por la Fase 4.7 Adversarial Validation
(`experimental/test_container_v1.py`): `LENGTH` se valida contra los
bytes disponibles antes de aceptar el objeto, independientemente de que
sea una identidad o cualquier otro tipo. No se requiere ningún
mecanismo adicional en el Core específico para Identity.

**Veredicto: PASS (por herencia de 4.7, sin código nuevo).**

---

### N — Replay de una presentación antigua

```text
t0: A → B   Container [Object IDENTITY_DECLARED VALUE="X"]
t5: M → B   Container [Object IDENTITY_DECLARED VALUE="X"]   (bytes idénticos, capturados en t0)
```

**Este caso expone un límite real, no una falla del Core.**

El Core, por diseño, no mantiene estado de "qué bytes ya vi antes". Un
`Container` estructuralmente idéntico decodifica exactamente igual sin
importar cuándo se recibió. El Core **no puede ni debe** detectar
replay: eso requeriría que interprete `VALUE` o mantenga estado de
sesión, ambas cosas fuera de su responsabilidad (I-10, Parse ≠
Interpret).

La protección contra replay pertenece a una capa distinta y ya
existente en el diseño: `session_id` en el `Packet Header`
(`packet.py`), nonces o timestamps dentro del `VALUE` definidos por el
Profile de autenticación, o ambos.

**Veredicto: PASS, con nota explícita**: la hipótesis no falla porque
el Core no resuelva replay — el Core nunca prometió resolverlo. Se dej
a documentado como responsabilidad de Profile/Session, no como
requisito nuevo para Container/Object.

---

### O — Conflicto de binding

```text
Container
 ├── Object ID=1  TYPE=IDENTITY_DECLARED    VALUE="X"
 ├── Object ID=2  TYPE=EVIDENCE             VALUE="ref:01; dice: verified"
 └── Object ID=3  TYPE=IDENTITY_REVOCATION  VALUE="ref:01; dice: revoked"
```

Dos objetos afirman cosas contradictorias sobre el mismo `ID`
referenciado. El formato no prohíbe esto
(`CONTAINER_OBJECT_WIREFORM_DESIGN.md` Sección 41.7, puntos 4 y 5): el
Core no resuelve conflictos semánticos, solo transporta. La resolución
("¿gana la evidencia o la revocación? ¿por timestamp? ¿por lifetime?")
es responsabilidad exclusiva del Profile.

**Veredicto: PASS (conflicto es semántico, no estructural).**

---

### P — `ID` de Object duplicado (caso crítico)

```text
Container
 ├── Object ID=7  TYPE=IDENTITY_DECLARED  VALUE="X"
 ├── Object ID=7  TYPE=IDENTITY_DECLARED  VALUE="Y"     (mismo ID!)
 └── Object ID=9  TYPE=EVIDENCE           VALUE="ref:07; verified"
```

El Core acepta esto sin error (Fase 4.7 ya estableció que `ID`
duplicado es estructuralmente válido). Pero a nivel de Profile,
`ref:07` es **ambiguo**: no se puede determinar si la evidencia
respalda a `"X"` o a `"Y"`.

**Este es exactamente el límite que Fase 5.1 Sección 21 dejó abierto.**
La prueba confirma:

1. El Core no falla ni necesita cambiar (`ID` duplicado sigue siendo
   una decisión de Profile, no de Core — I-7).
2. **Cualquier Profile que use `ID` como base de binding/evidence DEBE
   enforzar unicidad de `ID` dentro de los Objects que participan en
   ese binding**, como regla propia, antes de confiar en una
   referencia. El Core no se lo garantiza.

**Veredicto: PASS para el Core. FAIL potencial a nivel de Profile si
no se documenta la regla anterior** — por eso se agrega como invariante
nueva (ver Sección 3).

---

## 3. Invariante nueva descubierta por el caso P

> **I-17 — Reference disambiguation is a Profile responsibility.**
> Un Profile que interprete `ID` como base de una referencia de binding
> (Identity, Evidence, Delegation, Revocation, Rotation) debe exigir
> `ID` único entre los Objects que participan en esa relación dentro
> del Container. El Core V1 no garantiza unicidad de `ID`; solo
> garantiza que la estructura es parseable.

Esta invariante se agrega a `IDENTITY_INVARIANTS.md`.

---

## 4. Prueba definitiva: relay ciego

Además del análisis caso por caso, se requiere evidencia experimental
(no solo conceptual) de que un relay que no conoce ningún `TYPE` de
Identity puede transportarla intacta:

```text
A ───────► B ───────► C
           │
           ├── no conoce IDENTITY_DECLARED
           ├── no conoce EVIDENCE
           ├── no conoce ROTATION / REVOCATION / DELEGATION
           └── no interpreta VALUE

A.bytes == B.forwarded_bytes == C.received_bytes
```

Esta prueba se implementa en `experimental/identity_scenarios.py` y
`experimental/test_identity_fire_test.py`, reutilizando
`ContainerV1`/`ObjectV1` de Fase 4.6/4.7 **sin modificarlos**. Si el
relay ciego preserva bytes exactos para los casos A, D, G, H, I, N y P,
la hipótesis queda soportada también experimentalmente, no solo en
papel.

---

## 5. Veredicto final de la hipótesis

```text
A  PASS
B  PASS
C  PASS
D  PASS
E  PASS
F  PASS (fuera de alcance del Core)
G  PASS
H  PASS
I  PASS
J  PASS
K  PASS (no aplica)
L  PASS
M  PASS (heredado de 4.7)
N  PASS (con nota: replay no es responsabilidad del Core)
O  PASS (conflicto es semántico)
P  PASS para el Core / requiere regla explícita en Profile (I-17)
```

**Ningún caso exigió un campo nuevo en `Packet Header`, `Container
Header` u `Object Header`.**

```text
H: Identity puede representarse completamente mediante
   Container/Object V1, sin modificar el Core.

VEREDICTO: SOBREVIVE (no falsada)
```

Condición para que este veredicto se mantenga: la evidencia
experimental de la Sección 4 debe pasar (ver
`experimental/test_identity_fire_test.py`).

---

## 6. Qué NO decide este documento

* No asigna ningún `TYPE` real a Identity/Evidence/Rotation/Revocation/
  Delegation (siguen siendo ilustrativos).
* No elige mecanismo criptográfico (Ed25519, ML-DSA, DID, certificados).
* No resuelve las "Open decisions" de `IDENTITY_INVARIANTS.md` distintas
  de I-17.
* No modifica `container_v1.py` ni `ipv7_mvp/`.

---

## 7. Próximo paso

Si la prueba experimental de la Sección 4 confirma el veredicto:

```text
Fase 5.2 CLOSED
        ↓
Fase 5.3 — elección de mecanismo criptográfico concreto para
           Identity/Authentication, todavía sin tocar el Core.
```
