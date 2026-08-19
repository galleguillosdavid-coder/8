# IPv7 — Identity Invariants

> **Estado**: Fase 5.1 — diseño conceptual. Sin código, sin bytes, sin
> criptografía concreta.
>
> Estas invariantes deben regir cualquier wire format futuro de
> `Identity`, `Authentication`, `Binding`, `Delegation` y `Revocation`.
> Complementan a `CONTACT_KNOWLEDGE_INVARIANTS.md` y no las contradicen:
> Identity es un componente de Node Knowledge, sujeto a las mismas
> reglas de `TRUTH` y `LIFETIME` ya cerradas en Fase 3.
>
> Ver `IDENTITY_ARCHITECTURE.md` para el razonamiento completo detrás de
> cada invariante.

---

## 0. Invariante fundamental

> **El Core transporta forma. Los Profiles aportan significado.**
> **Identity no es una excepción a esta regla.**

Cualquier formato futuro de Identity debe permitir que el Core
reconozca un Object de identidad como estructura (`TYPE`, `ID`,
`LENGTH`, `VALUE`) sin necesitar saber qué constituye una identidad
válida, qué identidad merece confianza, ni qué relación semántica
existe entre identidades.

---

## I-1 — Identity no es Locator

Una identidad no debe depender de IP, puerto UDP, MAC, ruta o interfaz.
Un nodo puede cambiar de locator y conservar su identidad.

```text
Identity A
   │
   ├── Locator 1
   ├── Locator 2
   └── Locator 3
```

## I-2 — Identity no es Node

Un `Node` es una entidad observable en la red. Una `Identity` es una
afirmación vinculable presentada por (o atribuida a) un Node.

```text
Node
 ├── puede tener Identity
 ├── puede no tener Identity conocida
 └── puede presentar múltiples identidades bajo reglas definidas
```

No se asume `1 Node = 1 Identity`.

## I-3 — Identity debe poder ser transportada como Object

```text
Container
 └── Object
      ├── TYPE = Identity/Profile-defined
      └── VALUE = representación de identidad
```

El Core solamente ve `TYPE`, `ID`, `LENGTH`, `VALUE`. No necesita saber
que el objeto representa una identidad.

## I-4 — Identity no equivale a Trust

```text
IDENTITY ≠ TRUST
```

Saber que una identidad está vinculada criptográficamente a una clave
no implica confiar en ella. La evaluación de confianza es una decisión
de política de Profile/Application, nunca del Core.

## I-5 — Identity no equivale a Knowledge

```text
Identity ≠ Knowledge
```

Identity es el sujeto sobre el que se acumula Knowledge, no un ítem de
Knowledge intercambiable con los demás (CPU, latencia, availability,
etc.).

## I-6 — Identity debe admitir desconocimiento

`CONTACT` no debe exigir identidad conocida ni verificada antes de
permitir comunicación:

```text
UNKNOWN → CONTACT → NODE OBSERVED → IDENTITY PRESENTED → IDENTITY AUTHENTICATED
```

Cada flecha es opcional según el contexto; ninguna es obligatoria para
que exista comunicación.

## I-7 — Binding debe ser explícito

No se deben fusionar `identity`, `key`, `node`, `session` y `locator`
como si fueran el mismo concepto. Las relaciones entre ellos
(`bound-to`, `observed-on`, `presented-in`, `supported-by`) son
explícitas y, si se representan en el wire format, son referencias
locales interpretadas por el Profile — igual que `Evidence` en
`CONTAINER_OBJECT_WIREFORM_DESIGN.md` Sección 29.

## I-8 — Rotación no debe destruir continuidad

Si el material que sostiene una identidad rota (`Key A → Key B`), debe
existir, a nivel de Profile, una manera de demostrar continuidad. El
Core no necesita entender el mecanismo de rotación; solo transporta el
Object que lo demuestra.

