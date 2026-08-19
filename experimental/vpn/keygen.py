"""
IPv7 — WireGuard-compatible keygen (experimental).

WireGuard usa pares de clave X25519 (Curve25519) codificados en base64.
Este modulo genera esas claves con `cryptography` (ya usada en
src/core/network.py y en experimental/identity/) sin necesitar el
binario `wg.exe` ni WireGuard instalado. Las claves resultantes son
compatibles con el formato esperado por `wireguard.exe /installtunnelservice`.

No depende de nada de ipv7_mvp ni de experimental/identity — es un
modulo aislado.
"""

import base64
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


@dataclass(frozen=True)
class WgKeyPair:
    """Par de claves WireGuard, en bytes raw (32B) y en base64 (formato .conf)."""
    private_bytes: bytes
    public_bytes: bytes

    @property
    def private_b64(self) -> str:
        return base64.b64encode(self.private_bytes).decode("ascii")

    @property
    def public_b64(self) -> str:
        return base64.b64encode(self.public_bytes).decode("ascii")


def generate_keypair() -> WgKeyPair:
    """Generar un nuevo par de claves X25519 compatible con WireGuard."""
    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return WgKeyPair(private_bytes=private_bytes, public_bytes=public_bytes)


def public_from_private_b64(private_b64: str) -> str:
    """Derivar la clave publica (base64) a partir de una privada (base64)."""
    private_bytes = base64.b64decode(private_b64)
    private_key = X25519PrivateKey.from_private_bytes(private_bytes)
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(public_bytes).decode("ascii")


def shared_secret(private_b64: str, peer_public_b64: str) -> bytes:
    """
    Calcular el secreto ECDH X25519 entre una clave privada propia y una
    clave publica ajena. Sirve como prueba de sanidad de que las claves
    generadas son X25519 validas y coinciden en ambos extremos; WireGuard
    hace su propio calculo equivalente internamente durante el handshake
    Noise, este modulo no lo reemplaza ni lo reimplementa.
    """
    private_key = X25519PrivateKey.from_private_bytes(base64.b64decode(private_b64))
    peer_public_key = X25519PublicKey.from_public_bytes(base64.b64decode(peer_public_b64))
    return private_key.exchange(peer_public_key)
