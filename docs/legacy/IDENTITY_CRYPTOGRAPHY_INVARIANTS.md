# IPv7 — Identity Cryptography Invariants (Fase 5.3.1)

> **Estado**: diseño conceptual. Sin algoritmo, sin bytes, sin Byte
> Freeze.
>
> Estas invariantes formalizan `IDENTITY_CRYPTOGRAPHY_DESIGN.md` y
> extienden (no reemplazan) las invariantes I-1..I-17 de
> `IDENTITY_INVARIANTS.md`. Rigen cualquier comparación de algoritmos
> concreta en Fase 5.3.2 y cualquier Byte Freeze en Fase 5.3.3.

---

## CI-1 — Una Identity Proof resuelve Authentication e Integrity, nunca Trust ni Authorization

```text
Proof válida  → "quien la produjo controla el material asociado"
Proof válida ≠ "es confiable"
Proof válida ≠ "tiene permiso de hacer esto"
```

Extiende I-4 e I-11 al dominio criptográfico concreto.

## CI-2 — El Core nunca verifica ni interpreta una Proof

El Core trata cualquier Object que contenga una Identity Proof
exactamente igual que a cualquier otro Object: `TYPE | ID | LENGTH |
VALUE`, opaco. La verificación criptográfica ocurre exclusivamente en
Profile/Application.

## CI-3 — El nivel de vinculación (binding level) debe ser explícito y documentado por Profile

Toda Identity Proof debe declarar (a nivel de Profile, no de Core) si
su `Context` está atado a un Object, a un Container, a una Session, o
a una combinación. Un Profile que no documente esto no puede garantizar
propiedades de replay/relay/fragmentación (ver Sección 4 de
`IDENTITY_CRYPTOGRAPHY_DESIGN.md`).

## CI-4 — Ningún esquema criptográfico requiere que el Core calcule hashes o firmas

Si un esquema exige que el Core compute un hash canónico, verifique una
firma, o participe en cualquier operación criptográfica para poder
enrutar o relayar, el esquema se rechaza sin excepción, sin importar su
seguridad. Esta es la instancia criptográfica directa de I-10 (el Core
no es un Identity Engine).

## CI-5 — Replay es responsabilidad del Profile/Session, nunca del Core

Ya establecido experimentalmente en el Caso N de `IDENTITY_FIRE_TEST.md`.
Cualquier mecanismo anti-replay (nonce, timestamp, contador, ventana de
validez) vive dentro del `VALUE` de la Proof o se apoya en el
`session_id` ya existente en `packet.py`. El Core no gana ningún campo
nuevo para esto.

## CI-6 — Algoritmo desconocido se trata como TYPE desconocido

Un receptor que no reconoce el esquema de firma de una Identity Proof
la trata con las mismas reglas que cualquier Object desconocido
(`Unknown ≠ Invalid`, Fase 4.6/4.7/5.2 Caso B): la salta, opcionalmente
la preserva y reenvía. No existe una ruta especial de "algoritmo no
soportado" a nivel de Core.

## CI-7 — Rotación, revocación y delegación son Objects, no primitivas nuevas

Cualquier operación de gestión de identidad (Sección 7-9 de
`IDENTITY_CRYPTOGRAPHY_DESIGN.md`) se representa como Objects
adicionales dentro de un Container existente, referenciando por `ID`
local. No se introduce ningún nuevo tipo de Container ni Packet.

## CI-8 — Verificación válida e inválida son estructuralmente indistinguibles para el Core

El Core no debe (ni puede) diferenciar una Proof criptográficamente
válida de una inválida: ambas son, para el Core, un `Object` bien
formado o mal formado a nivel estructural. La validez criptográfica es
una propiedad exclusivamente de Profile.

## CI-9 — La elección de algoritmo no debe romper la opacidad semántica (I-16)

Ningún esquema criptográfico puede exigir que el Core lea, valide,
normalice o transforme el contenido de `VALUE`. Esto excluye, por
ejemplo, esquemas que requieran que un router intermedio "rellene" o
"complete" campos de la firma en tránsito.

