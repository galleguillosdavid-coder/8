# IPv7 — Identity Architecture

> **Estado**: Fase 5.1 — diseño conceptual. Sin código, sin bytes, sin
> criptografía concreta todavía.
>
> Este documento no decide DID, Ed25519, ML-DSA, certificados ni
> ningún mecanismo técnico. Primero define qué es Identity dentro de
> IPv7, qué NO es, y cómo se relaciona con lo que ya construimos en
> `NODE_KNOWLEDGE.md`, `FIRST_CONTACT_DESIGN.md`,
> `CONTACT_KNOWLEDGE_INVARIANTS.md` y
> `CONTAINER_OBJECT_WIREFORM_DESIGN.md`.

---

## 1. Pregunta de partida

> ¿Qué necesita el Core saber sobre identidad, si es que necesita saber
> algo, para transportar Containers/Objects de forma segura, sin
> convertirse en un motor de identidad?

No asumimos de antemano que el Core necesita `origin`, `destination` o
una "authentication proof". Esa es precisamente una de las preguntas
que este documento debe responder, no un punto de partida.

---

## 2. ¿Qué es Identity?

Identity es una **afirmación vinculable**: la afirmación de que cierta
entidad controla cierto material (típicamente criptográfico) que le
permite ser reconocida consistentemente a través del tiempo,
independientemente de dónde se encuentre en la red.

```text
Identity = "esta entidad puede demostrar consistentemente que es la
            misma entidad que antes"
```

Identity **no es**:

* una dirección de red;
* una ubicación;
* una sesión;
* una tabla de confianza;
* una propiedad observable de comportamiento;
* una garantía de veracidad sobre lo que la entidad declara.

---

## 3. Identity vs Node

Un **Node** es una entidad participante observable en la red: algo que
responde, transmite, o puede ser contactado.

Una **Identity** es una afirmación de identidad criptográficamente
vinculable, presentada por (o atribuida a) un Node.

```text
Node
 ├── puede tener Identity conocida
 ├── puede no tener Identity conocida todavía
 └── puede presentar múltiples Identities bajo reglas definidas
```

No asumimos `1 Node = 1 Identity`. Un Node puede:

* no presentar ninguna identidad (comunicación anónima, legacy, no-IPv7);
* presentar una identidad no verificada;
* presentar varias identidades en paralelo (multi-perfil, multi-servicio);
* cambiar de identidad presentada a lo largo del tiempo.

Esto es consistente con `NODE_KNOWLEDGE.md` Sección 5, donde `Identity`
es un componente de Node Knowledge, no una propiedad fija del Node.

---

## 4. Identity vs Locator

Ya establecido en `FIRST_CONTACT_DESIGN.md` y `NODE_KNOWLEDGE.md`:

```text
Identity      → persistent (años)
Locator       → perishable (segundos/minutos)
```

Una identidad no debe depender de IP, puerto UDP, MAC, interfaz, ruta
o posición en la red.

```text
Identity A
   │
   ├── Locator 1  (ayer)
   ├── Locator 2  (hoy, otra red)
   └── Locator 3  (mañana, otro transporte)
```

Regla:

> **Un nodo puede cambiar de locator sin perder su identidad.**

---

## 5. Identity vs Session

Una `Session` (ver `ARQUITECTURA_CANAL_SESION_OBJETO.md`) es un
contexto temporal de comunicación. Una identidad puede:

* presentarse una vez y sostener múltiples sesiones a lo largo del
  tiempo;
* no presentarse en absoluto, y la sesión seguir existiendo sobre una
  base de conocimiento puramente observacional (locator + reachability).

```text
Identity
   │
   └── presented-in → Session 1
   └── presented-in → Session 2
   └── presented-in → Session 3
```

La sesión no define la identidad; a lo sumo la referencia.

---

## 6. Identity vs Knowledge

Ya establecido conceptualmente en `NODE_KNOWLEDGE.md` Sección 12:

```text
"Soy este nodo"       → Identity / authentication
"Soy capaz de X"      → Capability (declared)
"Realmente hice X"    → Verification (observed/proved)
```

Identity responde **quién**. Knowledge responde **qué sabemos de él**.

```text
Identity:
    "X"

Knowledge:
    "X aparentemente tiene 8 GB RAM"     (declared)
    "X respondió en 12 ms"               (observed)
    "X declara soportar Profile Y"       (declared)
    "X demostró soportar Profile Y"      (verified)
```

Regla:

