"""
IPv7 — Transporte con integridad SHA-256 (experimental).

Envuelve un ContainerV1 codificado y agrega un checksum de 32 bytes.
El hash NO cubre su propio campo.
"""

import hashlib
import hmac

from ..container_v1 import ContainerError


CHECKSUM_SIZE = 32


class PacketV1:
    @staticmethod
    def pack(container_bytes: bytes) -> bytes:
        """Agrega SHA-256 delante del payload (appended)."""
        checksum = hashlib.sha256(container_bytes).digest()
        return container_bytes + checksum

    @staticmethod
    def unpack(data: bytes) -> bytes:
        """Verifica y devuelve los bytes del Container."""
        if len(data) < CHECKSUM_SIZE:
            raise ContainerError("Packet demasiado corto")
        container = data[:-CHECKSUM_SIZE]
        received = data[-CHECKSUM_SIZE:]
        expected = hashlib.sha256(container).digest()
        if not hmac.compare_digest(received, expected):
            raise ContainerError("SHA-256 no coincide")
        return container
