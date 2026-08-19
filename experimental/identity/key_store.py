"""
IPv7 Identity Engine — persistencia de claves (Fase 5.4, experimental).

Guarda/carga una Identity Ed25519 en disco. Analogo en espiritu a
`src/core/identity.py` (IdentityManager), pero con material
criptografico real en vez de un DID aleatorio de texto.

No modifica src/core/identity.py ni ipv7_mvp/.
"""

import base64
import json
import os

from .identity import Identity


def save(identity: Identity, path: str) -> None:
    """Guardar la clave privada (y el fingerprint) en un archivo JSON."""
    data = {
        "identity_id": identity.identity_id,
        "private_key_b64": base64.b64encode(identity.private_bytes()).decode("ascii"),
    }
    with open(path, "w") as f:
        json.dump(data, f)


def load(path: str) -> Identity:
    """Cargar una Identity desde un archivo JSON previamente guardado."""
    with open(path, "r") as f:
        data = json.load(f)
    private_bytes = base64.b64decode(data["private_key_b64"])
    return Identity.from_private_bytes(private_bytes)


def get_or_create(path: str) -> Identity:
    """
    Cargar la identidad persistida en `path`, o generar una nueva y
    guardarla si no existe (o si el archivo esta corrupto).
    """
    if os.path.exists(path):
        try:
            return load(path)
        except (json.JSONDecodeError, KeyError, ValueError):
            pass  # Archivo corrupto: regenerar.

    identity = Identity.generate()
    save(identity, path)
    return identity