> **Identity ≠ Knowledge.** Identity es el sujeto sobre el cual se
> acumula Knowledge, no un ítem más de Knowledge equivalente a los
> demás.

Sin embargo, el **grado de verdad** de una identidad sí sigue el mismo
modelo epistemológico de tres estados que el resto de Node Knowledge
(ver Sección 9).

---

## 7. Identity vs Authentication

```text
Identity        → ¿quién dice ser esta entidad?
Authentication  → ¿qué evidencia demuestra que controla lo que afirma
                   controlar?
```

Una identidad puede presentarse sin autenticarse (`declared`). La
autenticación es el procedimiento que produce evidencia verificable de
que quien presenta la identidad controla el material correspondiente
(p. ej. una clave privada).

```text
Identity presented
      │
      ▼
Authentication challenge/response (opcional, opt-in según contexto)
      │
      ▼
Evidence
      │
      ▼
Identity: truth = verified
```

---

## 8. Identity vs Trust vs Authorization

Tres conceptos que las arquitecturas de red tienden a fusionar
incorrectamente. IPv7 los separa explícitamente:

```text
Identity        → ¿quién dice ser esta entidad?
Authentication  → ¿qué evidencia demuestra el control de esa identidad?
Trust           → ¿cuánto confío en esta identidad/evidencia para
                   tomar una decisión?
Authorization   → ¿qué tiene permitido hacer, dado ese nivel de
                   confianza?
```

Cadena conceptual posible (no obligatoria):

```text
Identity
   ↓
Authentication
   ↓
Evidence
   ↓
Knowledge
   ↓
Trust
   ↓
Authorization
```

Regla:

> **IDENTITY ≠ TRUST.** Saber que una identidad está vinculada a una
> clave no implica confiar en ella. Trust es una decisión de política,
> tomada por el Profile o la Application, no por el Core.

> **AUTHENTICATION ≠ AUTHORIZATION.** Demostrar control de una
> identidad no implica ningún permiso concreto. La autorización es una
> capa adicional, también fuera del Core.

---

## 9. Identity y los tres niveles de verdad

Igual que en `CONTACT_KNOWLEDGE_INVARIANTS.md` Sección 3, la identidad
admite los mismos tres estados epistemológicos, sin escalera
obligatoria:

```text
DECLARED  → la entidad afirma ser X (p. ej. presenta una clave pública
            o un identificador)
OBSERVED  → el observador nota un comportamiento consistente con esa
            identidad a lo largo de múltiples interacciones
VERIFIED  → un procedimiento de autenticación definido ha demostrado
            el control del material asociado a esa identidad
```

```text
Identity X
 ├── DECLARED   (X se presentó con este identificador)
 ├── OBSERVED   (X se comportó de forma consistente en 12 sesiones)
 └── VERIFIED   (X respondió correctamente a un challenge criptográfico)
```

Una identidad `declared` puede ser perfectamente válida para
comunicarse (ver Sección 10, First Contact). No se exige verificación
para hablar.

---

## 10. Identity y First Contact

Consistente con `FIRST_CONTACT_DESIGN.md` y
`CONTACT_KNOWLEDGE_INVARIANTS.md`:

```text
UNKNOWN
   ↓
CONTACT
   ↓
NODE OBSERVED
   ↓
IDENTITY PRESENTED     (declared)
   ↓
IDENTITY AUTHENTICATED (verified, opcional, opt-in)
```

El Core no debe exigir conocer la identidad de un nodo antes de
permitir el contacto. `CONTACT` (Sección 1 de
`CONTACT_KNOWLEDGE_INVARIANTS.md`) ya establece que la identidad
disponible en un CONTACT puede ser **provisional**.

Esto es fundamental: exigir identidad verificada antes del primer
contacto convertiría a IPv7 en una red de permiso previo, contradiciendo
el principio rector de `NODE_KNOWLEDGE.md`:

```text
IPv7 does not require trust before communication;
it progressively builds knowledge through communication.
```

---

## 11. Identity presentada vs Identity observada

Dos formas distintas en que una identidad entra al conocimiento de un
nodo:

```text
PRESENTED   → la propia entidad envía su identificador/clave
OBSERVED    → el observador infiere consistencia de comportamiento sin
              que la entidad haya presentado nada formalmente (p. ej.
              siempre responde desde el mismo material criptográfico
              en un canal, aunque no haya un protocolo explícito de
              identidad)
```

