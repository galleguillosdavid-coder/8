# IPv7 — Identity Cryptography Design (Fase 5.3.1)

> **Estado**: diseño conceptual abstracto. **Ningún algoritmo
> criptográfico se elige en este documento.** No hay bytes, no hay
> tamaños de clave/firma, no hay Byte Freeze.
>
> Precondición: `IDENTITY_ARCHITECTURE.md` (5.1), `IDENTITY_INVARIANTS.md`
> (5.1) e `IDENTITY_FIRE_TEST.md` (5.2) están cerrados. La hipótesis
> "Identity cabe como Object/Container V1 sin modificar el Core"
> sobrevivió 34/34 pruebas, incluyendo relay ciego y el Caso N
> (replay). Este documento no vuelve a discutir esas invariantes; las
> usa como restricciones de diseño.

---

## 0. Qué NO decide este documento

* No elige Ed25519, ML-DSA, ninguna curva, ningún esquema híbrido.
* No fija tamaños de clave, firma, hash ni ningún campo binario.
* No modifica `container_v1.py` ni `ipv7_mvp/`.
* No asigna ningún `TYPE` real dentro del espacio 1..254 de Object V1.

Ese trabajo es Fase 5.3.2 (comparación de familias criptográficas) y
Fase 5.3.3 (Byte Freeze de Identity Proof), y ocurre **después** de que
este modelo abstracto pase su propia prueba de falsación (Sección 12).

---

## 1. El problema exacto que queremos resolver

No partimos de "necesitamos firmas digitales". Partimos de una pregunta
más estrecha:

> ¿Qué significa, dentro de IPv7, que una entidad **demuestre posesión**
> de una Identity?

Respuesta de trabajo:

```text
Demostrar posesión de una Identity significa producir una prueba que:

1. Solo puede producirse por quien controla cierto material
   (típicamente una clave privada u otro secreto vinculado a la
   Identity).
2. Puede verificarse por cualquier receptor que conozca el material
   público correspondiente.
3. Está vinculada a un contexto específico (Sección 4), de forma que
   la prueba no sea trivialmente reutilizable fuera de ese contexto.
```

Esto separa **posesión** (authentication) de **identidad** (quién se
afirma ser) y de **confianza** (si el receptor decide actuar en base a
esa prueba) — exactamente I-4 e I-11 de `IDENTITY_INVARIANTS.md`.

---

## 2. Cinco preguntas que no deben mezclarse

Heredadas de Fase 5.1, aquí se convierten en requisitos de diseño
criptográfico:

```text
IDENTITY        → ¿quién afirma ser?
AUTHENTICATION  → ¿puede demostrarlo?
INTEGRITY       → ¿el mensaje/objeto fue alterado en tránsito?
AUTHORIZATION   → ¿tiene permiso de hacer esto?
TRUST           → ¿cuánto confiamos en esta afirmación/evidencia?
```

Regla de diseño:

> **Una prueba criptográfica (`Identity Proof`) resuelve, como máximo,
> Authentication e Integrity.** Nunca debe, por sí sola, resolver
> Trust ni Authorization. Un Profile que trate "firma válida" como
> sinónimo de "autorizado" o "confiable" rompe I-4/I-11
> independientemente del algoritmo elegido.

---

## 3. Componentes de una Identity Proof (modelo abstracto)

```text
                 Identity Proof
                       │
          ┌────────────┴────────────┐
          │                         │
       Subject                    Context
          │                         │
   ¿de quién es la              ¿bajo qué circunstancia
    afirmación?                  se produjo esta prueba?
          │                         │
          └────────────┬────────────┘
                       │
                    Material
              (qué exactamente se firma/prueba)
                       │
                  Proof/Signature
```

### 3.1 Subject

Qué identidad afirma la prueba. Puede ser:

* una referencia local (`ID` dentro del Container, con las salvedades
  de I-17: el Profile debe garantizar unicidad si la usa para esto);
* un identificador estable transportado en otro Object (p. ej. una
  clave pública o su huella, ya presente como `IDENTITY_DECLARED`).

### 3.2 Context

Qué delimita el alcance de la prueba para que no sea reutilizable fuera
de su propósito original. Candidatos a evaluar en 5.3.2/5.3.3 (sin
decidir todavía):

* el propio `Container` que transporta la prueba (hash del Container
  canónico, ver Sección 40.8 de `CONTAINER_OBJECT_WIREFORM_DESIGN.md`);
* un `Session` (contexto temporal de comunicación, `session.py`);
* un desafío explícito (`challenge`) emitido por el verificador;
* una combinación (p. ej. `challenge` + `session_id`).