## I-9 — Identity admite múltiples niveles epistemológicos, sin escalera obligatoria

```text
DECLARED  → la entidad afirma ser X
OBSERVED  → comportamiento consistente observado a lo largo del tiempo
VERIFIED  → un procedimiento de autenticación demostró control del
            material asociado
```

No se exige `declared → observed → verified`. Los tres estados pueden
coexistir o presentarse por separado, igual que en
`CONTACT_KNOWLEDGE_INVARIANTS.md` Sección 3.2.

## I-10 — El Core no debe convertirse en Identity Engine

> El Core proporciona mecanismos estructurales y criptográficos mínimos
> cuando sean indispensables para transportar o proteger datos, pero no
> decide qué constituye una identidad, qué identidad es válida, qué
> identidad merece confianza, ni qué relación semántica existe entre
> identidades.

```text
                    CORE
                     │
        ┌────────────┴────────────┐
        │                         │
     estructura              mecanismo
        │                         │
        └────────────┬────────────┘
                     ↓
                  PROFILE
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
    Identity      Trust       Knowledge
        │
        ↓
   Application
```

## I-11 — Authentication ≠ Authorization

Demostrar control de una identidad (`authentication`) no implica ningún
permiso concreto (`authorization`). Son capas separadas, ambas fuera
del Core.

## I-12 — Revocation ≠ Expiration ≠ False

```text
Expired  = "ya no podemos asumir que sigue vigente" (tiempo, pasivo)
Revoked  = "se declaró explícitamente inválido"     (acción, activo)
False    = "se demostró que era incorrecto"          (evidencia contraria)
```

Los tres son estados distintos. Una identidad revocada fue válida en su
momento; el historial no se reescribe.

## I-13 — Delegación no transfiere identidad, la extiende

```text
Identity A ──delegates-to──► Identity B
```

`B` actúa con permiso de `A` dentro de un scope definido por el
Profile. `B` no se convierte en `A`; ambas identidades siguen siendo
distinguibles.

## I-14 — Multiplicidad de identidades es válida

Un Node puede presentar más de una identidad simultáneamente, cada una
con su propio scope, sin que el Core necesite saber cuántas ni por qué.

## I-15 — Observación no es identidad verificada

```text
Observed consistency ≠ Identity verified
```

Un nodo no-IPv7 que se comporta de forma consistente desde el mismo
locator no tiene, por eso, una identidad criptográfica verificada. Es
una señal débil (`observed`), no una prueba (`verified`).

## I-16 — Opacidad semántica también aplica a Identity

El Core nunca interpreta `VALUE` (Parse ≠ Interpret,
`CONTAINER_OBJECT_WIREFORM_DESIGN.md` Sección 36). Un relay transparente
puede transportar un Object de identidad sin conocer su contenido. Esta
propiedad, heredada de Fase 4, es la base estructural de cualquier
propiedad de privacidad que Identity necesite; no debe reimplementarse
en el Core.

## I-17 — Reference disambiguation is a Profile responsibility

> Un Profile que interprete `ID` como base de una referencia de binding
> (Identity, Evidence, Delegation, Revocation, Rotation) debe exigir
> `ID` único entre los Objects que participan en esa relación dentro
> del Container. El Core V1 no garantiza unicidad de `ID`; solo
> garantiza que la estructura es parseable.

Descubierta durante la Fase 5.2 (`IDENTITY_FIRE_TEST.md`, Caso P). No
requiere ningún cambio en el Core: `ID` duplicado sigue siendo
estructuralmente válido (Fase 4.7). La invariante recae enteramente
sobre el Profile que decida usar `ID` para expresar bindings.

---

## Amenazas consideradas (modelo mínimo, no exhaustivo)

Estas amenazas no se resuelven en este documento. Se listan para que
Fase 5.2 (prueba de fuego) y Fase 5.3 (mecanismo concreto) las tengan
en cuenta explícitamente.

