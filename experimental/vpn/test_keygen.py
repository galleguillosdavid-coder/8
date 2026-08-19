"""
Tests de experimental/vpn/keygen.py.

Verifica que las claves generadas tienen el formato correcto para un
archivo .conf de WireGuard (32 bytes, base64), y que dos pares de
claves distintos derivan el MISMO secreto compartido via X25519 ECDH
(sanity check de que las claves son X25519 validas y utilizables por
WireGuard, sin reimplementar el handshake de WireGuard).
"""

import base64
import unittest

from .keygen import generate_keypair, public_from_private_b64, shared_secret


class KeygenFormatTests(unittest.TestCase):
    def test_key_lengths(self):
        kp = generate_keypair()
        self.assertEqual(len(kp.private_bytes), 32)
        self.assertEqual(len(kp.public_bytes), 32)

    def test_base64_roundtrip(self):
        kp = generate_keypair()
        self.assertEqual(base64.b64decode(kp.private_b64), kp.private_bytes)
        self.assertEqual(base64.b64decode(kp.public_b64), kp.public_bytes)

    def test_two_keypairs_are_different(self):
        a = generate_keypair()
        b = generate_keypair()
        self.assertNotEqual(a.private_b64, b.private_b64)
        self.assertNotEqual(a.public_b64, b.public_b64)

    def test_public_from_private_matches_generated_public(self):
        kp = generate_keypair()
        derived_public = public_from_private_b64(kp.private_b64)
        self.assertEqual(derived_public, kp.public_b64)


class DiffieHellmanSanityTests(unittest.TestCase):
    def test_shared_secret_matches_both_directions(self):
        """
        A y B calculan el mismo secreto ECDH a partir de su propia
        privada y la publica del otro. Esto confirma que las claves
        generadas son X25519 utilizables, no que reemplaza el
        handshake real de WireGuard (Noise), que sigue siendo
        responsabilidad exclusiva de la app de WireGuard.
        """
        a = generate_keypair()
        b = generate_keypair()

        secret_from_a = shared_secret(a.private_b64, b.public_b64)
        secret_from_b = shared_secret(b.private_b64, a.public_b64)

        self.assertEqual(secret_from_a, secret_from_b)
        self.assertEqual(len(secret_from_a), 32)

    def test_different_peers_produce_different_secrets(self):
        a = generate_keypair()
        b = generate_keypair()
        c = generate_keypair()

        secret_ab = shared_secret(a.private_b64, b.public_b64)
        secret_ac = shared_secret(a.private_b64, c.public_b64)

        self.assertNotEqual(secret_ab, secret_ac)


if __name__ == "__main__":
    unittest.main()