Esta es la pregunta más importante de todo el documento (Sección 4).

### 3.3 Material firmado

Qué bytes exactamente entran a la operación criptográfica. No se asume
`signature = sign(VALUE)` porque:

* `VALUE` por sí solo no incluye `Context`;
* firmar solo `VALUE` no protege contra "cortar y pegar" ese mismo
  Object en otro Container con otro significado (Sección 5).

### 3.4 Proof / Signature

El resultado de la operación criptográfica. Es, para el Core, un blob
opaco más dentro de `VALUE` — sin excepciones (Sección 8).

---

## 4. ¿A qué nivel se vincula una Identity Proof?

Pregunta central, heredada del problema planteado por el usuario. Se
listan las opciones sin decidir:

```text
Nivel de vinculación posible:

(a) Object      → se firma un Object individual
(b) Container   → se firma el Container completo (canónico)
(c) Session      → se firma algo ligado a una sesión específica
(d) Combinación → p. ej. Object + referencia a Session + nonce
```

### 4.1 Consecuencias de cada nivel

| Nivel | Relay | Replay | Fragmentación | Reempaquetado |
|-------|-------|--------|----------------|----------------|
| (a) Object | Un relay puede reenviar el Object sin romper la firma, incluso si reordena otros Objects del Container | Débil por sí solo: el mismo Object firmado sigue siendo válido en cualquier Container futuro, salvo que el `VALUE` incluya su propio nonce/contexto | Un Object fragmentado (Sección 40.7 del wireform) rompe la firma si esta cubre bytes crudos del Object antes de reensamblar | Un Object firmado puede moverse a otro Container sin invalidar la firma — puede ser deseable (portabilidad) o peligroso (reuso fuera de contexto), según el Profile |
| (b) Container | Requiere que el relay preserve el Container completo sin alterar orden de Objects si la canonicalización depende de orden | Ata la prueba a *ese* Container específico; sigue siendo replayable si el Container completo se retransmite igual (Caso N ya documentó que esto no es resoluble por el Core) | El Container debe reensamblarse antes de poder verificar cualquier firma que lo cubra — coherente con la regla ya establecida ("el Profile nunca ve fragmentos", Sección 40.7) | Un Container firmado no puede reordenarse sin invalidar la firma, salvo que se firme sobre la forma canónica (Sección 40.8) |
| (c) Session | Ata la prueba a una sesión, mitigando replay entre sesiones distintas | Sigue sin resolver replay *dentro* de la misma sesión sin nonce adicional | Ortogonal a fragmentación de Container | Ortogonal a reempaquetado de Objects individuales |
| (d) Combinación | Máxima flexibilidad, máxima complejidad | Puede resolver replay si incluye nonce/timestamp | Depende de qué se combine | Depende de qué se combine |

### 4.2 Restricción arquitectónica (no negociable)

> **Cualquiera que sea el nivel elegido, el Core nunca debe necesitar
> saber que existe una firma, ni participar en su verificación.** El
> Core sigue viendo Objects opacos. La vinculación a Container o
> Session es un cálculo que hace el Profile *usando* información que
> el Core ya expone estructuralmente (los bytes del Container, el
> `session_id` del Packet), sin que el Core interprete nada nuevo.

Esto es consistente con I-16 (opacidad semántica) y con el hallazgo del
Caso N: el `session_id` ya existe en `packet.py`; un Profile de
autenticación puede *usarlo* como parte del contexto firmado sin que el
Core cambie en absoluto.

### 4.3 Decisión diferida

Este documento no elige (a), (b), (c) o (d). Se difiere a Fase 5.3.2,
donde se evaluará contra los casos de la prueba de falsación (Sección
12), en particular relay ciego, fragmentación y replay.

---

## 5. Dónde vive la clave pública

Tres opciones, sin decidir:

```text
(1) Embebida   → la clave pública viaja dentro del mismo VALUE que la
                  identidad declarada (auto-contenida)
(2) Referenciada → un Object separado contiene la clave; la Identity
                  la referencia por ID local (como Evidence)
(3) Externa    → la clave se resuelve fuera de banda (Discovery,
                  directorio, TOFU) y el Container solo transporta un
                  identificador corto (huella/hash)
```

Ninguna opción exige cambios en el Core: las tres siguen siendo
Objects genéricos o referencias locales, ya validadas por Fase 4/5.2.

Compromiso de tamaño vs. Fase 5.3.2: (1) es autosuficiente pero más
pesado por mensaje; (3) es liviano pero depende de un mecanismo de
resolución de claves que debe diseñarse aparte (fuera de alcance de
este documento).

