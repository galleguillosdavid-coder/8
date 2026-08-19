"""
Fase 5.4 — Identity Engine tests (experimental).

Verifica:
- generacion/persistencia de identidad (Ed25519, Fase 5.3)
- firma y verificacion exitosa
- verificacion falla con contexto distinto (replay entre contextos)
- verificacion falla con Object manipulado
- ID duplicado -> referencia ambigua detectada por el Profile (I-17),
  el Core (ContainerV1) sigue aceptando el Container sin error
- relay ciego real: A firma, B no conoce ningun TYPE de Identity y
  reenvia bytes intactos, C verifica con exito
- rotacion de identidad

No modifica container_v1.py ni ipv7_mvp/.
"""

import os
import tempfile
import unittest

from ..container_v1 import ContainerV1, ObjectV1
from .identity import Identity
from . import key_store
from .binding import (
    TYPE_IDENTITY_KEY,
    identity_key_object,
    build_proof_object,
    build_rotation_object,
)
from .verification import verify_identity_proof, verify_rotation, VerificationError


class IdentityKeyGenerationTests(unittest.TestCase):
    def test_generate_produces_32_byte_key(self):
        identity = Identity.generate()
        self.assertEqual(len(identity.public_key_bytes), 32)
        self.assertEqual(len(identity.identity_id), 16)

    def test_persistence_roundtrip(self):
        identity = Identity.generate()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "id.json")
            key_store.save(identity, path)
            loaded = key_store.load(path)
            self.assertEqual(loaded.public_key_bytes, identity.public_key_bytes)
            self.assertEqual(loaded.identity_id, identity.identity_id)

    def test_get_or_create_generates_once(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "id.json")
            first = key_store.get_or_create(path)
            second = key_store.get_or_create(path)
            self.assertEqual(first.public_key_bytes, second.public_key_bytes)

    def test_get_or_create_regenerates_on_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "id.json")
            with open(path, "w") as f:
                f.write("not json{{{")
            identity = key_store.get_or_create(path)
            self.assertEqual(len(identity.public_key_bytes), 32)


class IdentityProofTests(unittest.TestCase):
    def _build_signed_container(self, context: bytes = b""):
        identity = Identity.generate()
        key_obj = identity_key_object(identity, obj_id=1)
        proof_obj = build_proof_object(identity, key_obj, context=context, proof_id=2)
        container = ContainerV1(objects=[key_obj, proof_obj])
        return identity, container, key_obj, proof_obj

    def test_valid_proof_verifies(self):
        _, container, _, proof_obj = self._build_signed_container(context=b"session-42")
        self.assertTrue(verify_identity_proof(container, proof_obj, context=b"session-42"))

    def test_proof_fails_with_wrong_context(self):
        """El mismo Proof no es valido bajo un contexto distinto (anti cut-and-paste)."""
        _, container, _, proof_obj = self._build_signed_container(context=b"session-42")
        self.assertFalse(verify_identity_proof(container, proof_obj, context=b"session-99"))

    def test_proof_fails_if_subject_tampered(self):
        identity, container, key_obj, proof_obj = self._build_signed_container(context=b"ctx")
        tampered_key = ObjectV1(type=TYPE_IDENTITY_KEY, id=key_obj.id, value=b"\x00" * 32)
        tampered_container = ContainerV1(objects=[tampered_key, proof_obj])
        self.assertFalse(verify_identity_proof(tampered_container, proof_obj, context=b"ctx"))

    def test_proof_fails_with_wrong_identity(self):
        """Una firma de otra identidad sobre el mismo subject no debe verificar."""
        identity_a = Identity.generate()
        identity_b = Identity.generate()
        key_obj = identity_key_object(identity_a, obj_id=1)
        # B firma el subject de A: no deberia verificar contra la clave de A.
        forged_proof = build_proof_object(identity_b, key_obj, context=b"", proof_id=2)
        container = ContainerV1(objects=[key_obj, forged_proof])
        self.assertFalse(verify_identity_proof(container, forged_proof, context=b""))

    def test_roundtrip_through_wire_bytes(self):
        """La Proof sobrevive encode/decode del Container (Core V1) intacta."""
        _, container, _, proof_obj = self._build_signed_container(context=b"wire")
        raw = container.encode()
        decoded = ContainerV1.decode(raw)
        decoded_proof = next(o for o in decoded.objects if o.id == proof_obj.id)
        self.assertTrue(verify_identity_proof(decoded, decoded_proof, context=b"wire"))


