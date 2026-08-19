"""
IPv7 — Transporte con integridad SHA-256 y firma Ed25519 (experimental).

Envuelve un ContainerV1 codificado y agrega:
  - una firma Ed25519 de 64 bytes (opcional pero activa por defecto)
  - un checksum SHA-256 de 32 bytes sobre Container + firma

El hash NO cubre su propio campo.
"""

import hashlib
import hmac

from ..container_v1 import ContainerError


CHECKSUM_SIZE = 32
SIGNATURE_SIZE = 64


class PacketV1:
    @staticmethod
    def pack(container_bytes: bytes, signature: bytes = b"") -> bytes:
        """Agrega firma y SHA-256 delante del payload."""
        if len(signature) != SIGNATURE_SIZE and signature:
            raise ContainerError(f"Firma debe tener {SIGNATURE_SIZE} bytes")
        if len(signature) == 0:
            signature = b"\x00" * SIGNATURE_SIZE
        signed = container_bytes + signature
        checksum = hashlib.sha256(signed).digest()
        return signed + checksum

    @staticmethod
    def unpack(data: bytes):
        """Verifica y devuelve (container_bytes, signature)."""
        if len(data) < CHECKSUM_SIZE + SIGNATURE_SIZE:
            raise ContainerError("Packet demasiado corto")
        checksum = data[-CHECKSUM_SIZE:]
        signed = data[:-CHECKSUM_SIZE]
        expected = hashlib.sha256(signed).digest()
        if not hmac.compare_digest(received := checksum, expected):
            raise ContainerError("SHA-256 no coincide")
        container = signed[:-SIGNATURE_SIZE]
        signature = signed[-SIGNATURE_SIZE:]
        return container, signature