Un nodo no-IPv7 (Sección 21 de `CONTACT_KNOWLEDGE_INVARIANTS.md`,
Sección 10 de `FIRST_CONTACT_DESIGN.md`) normalmente solo permite
identidad `observed` (o ninguna), nunca `presented` según el formato de
IPv7.

---

## 12. Binding

`Binding` es la relación explícita entre una Identity y otro elemento:
una clave, un Node, una Session, o Evidence.

```text
Identity
   │
   ├── bound-to     → Key
   ├── observed-on  → Node
   ├── presented-in → Session
   └── supported-by → Evidence
```

Regla de diseño (provisional, sujeta a Fase 5.2):

> El binding es una relación semántica. Puede representarse mediante
> referencias locales por `ID` dentro de un `Container` (igual que
> `Evidence` en `CONTAINER_OBJECT_WIREFORM_DESIGN.md` Sección 29), pero
> su interpretación ("esta clave respalda a esta identidad") pertenece
> al Profile, no al Core.

No mezclamos deliberadamente:

```text
identity ≠ key ≠ node ≠ session ≠ locator
```

Cada uno es un concepto distinto que puede referenciar a los demás,
pero ninguno sustituye a otro.

---

## 13. Rotación de claves

Si una identidad se sostiene mediante material criptográfico que puede
rotar:

```text
Key A (t0)
   │
   │ rotation
   ▼
Key B (t1)
```

Debe existir, en algún nivel (probablemente Profile, no Core), una
manera de demostrar continuidad: que quien controla `Key B` es la misma
entidad que controlaba `Key A`.

Este documento no decide **cómo** se demuestra esa continuidad
(firma de transición, cadena de rotación, revocación explícita, etc.).
Solo establece que:

> El mecanismo de rotación no debe introducirse prematuramente en el
> parser del Core. El Core transporta el Object que representa la
> prueba de rotación; no la entiende.

---

## 14. Delegación

Una identidad puede delegar capacidad de actuar en su nombre a otra
identidad (p. ej. un sub-nodo, un proceso, un dispositivo temporal).

```text
Identity A
   │
   └── delegates-to → Identity B
                        (scope, expiry, constraints definidos por Profile)
```

Igual que Binding, la delegación es una relación semántica que puede
transportarse como Object/Evidence, pero cuya validez y alcance los
evalúa el Profile/Application, no el Core.

---

## 15. Revocación

Una identidad, o el binding entre identidad y clave, puede revocarse.

```text
Identity X + Key A
      │
      │ revoked at t
      ▼
Identity X + Key A → no longer valid after t
```

Al igual que en `NODE_KNOWLEDGE.md` Sección 6 (lifetime), revocación no
es lo mismo que expiración:

```text
Expired  = "ya no podemos asumir que sigue vigente" (pasividad, tiempo)
Revoked  = "se ha declarado explícitamente inválido" (acción deliberada)
```

Ambos estados son distintos de `false`: una identidad revocada fue
válida en su momento; no se reescribe la historia.

---

## 16. Múltiples identidades

Un Node puede presentar más de una identidad, cada una con su propio
scope:

```text
Node
 ├── Identity A  (perfil: sensor)
 ├── Identity B  (perfil: control)
 └── Identity C  (identidad efímera / anónima para una sesión puntual)
```

El Core no necesita saber cuántas identidades tiene un Node ni por qué;
solo transporta los Objects que las representan.

---

## 17. Nodos anónimos / sin identidad

Un nodo puede comunicarse sin presentar ninguna identidad. Esto ya está
implícito en `CONTACT_KNOWLEDGE_INVARIANTS.md` Sección 1.3 (`CONTACT no
exige verificación`) y debe extenderse explícitamente:

```text
CONTACT no exige identidad.
```

El conocimiento resultante queda marcado como tal (`identity: unknown`
o ausente), igual que en el ejemplo de nodo no-IPv7 de
`CONTACT_KNOWLEDGE_INVARIANTS.md` Sección 22.

---

## 18. Nodos legacy / no-IPv7

Un nodo no-IPv7 no presenta identidad en el formato de IPv7. IPv7
puede, sin embargo, construir una noción débil de "identidad
observacional" (p. ej. "siempre veo el mismo comportamiento/material
desde este locator"), pero:

```text
Observed consistency ≠ Identity verified
```

Esa distinción evita que IPv7 sobre-interprete comportamiento
observado como si fuera una identidad criptográfica genuina.

---

## 19. Privacidad

