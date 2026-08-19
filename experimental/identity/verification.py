"""
IPv7 Identity Engine — verificacion (Fase 5.4, experimental).

Resuelve referencias locales por `ID` dentro de un ContainerV1 y
verifica Identity Proofs. Vive enteramente en el Profile: el Core
(container_v1.py) nunca se entera de que esto existe.

Aplica explicitamente I-17 (IDENTITY_INVARIANTS.md): si mas de un
Object comparte el `ID` referenciado, la referencia es ambigua y este
modulo lo rechaza en vez de adivinar.
"""

from ..container_v1 import ContainerV1, ObjectV1
from .binding import (
    TYPE_IDENTITY_KEY,
    parse_proof_object,
    parse_rotation_object,
    public_key_from_object,
)


class VerificationError(Exception):
    """Error de verificacion (firma invalida, referencia ambigua, etc.)."""
    pass


def _resolve_unique(container: ContainerV1, ref_id: int) -> ObjectV1:
    """
    Resolver un `ID` local a un unico Object. Lanza VerificationError si
    no existe o si es ambiguo (I-17).
    """
    candidates = [o for o in container.objects if o.id == ref_id]
    if len(candidates) == 0:
        raise VerificationError(f"Referencia a ID inexistente: {ref_id}")
    if len(candidates) > 1:
        raise VerificationError(
            f"Referencia ambigua: {len(candidates)} Objects comparten ID={ref_id} "
            f"(I-17: el Profile debe exigir unicidad de ID para binding)"
        )
    return candidates[0]


def verify_identity_proof(
    container: ContainerV1,
    proof: ObjectV1,
    context: bytes,
) -> bool:
    """
    Verificar un Object IDENTITY_PROOF dentro de `container`, atado a
    `context` (los mismos bytes que uso el firmante).

    Devuelve True/False. Lanza VerificationError solo ante ambiguedad
    estructural de referencia (I-17), nunca ante una firma simplemente
    invalida (eso es False, no una excepcion: CI-8, el Core -y este
    modulo, que actua como Profile- no distinguen "invalido" de
    "atacado").
    """
    ref_id, signature = parse_proof_object(proof)
    subject = _resolve_unique(container, ref_id)

    if subject.type != TYPE_IDENTITY_KEY:
        return False

    public_identity = public_key_from_object(subject)
    material = subject.value + context
    return public_identity.verify(material, signature)


def verify_rotation(
    container: ContainerV1,
    rotation: ObjectV1,
    new_identity_key_object: ObjectV1,
) -> bool:
    """
    Verificar que `rotation` fue firmada por la clave vieja
    (referenciada dentro de `container`) sobre la clave publica nueva.
    """
    ref_id, signature = parse_rotation_object(rotation)
    old_key_object = _resolve_unique(container, ref_id)

    if old_key_object.type != TYPE_IDENTITY_KEY:
        return False

    old_public_identity = public_key_from_object(old_key_object)
    return old_public_identity.verify(new_identity_key_object.value, signature)