## CI-10 — El tamaño de la Proof es una propiedad medible, no una preferencia estética

Antes de elegir un algoritmo, su impacto sobre `PATH_MTU` (~1280 bytes
en los ejemplos de `NODE_KNOWLEDGE.md`/`FIRST_CONTACT_DESIGN.md`) y
sobre la necesidad de fragmentación de Container debe medirse
explícitamente contra los criterios de la Sección 13 de
`IDENTITY_CRYPTOGRAPHY_DESIGN.md`, no asumirse.

---

## Modelo de amenazas ampliado (extiende `IDENTITY_INVARIANTS.md`)

1. **Cut-and-paste de Proof entre contextos**: una Proof válida para un
   Object/Container/Session se reutiliza en otro contexto no previsto.
   Mitigación: `Context` explícito (CI-3), a definir en 5.3.2/5.3.3.
2. **Confusión entre "firma inválida" y "Object corrupto"**: un
   Profile que trate ambos casos igual puede ocultar ataques
   deliberados detrás de errores de transporte. Deben distinguirse a
   nivel de Profile (el Core ya los trata igual por diseño, CI-8).
3. **Downgrade de algoritmo**: un atacante en posición de relay podría
   intentar sustituir una Proof por otra de un algoritmo más débil.
   Mitigación: el `Subject`/`Context` de la Proof debe amarrar
   inequívocamente qué algoritmo se usó (a definir en 5.3.2); el Core
   no puede prevenir esto porque no interpreta `VALUE` (I-16) — es
   exclusivamente responsabilidad de Profile.
4. **Ambigüedad de key id ante ID duplicado**: extiende I-17. Si la
   referencia a una clave usa `ID` local y el Container tiene IDs
   duplicados, el Profile debe resolver la ambigüedad antes de
   verificar, o rechazar el Container.
5. **Explosión de tamaño por rotación/delegación en cadena**: cadenas
   largas de rotación o delegación pueden acercarse a los límites de
   `PAYLOAD_LENGTH`/`OBJECT_COUNT` de Container V1 (255 objetos, 65535
   bytes). No es una amenaza de seguridad per se, pero es una
   restricción de diseño a considerar en 5.3.2/5.3.3.

---

## Decisiones abiertas para Fase 5.3.2

1. **Nivel de vinculación**: Object / Container / Session / combinación
   (Sección 4 de `IDENTITY_CRYPTOGRAPHY_DESIGN.md`).
2. **Ubicación de la clave pública**: embebida / referenciada /
   externa (Sección 5).
3. **Mecanismo de Key ID**: huella dentro de `VALUE` vs. referencia
   local por `ID` (Sección 6).
4. **Delegación transitiva**: ¿se permite que B delegue a su vez?
   (Sección 9).
5. **Familia criptográfica**: Ed25519 / ML-DSA / híbrido / otra,
   evaluada contra las propiedades de la Sección 13 de
   `IDENTITY_CRYPTOGRAPHY_DESIGN.md`.
6. **Namespace de `TYPE`** reservado para Identity Proof y sus
   variantes (rotación, revocación, delegación) dentro del rango
   1..254 de Object V1. No se asigna ningún valor todavía.
7. **Canonicalización**: si el nivel de vinculación elegido es
   Container, ¿se reutiliza la canonicalización ya prevista en
   `CONTAINER_OBJECT_WIREFORM_DESIGN.md` Sección 40.8 (orden por ID
   ascendente) o se necesita una regla adicional?

---

## Próximo paso

Fase 5.3.2: tomar al menos un candidato concreto (por ejemplo, Ed25519
como baseline de comparación) y ejecutar la prueba de falsación de la
Sección 12 de `IDENTITY_CRYPTOGRAPHY_DESIGN.md` (Q1-Q5), midiendo las
propiedades de la Sección 13 contra al menos dos familias
criptográficas (p. ej. Ed25519 vs. ML-DSA vs. híbrido). Solo si un
candidato sobrevive la prueba de falsación y resulta preferible según
esas propiedades medidas, Fase 5.3.3 define el Byte Freeze de Identity
Proof. No se escribe código de firma/verificación antes de eso.