class DuplicateIdAmbiguityTests(unittest.TestCase):
    """Caso P de IDENTITY_FIRE_TEST.md, ahora con criptografia real."""

    def test_core_accepts_duplicate_id_container(self):
        """El Core (ContainerV1) no rechaza IDs duplicados."""
        identity = Identity.generate()
        key_a = ObjectV1(type=TYPE_IDENTITY_KEY, id=7, value=identity.public_key_bytes)
        key_b = ObjectV1(type=TYPE_IDENTITY_KEY, id=7, value=b"\x11" * 32)
        container = ContainerV1(objects=[key_a, key_b])
        raw = container.encode()
        decoded = ContainerV1.decode(raw)  # no debe lanzar ContainerError
        self.assertEqual(len(decoded.objects), 2)

    def test_profile_rejects_ambiguous_reference(self):
        """El Profile (verification.py) SI detecta la ambiguedad y la rechaza (I-17)."""
        identity = Identity.generate()
        key_a = ObjectV1(type=TYPE_IDENTITY_KEY, id=7, value=identity.public_key_bytes)
        key_b = ObjectV1(type=TYPE_IDENTITY_KEY, id=7, value=b"\x11" * 32)
        proof = build_proof_object(identity, key_a, context=b"", proof_id=9)
        container = ContainerV1(objects=[key_a, key_b, proof])

        with self.assertRaises(VerificationError):
            verify_identity_proof(container, proof, context=b"")


class IdentityBlindRelayTests(unittest.TestCase):
    """
    Prueba definitiva: A firma, B no conoce ningun TYPE de identidad y
    reenvia byte-a-byte, C decodifica y verifica con exito.
    """

    def test_relay_blind_preserves_verifiable_proof(self):
        identity = Identity.generate()
        key_obj = identity_key_object(identity, obj_id=1)
        proof_obj = build_proof_object(identity, key_obj, context=b"A-to-C", proof_id=2)
        from_a = ContainerV1(objects=[key_obj, proof_obj]).encode()

        # B: no conoce IDENTITY_KEY ni IDENTITY_PROOF.
        at_b = ContainerV1.decode(from_a)
        known_to_b = set()
        self.assertEqual(len([o for o in at_b.objects if o.type in known_to_b]), 0)

        # B reenvia sin interpretar VALUE.
        to_c = at_b.encode()
        self.assertEqual(to_c, from_a)

        # C recibe exactamente lo que A produjo y SI puede verificar.
        at_c = ContainerV1.decode(to_c)
        proof_at_c = next(o for o in at_c.objects if o.id == 2)
        self.assertTrue(verify_identity_proof(at_c, proof_at_c, context=b"A-to-C"))


class IdentityRotationTests(unittest.TestCase):
    def test_rotation_verifies_against_old_key(self):
        old_identity = Identity.generate()
        new_identity = Identity.generate()

        old_key_obj = identity_key_object(old_identity, obj_id=1)
        new_key_obj = identity_key_object(new_identity, obj_id=2)
        rotation_obj = build_rotation_object(
            old_identity, old_key_object_id=1, new_identity=new_identity, rotation_id=3
        )

        container = ContainerV1(objects=[old_key_obj, new_key_obj, rotation_obj])
        raw = container.encode()
        decoded = ContainerV1.decode(raw)

        decoded_rotation = next(o for o in decoded.objects if o.id == 3)
        decoded_new_key = next(o for o in decoded.objects if o.id == 2)
        self.assertTrue(verify_rotation(decoded, decoded_rotation, decoded_new_key))

    def test_rotation_fails_if_new_key_tampered(self):
        old_identity = Identity.generate()
        new_identity = Identity.generate()
        attacker_identity = Identity.generate()

        old_key_obj = identity_key_object(old_identity, obj_id=1)
        rotation_obj = build_rotation_object(
            old_identity, old_key_object_id=1, new_identity=new_identity, rotation_id=3
        )
        # Un atacante intenta sustituir la clave nueva declarada.
        forged_new_key_obj = identity_key_object(attacker_identity, obj_id=2)

        container = ContainerV1(objects=[old_key_obj, forged_new_key_obj, rotation_obj])
        self.assertFalse(verify_rotation(container, rotation_obj, forged_new_key_obj))


if __name__ == "__main__":
    unittest.main()