Cuestiones que Fase 5.2+ deberá resolver, dejadas explícitamente
abiertas aquí:

* ¿Una identidad debe ser observable por terceros en tránsito (relay),
  o el Core debe poder transportarla de forma opaca incluso para
  intermediarios que la reenvían?
* ¿Existen identidades de un solo uso (unlinkable) además de las
  persistentes?
* ¿Cómo se relaciona esto con la propiedad de `Semantic opacity`
  (invariante 12 de `CONTAINER_OBJECT_WIREFORM_DESIGN.md` Sección 38):
  el Core nunca interpreta `VALUE`, así que tampoco interpreta el
  contenido de un Object de identidad?

Dado que el Core nunca interpreta `VALUE` (Parse ≠ Interpret, ver
`CONTAINER_OBJECT_WIREFORM_DESIGN.md` Sección 36), un relay transparente
ya puede transportar un Object de identidad sin verlo semánticamente.
Eso es una base de privacidad estructural gratuita, heredada de la
Fase 4, que Fase 5 debe aprovechar en vez de reinventar.

---

## 20. Frontera Core / Profile para Identity

Pregunta central de esta fase:

> ¿Puede existir una identidad completamente transportada como
> Object/Profile sin introducir semántica de identidad en el Core?

Respuesta de trabajo (a confirmar en Fase 5.2 con la prueba de fuego
equivalente a la Sección 32 de `CONTAINER_OBJECT_WIREFORM_DESIGN.md`):

```text
CORE
 │
 ├── Packet → Container → Object
 ├── TYPE, ID, LENGTH, VALUE
 ├── validar estructura
 ├── saltar Object de identidad desconocido (unknown ≠ invalid)
 └── relay sin interpretar VALUE
         │
         ▼
     PROFILE
 ├── Identity        (interpretación de TYPE=Identity)
 ├── Authentication  (challenge/response, evidencia)
 ├── Trust           (política de confianza)
 ├── Authorization   (permisos)
 └── Binding / Delegation / Revocation
         │
         ▼
    APPLICATION
```

Si esta separación se sostiene (igual que se sostuvo para Knowledge,
Availability, Probe, etc. en Fase 4), entonces **el Core no necesita
ningún campo nuevo para Identity**. Identity viaja como uno o más
`Object` dentro de un `Container`, con `TYPE` reservado a un
namespace/Profile de identidad, exactamente como cualquier otro
conocimiento.

Esto es preliminar. Hay un caso límite a resolver explícitamente en
Fase 5.2: **si el Core algún día necesita distinguir remitente/
destinatario a nivel de Packet** (no de Container) para enrutar o para
aplicar seguridad de transporte, eso podría requerir un campo mínimo
de identidad en el Packet Header — pero eso sería una decisión de
**enrutamiento/transporte**, no de "qué es una identidad", y debe
tratarse por separado (ver Sección 27 de `IDENTITY_INVARIANTS.md`).

---

## 21. Relación con ID duplicado en Container V1

Nota heredada de la Fase 4.7 (`experimental/README.md`): en el wire
format V1, un `Container` puede tener Objects con `ID` duplicado sin
que el parser lo rechace.

Para `Identity` y `Evidence`, donde `ID` probablemente se use para
expresar bindings (`bound-to`, `supported-by`, `delegates-to`), un `ID`
ambiguo puede ser problemático: una referencia `bound-to → 7` sería
indeterminada si existen dos Objects con `ID=7`.

Este documento no resuelve todavía si V1 debe:

* (A) mantenerse permisivo a nivel de Core y exigir unicidad a nivel de
  Profile cuando se usen referencias; o
* (B) introducir unicidad de `ID` como regla general del Core.

Se deja como **decisión abierta** para Fase 5.2, a resolver antes de
definir cómo Identity/Evidence usan referencias (ver
`IDENTITY_INVARIANTS.md` Sección "Open decisions").

---

## 22. Próximo paso

`IDENTITY_INVARIANTS.md` formaliza las invariantes I-1..I-N que se
derivan de este documento, agrega un modelo de amenazas mínimo, y dejar
explícitas las decisiones abiertas antes de cualquier Byte Freeze de
Identity. Solo después de cerrar invariantes (igual que se hizo en
Fase 3 → Fase 4) se pasará a Fase 5.2: prueba de fuego de Identity sobre
`Container/Object`, y recién más adelante, Fase 5.3: elección de
mecanismo criptográfico concreto.
