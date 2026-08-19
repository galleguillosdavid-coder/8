"""
IPv7 Identity Engine — binding entre Identity y Container/Object
(Fase 5.4, experimental).

Construye Objects V1 (TYPE | ID | LENGTH | VALUE) para transportar una
clave de identidad y una prueba (Identity Proof), reutilizando
ContainerV1/ObjectV1 de Fase 4 SIN MODIFICARLOS.

Los TYPE usados aqui son ilustrativos (namespace de ejemplo, igual que
en experimental/identity_scenarios.py). El Core (container_v1.py)
nunca les asigna significado.

Formato de VALUE (decision de implementacion V1 experimental, NO Byte
Freeze del Core):

    IDENTITY_KEY    VALUE = <32 bytes: clave publica Ed25519 raw>

    IDENTITY_PROOF  VALUE = <1 byte: ID local del Object referenciado>
                            + <64 bytes: firma Ed25519>

    IDENTITY_ROTATION  VALUE = <1 byte: ID local de la key vieja>
                              + <64 bytes: firma de la key vieja sobre
                                 la clave publica nueva>
                              (la clave publica nueva viaja en su propio
                               Object IDENTITY_KEY, como cualquier otra)

El "Context" (Seccion 4 de docs/IDENTITY_CRYPTOGRAPHY_DESIGN.md) se
resuelve aqui como: el llamador decide y pasa explicitamente los bytes
de contexto (challenge, session id, o vacio). Este modulo no fabrica
contexto por su cuenta.
"""

import struct

from ..container_v1 import ObjectV1, ContainerError
from .identity import Identity, PublicIdentity

TYPE_IDENTITY_KEY = 20
TYPE_IDENTITY_PROOF = 22
TYPE_IDENTITY_ROTATION = 23
TYPE_IDENTITY_REVOCATION = 24

_PUBLIC_KEY_LEN = 32
_SIGNATURE_LEN = 64


class BindingError(Exception):
    """Error al construir o interpretar un binding de Identity."""
    pass


def identity_key_object(identity: Identity, obj_id: int) -> ObjectV1:
    """Object que transporta la clave publica de una Identity."""
    return ObjectV1(type=TYPE_IDENTITY_KEY, id=obj_id, value=identity.public_key_bytes)


def public_key_from_object(obj: ObjectV1) -> PublicIdentity:
    """Reconstruir una PublicIdentity a partir de un Object IDENTITY_KEY."""
    if obj.type != TYPE_IDENTITY_KEY:
        raise BindingError(f"Object no es IDENTITY_KEY (TYPE={obj.type})")
    if len(obj.value) != _PUBLIC_KEY_LEN:
        raise BindingError(f"Clave publica invalida: {len(obj.value)} bytes")
    from .identity import fingerprint
    return PublicIdentity(public_key_bytes=obj.value, identity_id=fingerprint(obj.value))


def build_proof_object(
    identity: Identity,
    subject: ObjectV1,
    context: bytes,
    proof_id: int,
) -> ObjectV1:
    """
    Firmar `subject` (un Object ya existente, p. ej. IDENTITY_KEY) con
    `identity`, atado a `context` (bytes arbitrarios: challenge,
    session id, o b"" si no se requiere).

    Material firmado = subject.value + context. Ver docs/
    IDENTITY_CRYPTOGRAPHY_DESIGN.md Seccion 3.3 y 4.
    """
    material = subject.value + context
    signature = identity.sign(material)
    value = struct.pack('!B', subject.id) + signature
    return ObjectV1(type=TYPE_IDENTITY_PROOF, id=proof_id, value=value)


def parse_proof_object(proof: ObjectV1) -> tuple:
    """Devuelve (ref_id, signature) desde un Object IDENTITY_PROOF."""
    if proof.type != TYPE_IDENTITY_PROOF:
        raise BindingError(f"Object no es IDENTITY_PROOF (TYPE={proof.type})")
    if len(proof.value) != 1 + _SIGNATURE_LEN:
        raise BindingError(f"IDENTITY_PROOF con longitud invalida: {len(proof.value)} bytes")
    ref_id = struct.unpack('!B', proof.value[0:1])[0]
    signature = proof.value[1:]
    return ref_id, signature


def build_rotation_object(
    old_identity: Identity,
    old_key_object_id: int,
    new_identity: Identity,
    rotation_id: int,
) -> ObjectV1:
    """
    `old_identity` firma la clave publica de `new_identity`,
    referenciando el Object de la clave vieja por su ID local.
    """
    signature = old_identity.sign(new_identity.public_key_bytes)
    value = struct.pack('!B', old_key_object_id) + signature
    return ObjectV1(type=TYPE_IDENTITY_ROTATION, id=rotation_id, value=value)


def parse_rotation_object(rotation: ObjectV1) -> tuple:
    """Devuelve (old_key_ref_id, signature) desde un Object IDENTITY_ROTATION."""
    if rotation.type != TYPE_IDENTITY_ROTATION:
        raise BindingError(f"Object no es IDENTITY_ROTATION (TYPE={rotation.type})")
    if len(rotation.value) != 1 + _SIGNATURE_LEN:
        raise BindingError(f"IDENTITY_ROTATION con longitud invalida: {len(rotation.value)} bytes")
    ref_id = struct.unpack('!B', rotation.value[0:1])[0]
    signature = rotation.value[1:]
    return ref_id, signature
