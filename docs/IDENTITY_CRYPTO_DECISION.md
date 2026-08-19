# IPv7 — Identity Crypto Decision (Fase 5.3)

> **Estado**: decisión cerrada para V1 experimental. Corta y decisiva,
> no una nueva ronda de diseño. Extiende `IDENTITY_CRYPTOGRAPHY_DESIGN.md`
> e `IDENTITY_CRYPTOGRAPHY_INVARIANTS.md` (Fase 5.3.1), que siguen
> vigentes sin cambios.
>
> **Nota de honestidad**: no existe en este proyecto ninguna
> especificación previa (HRS-HDN, X25519+BLAKE3+ChaCha20 congelados,
> handshake Hello→Challenge→Proof→SessionConfirm). Lo único que existía
> antes de este documento era `docs/DESARROLLO_CHECK.md` línea 69:
> *"Ed25519, ML-DSA, AES-GCM, HKDF (evaluación en curso)"*. Esta fase
> cierra esa evaluación con datos reales del entorno, no con supuestos.

---

## 1. Comparación

| Propiedad | Ed25519 | ML-DSA | Híbrido (Ed25519+ML-DSA) |
|-----------|---------|--------|---------------------------|
| Firma clásica | ✅ | — | ✅ |
| Resistencia post-cuántica | — | ✅ | ✅ |
| Tamaño de firma | 64 bytes | ~2.4–4.6 KB según nivel | suma de ambas |
| Tamaño de clave pública | 32 bytes | ~1.3–2.6 KB según nivel | suma de ambas |
| CPU (firmar/verificar) | bajo | mayor | mayor |
| Impacto en PATH_MTU (~1280 B) | despreciable | una sola Identity Proof puede rondar o superar el PATH_MTU típico, forzando fragmentación de Container incluso en First Contact mínimo | igual o peor que ML-DSA solo |
| Disponibilidad real en este entorno | **`cryptography` 50.0.0, instalada, soporte nativo** | **no disponible** en `cryptography` 50.0.0 (`ml_dsa` no existe en este build); requeriría dependencia adicional no evaluada | requiere la dependencia faltante de ML-DSA |
| Complejidad de integración | baja | media/alta (dependencia externa no verificada) | alta |

Verificación de disponibilidad real (no supuesta), ejecutada en este
entorno:

```text
cryptography==50.0.0  → ed25519 OK, x25519 OK, chacha20poly1305 OK, hkdf OK
ml_dsa                → NO disponible en cryptography 50.0.0
blake3 (paquete)      → NO instalado
pynacl                → NO instalado
```

---

## 2. Pregunta fundamental

> ¿Necesitamos identidad post-cuántica en V1, o necesitamos primero una
> identidad funcional, compacta y experimentalmente integrable?

Respuesta: **V1 necesita lo segundo.** Introducir PQC en el Core (o en
el Profile de identidad) solo porque existe, sin una dependencia
disponible, sin medir su impacto real en `PATH_MTU`, y sin haber
todavía ni siquiera un Identity Engine funcional, viola la misma
disciplina que nos protegió en Fase 4 y 5.1/5.2: no se agrega
complejidad "por si acaso".

---

## 3. Decisión (V1 experimental)

```text
Firma / Authentication  → Ed25519
Key exchange            → X25519          (reservado para Fase 6, sesión cifrada)
AEAD (cifrado sesión)   → ChaCha20-Poly1305  (reservado para Fase 6)
Derivación de sesión    → HKDF-SHA256        (reservado para Fase 6)
Fingerprint / Key ID    → SHA-256            (stdlib `hashlib`, ya usado en packet.py;
                                              se descarta BLAKE3 por no estar instalado
                                              y no aportar nada crítico en V1)
Post-quantum (ML-DSA)   → NO en V1. Diferido explícitamente a una fase
                           futura, cuando exista una dependencia
                           disponible y medida contra estas mismas
                           propiedades.
```

Todo lo anterior proviene de `cryptography` 50.0.0, ya utilizada en
`src/core/network.py` — no se agrega ninguna dependencia nueva para
Identity/Authentication en V1.

---

## 4. Restricciones heredadas de Fase 5.3.1 (no negociables)

* **CI-4**: el Core nunca calcula ni verifica firmas. Todo lo anterior
  vive en Profile/Application, nunca en `container_v1.py`.
* **CI-6**: un algoritmo desconocido (incluida una futura variante
  PQC) se trata como `TYPE` desconocido — `Unknown ≠ Invalid`.
* **CI-9**: el contenido de la clave/firma es opaco para el Core; vive
  dentro de `VALUE`.
* El namespace de `TYPE` para Identity sigue sin asignarse en el
  espacio real del Core; los valores usados en el código experimental
  siguen siendo ilustrativos (documentado en cada archivo).

---

## 5. Qué decide y qué no decide este documento

Decide:

* Algoritmo de firma para Identity Proof en V1: **Ed25519**.
* Algoritmo de fingerprint/Key ID: **SHA-256**.
* Que PQC queda fuera de V1, explícitamente, con motivo documentado.

No decide todavía (se resuelve en la implementación de Fase 5.4/5.5 de
forma experimental, sin Byte Freeze):

* El nivel de vinculación exacto (Object/Container/Session/combinación,
  Sección 4 de `IDENTITY_CRYPTOGRAPHY_DESIGN.md`) — la implementación
  de Fase 5.4 lo resuelve de forma concreta y documentada en el propio
  código (`experimental/identity/verification.py`), pero sigue sin ser
  un Byte Freeze del Core.
* Ubicación final de la clave pública (embebida/referenciada/externa).
* Uso real de X25519/ChaCha20/HKDF: reservado para cuando se aborde la
  sesión cifrada (Fase 6), no para el Identity Engine de Fase 5.4.

---

## 6. Próximo paso

Fase 5.4 — Identity Engine: implementación real en
`experimental/identity/` usando Ed25519 vía `cryptography`, construida
exclusivamente como consumidor de `ContainerV1`/`ObjectV1` (Fase 4),
sin modificar `container_v1.py`. Ver Sección 20 de
`IDENTITY_ARCHITECTURE.md` para la frontera Core/Profile que esta
implementación debe respetar.
