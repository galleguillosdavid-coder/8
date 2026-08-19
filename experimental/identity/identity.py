"""
IPv7 Identity Engine — Fase 5.4 (experimental).

Generacion y representacion de una identidad Ed25519 (decision de
Fase 5.3, ver docs/IDENTITY_CRYPTO_DECISION.md).

Este modulo NO conoce Container/Object. Solo sabe de claves, huellas
(fingerprint) e identificadores. La integracion con Container/Object
vive en `binding.py` y `verification.py`.

No modifica experimental/container_v1.py.
"""

import hashlib
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


class IdentityError(Exception):
    """Error de dominio de Identity (no confundir con ContainerError)."""
    pass


def fingerprint(public_key_bytes: bytes) -> str:
    """
    Huella corta y estable de una clave publica (Key ID), usando
    SHA-256 (Fase 5.3: se descarta BLAKE3 por no estar disponible en
    este entorno). Devuelve hex de 16 caracteres (8 bytes) — suficiente
    para distinguir identidades en un entorno experimental, no es un
    compromiso de seguridad final.
    """
    digest = hashlib.sha256(public_key_bytes).hexdigest()
    return digest[:16]


@dataclass(frozen=True)
class Identity:
    """
    Una identidad Ed25519: clave privada (si se posee), clave publica
    en formato raw (32 bytes, "Raw Public Key") y su fingerprint.
    """
    private_key: Ed25519PrivateKey
    public_key_bytes: bytes
    identity_id: str  # fingerprint de la clave publica

    @classmethod
    def generate(cls) -> 'Identity':
        """Generar una nueva identidad Ed25519."""
        private_key = Ed25519PrivateKey.generate()
        public_key_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return cls(
            private_key=private_key,
            public_key_bytes=public_key_bytes,
            identity_id=fingerprint(public_key_bytes),
        )

    @classmethod
    def from_private_bytes(cls, private_bytes: bytes) -> 'Identity':
        """Reconstruir una identidad a partir de 32 bytes de clave privada raw."""
        if len(private_bytes) != 32:
            raise IdentityError(f"Clave privada Ed25519 invalida: {len(private_bytes)} bytes")
        private_key = Ed25519PrivateKey.from_private_bytes(private_bytes)
        public_key_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return cls(
            private_key=private_key,
            public_key_bytes=public_key_bytes,
            identity_id=fingerprint(public_key_bytes),
        )

    def private_bytes(self) -> bytes:
        """Exportar la clave privada como 32 bytes raw (para persistencia)."""
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def sign(self, material: bytes) -> bytes:
        """Firmar bytes arbitrarios. `material` es opaco para este modulo."""
        return self.private_key.sign(material)

    def public_identity(self) -> 'PublicIdentity':
        """Vista publica de esta identidad, para compartir/transportar."""
        return PublicIdentity(
            public_key_bytes=self.public_key_bytes,
            identity_id=self.identity_id,
        )


@dataclass(frozen=True)
class PublicIdentity:
    """Representacion publica de una identidad: solo lo que se transporta."""
    public_key_bytes: bytes
    identity_id: str

    def verify(self, material: bytes, signature: bytes) -> bool:
        """
        Verificar una firma sobre `material`. Devuelve False en vez de
        propagar la excepcion de la libreria criptografica, para que
        el llamador (Profile) decida como tratar una firma invalida
        sin necesitar conocer la excepcion especifica de `cryptography`.
        """
        try:
            public_key = Ed25519PublicKey.from_public_bytes(self.public_key_bytes)
            public_key.verify(signature, material)
            return True
        except Exception:
            return False