---

## 6. Identificación de la clave (Key ID)

Si se permite rotación (Sección 7) o múltiples identidades (I-14), se
necesita poder distinguir *qué* clave produjo una prueba dada. Esto
puede resolverse:

* con una huella/hash de la clave dentro del `VALUE` (opaco para el
  Core);
* con una referencia local `ID` a un Object de tipo "clave" dentro del
  mismo Container (sujeto a I-17: unicidad exigida por el Profile).

No se decide el mecanismo. Se establece la restricción: **el Core nunca
necesita parsear un "key id"** — es contenido de `VALUE` o una
referencia local ya soportada por Object V1.

---

## 7. Rotación (elaboración de I-8)

Modelo abstracto de continuidad:

```text
Key A (activa hasta t1)
   │
   │ Rotation Proof: "Key B es la sucesora de Key A"
   │ (firmado con Key A, referenciando Key B)
   ▼
Key B (activa desde t1)
```

Preguntas a resolver en 5.3.2/5.3.3, no aquí:

* ¿La prueba de rotación firma solo la referencia a la nueva clave, o
  también un rango de validez temporal?
* ¿Qué pasa con pruebas producidas por `Key A` después de `t1`? (Esto
  es una política de Profile — revocación temporal — no del Core.)

El Object de rotación sigue el mismo esquema `TYPE | ID | LENGTH |
VALUE` que cualquier otro (ya demostrado en el Caso G de
`IDENTITY_FIRE_TEST.md`).

---

## 8. Revocación (elaboración de I-12)

```text
Revocation Proof: "Key A / Identity X ya no debe considerarse válida
                    a partir de t"
```

Firmada, en principio, por la propia identidad que se revoca, por una
identidad delegante (Sección 9), o por una autoridad de Profile
definida fuera del Core. Este documento no elige cuál; solo constata
que en los tres casos el mecanismo es "otro Object, con su propia
Proof, referenciando el `ID` a revocar" — ya validado por el Caso H.

Revoked ≠ Expired ≠ False sigue vigente (I-12): la Revocation Proof no
reescribe pruebas pasadas, las marca inválidas desde cierto punto en
adelante.

---

## 9. Delegación (elaboración de I-13)

```text
Delegation Proof: "Identity A autoriza a Identity B a actuar dentro de
                    <scope>, firmado por A"
```

`scope` es contenido de Profile, opaco para el Core (igual que en el
Caso I de `IDENTITY_FIRE_TEST.md`). La pregunta de diseño diferida:
¿puede B delegar a su vez (delegación transitiva)? Este documento no
lo resuelve; lo deja como decisión abierta de 5.3.2.

---

## 10. Replay y expiración

Ya resuelto conceptualmente por el Caso N (`IDENTITY_FIRE_TEST.md`):

> El Core no puede ni debe detectar replay. Cualquier defensa contra
> replay (nonce, timestamp, contador, ventana de validez) debe vivir
> dentro del `VALUE` de la Proof o apoyarse en el `session_id` ya
> existente en `packet.py` — nunca en un campo nuevo del Core.

Expiración sigue el modelo de lifetime ya cerrado en Fase 3
(`fresh → stale → expired`, `CONTACT_KNOWLEDGE_INVARIANTS.md` Sección
4): una Identity Proof puede incluir su propia validez temporal dentro
de `VALUE`, interpretada por el Profile, nunca por el Core.

---

## 11. Compatibilidad con relay, fragmentación y multiplicidad

* **Relay ciego**: cualquier esquema elegido debe seguir permitiendo
  que un nodo que no conoce el algoritmo transporte la Proof intacta
  (ya demostrado estructuralmente en 5.2 para Objects genéricos; la
  Proof no es distinta en este sentido).
* **Fragmentación**: si se opta por vincular la Proof al Container
  completo (nivel (b) de la Sección 4), debe respetarse la regla ya
  cerrada: "el Profile nunca ve fragmentos" — la verificación ocurre
  después del reensamblaje, nunca durante.
* **Múltiples identidades**: nada en este modelo impide que un Node
  presente varias Identity Proofs en el mismo Container (Caso E), cada
  una con su propio Subject/Context/Material/Proof.
* **Identidad anónima/pseudónima**: un Container sigue pudiendo omitir
  toda Identity Proof (Caso J); la ausencia de prueba no es un error.