1. **Suplantación (impersonation)**: un nodo presenta una identidad que
   no le pertenece. Mitigación: `authentication` con evidencia
   verificable (fuera del Core).
2. **Replay de evidencia de autenticación**: reutilizar una prueba de
   autenticación capturada anteriormente. Mitigación: pertenece al
   diseño del procedimiento de authentication (challenge/response,
   nonces, timestamps), no al Core.
3. **Correlación no deseada (linkability)**: un observador correlaciona
   múltiples interacciones de una identidad para construir un perfil no
   consentido. Ver Sección 19 de `IDENTITY_ARCHITECTURE.md` (abierto).
4. **Confusión Identity/Trust**: un Profile o Application que trate
   `verified` como sinónimo de `trusted`. Mitigado arquitectónicamente
   por I-4 y I-11, pero requiere disciplina de implementación.
5. **Ambigüedad de `ID` duplicado en Container V1** al usarse para
   binding/evidence (ver `IDENTITY_ARCHITECTURE.md` Sección 21).
   **Resuelto arquitectónicamente por I-17** (Fase 5.2, Caso P): la
   unicidad de `ID` para binding es responsabilidad del Profile, no del
   Core. No requiere Byte Freeze adicional.
6. **Objeto de identidad malicioso/oversized**: mismo modelo de amenazas
   ya cubierto por el wire format V1 (`CONTAINER_OBJECT_WIREFORM_DESIGN.md`
   Sección 24 y `experimental/` Fase 4.7): `LENGTH` se valida antes de
   reservar memoria, no se interpreta `VALUE`.
7. **Rotación de claves usada para repudiar acciones pasadas**: si `Key
   A` se rota a `Key B`, un actor malicioso podría intentar negar
   acciones firmadas por `Key A`. Mitigación pertenece al diseño de
   continuidad de rotación (I-8), pendiente en Fase 5.3.

---

## Decisiones abiertas (no resolver todavía)

1. **¿Identity es siempre un Object de Profile, o existe un caso límite
   donde el Core necesita un campo mínimo de identidad a nivel de
   Packet** (p. ej. para enrutamiento o seguridad de transporte)? Ver
   `IDENTITY_ARCHITECTURE.md` Sección 20.
2. ~~¿`ID` debe ser único dentro de un Container cuando se usa para
   binding/evidence de Identity?~~ **Resuelto por I-17**: no a nivel de
   Core; el Profile debe exigirlo cuando lo necesite.
3. **¿Cómo se representa la rotación de claves como Object/Evidence?**
   No se decide el mecanismo (cadena de firmas, certificado de
   transición, etc.) todavía.
4. **¿Existen identidades de un solo uso (unlinkable) además de las
   persistentes?** Relacionado con privacidad (Sección 19 de
   `IDENTITY_ARCHITECTURE.md`).
5. **¿Cómo interactúa Identity con Discovery** (`FIRST_CONTACT_DESIGN.md`
   Sección 4.1)? ¿Se puede resolver `identity → locator` sin revelar la
   identidad a intermediarios de Discovery?
6. **¿Qué Profile(s) namespace(s) se reservan para Identity/
   Authentication/Evidence dentro del espacio `TYPE` de Container V1
   (1..254)?** No se asigna ningún valor de `TYPE` todavía.

---

## Próximo paso

Fase 5.2: repetir sobre Identity el mismo ejercicio de "prueba de fuego"
que se hizo en `CONTAINER_OBJECT_WIREFORM_DESIGN.md` Sección 32 para
Container/Object — intentar representar Identity presentada, observada,
verificada, revocada, delegada y rotada exclusivamente como
`Object`/`Container`, sin introducir ningún campo nuevo en el Core, y
verificar si sobrevive. Solo si sobrevive, Fase 5.3 elige mecanismo
criptográfico concreto. No se escribe `identity.py` nuevo ni se congela
ningún byte antes de eso.
