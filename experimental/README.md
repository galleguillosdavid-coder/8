# IPv7 — Experimental Wire Format V1

Este directorio contiene la implementacion experimental aislada del wire
format `Container → Object` V1 (Fases 4.6 y 4.7). No modifica el Core de
`ipv7_mvp/`.

## Estado

```text
FASE 4 — CONTAINER / OBJECT / IDTLV
├── 4.6 Implementacion experimental ...... 18/18 PASS
└── 4.7 Adversarial Validation ........... 27/27 PASS

FASE 4: CLOSED

FASE 5 — IDENTITY
├── 5.1 Identity Architecture & Invariants ... CONCEPTUAL, CERRADA
├── 5.2 Identity Fire Test ................... 7/7 PASS
├── 5.3 Identity Crypto Decision .............. Ed25519 (V1), CERRADA
└── 5.4 Identity Engine (codigo real) ......... 14/14 PASS

TOTAL EXPERIMENTAL: 48/48 PASS
ipv7_mvp/ y container_v1.py (Core): SIN MODIFICAR
```

## Archivos

- `container_v1.py` — encoder/decoder estrictamente estructural (Core, Fase 4).
- `hex_vectors.py` — vectores de round-trip y casos de uso (Fase 4).
- `test_container_v1.py` — suite de tests, incluyendo Fase 4.7 adversarial.
- `identity_scenarios.py` — escenarios de Identity (Fase 5.2) construidos
  exclusivamente con `ContainerV1`/`ObjectV1`, sin tocar `container_v1.py`.
- `test_identity_fire_test.py` — prueba de fuego adversarial de Identity:
  round-trip, unknown type, relay ciego, ID duplicado, replay, objeto
  malicioso.
- `identity/` — **Fase 5.4, Identity Engine con criptografia real
  (Ed25519, via `cryptography`)**:
  - `identity.py` — generacion de claves, `Identity`/`PublicIdentity`,
    firma, fingerprint (SHA-256).
  - `key_store.py` — persistencia de identidad en disco (JSON + base64).
  - `binding.py` — construye Objects `IDENTITY_KEY` / `IDENTITY_PROOF` /
    `IDENTITY_ROTATION` sobre `ContainerV1`/`ObjectV1`, sin tocar el Core.
  - `verification.py` — resuelve referencias por `ID` (aplicando I-17:
    rechaza referencias ambiguas) y verifica firmas.
  - `test_identity_engine.py` — 14 tests: persistencia, firma/verificacion,
    contexto incorrecto, Object manipulado, identidad equivocada,
    ID duplicado (Caso P con criptografia real), relay ciego real
    A→B→C, rotacion.

## Ejecutar tests

```bash
python -m unittest experimental.test_container_v1 experimental.test_identity_fire_test experimental.identity.test_identity_engine
```

## Autoridad normativa

Los hex dumps del documento de diseno (`docs/CONTAINER_OBJECT_WIREFORM_DESIGN.md`)
son ilustrativos. Durante la Fase 4.6 se descubrieron inconsistencias entre las
longitudes declaradas (`LENGTH`, `PAYLOAD_LENGTH`) y los bytes ASCII mostrados en
algunos ejemplos.

La **autoridad** para este modulo es la especificacion V1 congelada (Byte Freeze):

- Container Header: 5 bytes (`VERSION | FLAGS | OBJECT_COUNT | PAYLOAD_LENGTH`)
- Object Header: 4 bytes (`TYPE | ID | LENGTH`)
- Big endian
- `ID` 0..254 validos, 255 reservado
- `TYPE` 0 y 255 reservados
- `LENGTH` 0..65535, 0 valido

Los **vectores ejecutables** en `hex_vectors.py` son la referencia de prueba.
Se generan a partir de las descripciones del documento, pero con longitudes
ajustadas para ser estructuralmente validos segun V1.

Regla para futuros desarrolladores:

> Si un hex dump antiguo contradice el Byte Freeze, gana el Byte Freeze.
> Los tests pasados son la referencia ejecutable.

## Nota sobre `ID` duplicado (resuelta en Fase 5.2 — I-17)

En V1 un Container puede contener varios Objects con el mismo `ID` sin que el
parser estructural lo rechace. La Fase 5.2 (`docs/IDENTITY_FIRE_TEST.md`,
Caso P; `docs/IDENTITY_INVARIANTS.md`, I-17) confirma que esto no requiere
cambios en el Core: cualquier Profile que use `ID` como base de una
referencia de binding (Identity, Evidence, Rotation, Revocation,
Delegation) debe exigir unicidad de `ID` por su cuenta. El Core V1 no lo
garantiza y no debe hacerlo.

## Frontera Core / Profile

El Core V1 maneja:

- Packet → Container → Object
- TYPE, ID, LENGTH, VALUE
- Validacion estructural, saltar desconocidos, relay

El Core V1 NO maneja:

- CPU, latencia, Availability, Capability, Probe
- Identity, Evidence, First Contact
- Significado de `VALUE`

Esa separacion se demostro experimentalmente con los tests de relay: `B` no
conoce los tipos y aun asi reenvia `A.bytes == C.bytes`.

## Fase 5.3/5.4 — decision criptografica y Engine real

`docs/IDENTITY_CRYPTO_DECISION.md` cierra la evaluacion de
`docs/DESARROLLO_CHECK.md` ("Ed25519, ML-DSA, AES-GCM, HKDF —
evaluación en curso") con datos reales del entorno (`cryptography`
50.0.0 disponible con Ed25519/X25519/ChaCha20-Poly1305/HKDF; `ml_dsa` y
`blake3` NO disponibles). Decision para V1: **Ed25519** para firma,
**SHA-256** para fingerprint, PQC diferido explicitamente.

`experimental/identity/` implementa esto como código real, sin ninguna
modificación a `container_v1.py`: la Identity es, literalmente, otro
consumidor de `ContainerV1`/`ObjectV1` — exactamente la propiedad que
`IDENTITY_ARCHITECTURE.md` Sección 20 planteaba como hipótesis y que
`IDENTITY_FIRE_TEST.md` sometió a prueba de fuego.

## Dependencias

`experimental/identity/` requiere el paquete `cryptography` (ya usado
en `src/core/network.py`). No se agregan dependencias nuevas.