* **Algoritmo desconocido**: un receptor que no reconoce el esquema de
  firma (p. ej. un algoritmo `TYPE`/namespace más nuevo) debe poder
  tratar la Proof como cualquier Object desconocido: `Unknown ≠
  Invalid`, la salta y opcionalmente la reenvía (ya validado por el
  Caso B).

---

## 12. Prueba de falsación para el modelo abstracto (previa a elegir algoritmo)

Regla, análoga a la de `IDENTITY_FIRE_TEST.md`:

> Si el modelo de Identity Proof descrito en este documento exige que
> el Core conozca el algoritmo, interprete el `VALUE`, evalúe validez
> criptográfica, o participe en decisiones de Trust/Authorization, el
> modelo **falla arquitectónicamente** y debe rediseñarse antes de
> comparar algoritmos concretos.

Casos a verificar en Fase 5.3.2 con al menos un candidato concreto
(sin comprometerse todavía a cuál):

```text
Q1  Proof transportada como Object opaco, TYPE ilustrativo desconocido
    para un relay intermedio → debe sobrevivir relay ciego.
Q2  Verificación exitosa y fallida deben producir el mismo tratamiento
    estructural en el Core (el Core no distingue "firma válida" de
    "firma inválida"; eso es responsabilidad del Profile).
Q3  Una Proof corrupta a nivel de bytes (LENGTH inconsistente, etc.)
    debe seguir cayendo en las mismas reglas de corrupción ya
    validadas en Fase 4.7, sin código adicional en el Core.
Q4  Rotación, revocación y delegación deben seguir representándose
    como Objects adicionales referenciando por `ID`, sin nuevo tipo de
    Container.
Q5  El nivel de vinculación elegido (Object/Container/Session/
    combinación) no debe requerir que el Core calcule ni verifique
    ningún hash o firma por sí mismo.
```

---

## 13. Propiedades que debe tener el formato antes de elegir algoritmo

Estas propiedades condicionan la comparación de familias criptográficas
en Fase 5.3.2 — no son una preferencia por ningún algoritmo, son
criterios de medición:

```text
tamaño de clave publica
tamaño de firma/proof
coste de verificación (CPU, especialmente en dispositivos pequeños)
coste de generación de firma
determinismo (¿la firma es reproducible o requiere aleatoriedad?)
statefulness (¿el esquema exige que el firmante mantenga estado,
    p. ej. contadores, para evitar reuso de material?)
resistencia post-cuántica
madurez / estandarización
impacto sobre PATH_MTU (los ejemplos de Node Knowledge usan MTU
    observado ~1280 bytes; una Proof de varios KB puede forzar
    fragmentación del Container incluso para un First Contact mínimo)
impacto sobre el límite V1 de 65535 bytes de VALUE (holgado para casi
    cualquier esquema, pero el límite real de interés es el PATH_MTU,
    no el límite de Object V1)
canonicalización requerida (¿la Proof exige un orden determinista de
    Objects dentro del Container, como ya prevé la Sección 40.8 del
    wireform design para Signed Container?)
```

Ninguna de estas propiedades se mide todavía. Se documentan aquí para
que la comparación de 5.3.2 no se decida "por sensación de seguridad"
sino contra estos criterios explícitos, igual que se hizo con los
layouts de bytes en Fase 4.4.

---

## 14. Frontera Core / Profile / Application para criptografía de Identity

```text
              APPLICATION
                   │
             CRYPTO PROFILE
     (algoritmo, Subject, Context, Material,
      verificación, Trust, Authorization)
                   │
          ┌────────┴────────┐
          │  IDENTITY PROOF │
          │  (Subject,      │
          │   Context,      │
          │   Material,     │
          │   Signature)    │
          └────────┬────────┘
                   │
              OBJECT V1
       (TYPE | ID | LENGTH | VALUE)
                   │
          ┌────────┴────────┐
          │       CORE      │
          │                 │
          │ parse           │
          │ validate struct │
          │ skip unknown    │
          │ relay           │
          └─────────────────┘
```

El Core no aparece en ningún nivel por encima de `Object V1`. Esa es la
propiedad que Fase 5.3.2 debe preservar al comparar algoritmos
concretos.

---

## 15. Próximo paso

Fase 5.3.2: comparar familias criptográficas concretas (p. ej. Ed25519,
ML-DSA, esquema híbrido) exclusivamente contra las propiedades de la
Sección 13 y la prueba de falsación de la Sección 12 — todavía sin
elegir una, salvo que la comparación deje un candidato claramente
preferible. Fase 5.3.3 recién ahí definiría el Byte Freeze de Identity
Proof. Ningún código se escribe antes de cerrar 5.3.2.
