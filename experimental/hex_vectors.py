"""
Vectores hexadecimales V1 para tests de round-trip y parsing.

Los hex strings se generan a partir de las descripciones de los 10 casos
en `docs/CONTAINER_OBJECT_WIREFORM_DESIGN.md` (Seccion 41.4), normalizando
las longitudes (LENGTH y PAYLOAD_LENGTH) para que sean estructuralmente
validas segun la especificacion V1. De este modo todos los vectores son
round-tripables.
"""

from .container_v1 import ContainerV1, ObjectV1


def make_first_contact() -> bytes:
    """Ejemplo 1: First Contact minimo."""
    return ContainerV1(objects=[
        ObjectV1(type=1, id=1, value=b""),
    ]).encode()


def make_node_knowledge_cpu() -> bytes:
    """Ejemplo 2: Node Knowledge (CPU declarado)."""
    return ContainerV1(objects=[
        ObjectV1(type=3, id=1, value=b"cpu:8:declared:declared"),
    ]).encode()


def make_measurement_latency() -> bytes:
    """Ejemplo 3: Measurement (latencia)."""
    return ContainerV1(objects=[
        ObjectV1(type=4, id=1, value=b"latency:4.82:ms:observed"),
    ]).encode()


def make_capability_probe() -> bytes:
    """Ejemplo 4: Capability Probe result."""
    return ContainerV1(objects=[
        ObjectV1(type=5, id=1, value=b"cpu.compute:class-X"),
    ]).encode()


def make_availability() -> bytes:
    """Ejemplo 5: Availability."""
    return ContainerV1(objects=[
        ObjectV1(type=6, id=1, value=b"telemetry:intermittent:18:00-22:00"),
    ]).encode()


def make_evidence() -> bytes:
    """Ejemplo 6: Evidence (referencia local)."""
    return ContainerV1(objects=[
        ObjectV1(type=5, id=1, value=b"ed25519"),
        ObjectV1(type=7, id=2, value=b"ref:01"),
    ]).encode()


def make_non_ipv7_observed() -> bytes:
    """Ejemplo 7: Nodo no-IPv7 observado."""
    return ContainerV1(objects=[
        ObjectV1(type=16, id=1, value=b"IPv4"),
        ObjectV1(type=17, id=2, value=b"8.2:ms"),
    ]).encode()


def make_nested_container() -> bytes:
    """Ejemplo 8: Container anidado."""
    sub = ContainerV1(objects=[
        ObjectV1(type=1, id=0, value=b"inner"),
    ]).encode()
    return ContainerV1(objects=[
        ObjectV1(type=10, id=5, value=sub),
    ]).encode()


def make_large_value() -> bytes:
    """
    Ejemplo 9: VALUE de 65531 bytes, que es el maximo que cabe en un
    Container V1 cuando el payload total es 65535 bytes (4 de header
    de objeto + 65531 de value).
    """
    value = b"\x00" * 65531
    return ContainerV1(objects=[
        ObjectV1(type=1, id=0, value=value),
    ]).encode()


def make_signed_container() -> bytes:
    """Ejemplo 10: Signed Container."""
    data_obj = ObjectV1(type=1, id=0, value=b"some profile data")
    signature_obj = ObjectV1(type=2, id=1, value=b"\xab" * 32)
    return ContainerV1(objects=[data_obj, signature_obj]).encode()


def make_unknown_object() -> bytes:
    """Container con known-unknown-known, para el test de preservacion."""
    return ContainerV1(objects=[
        ObjectV1(type=1, id=0, value=b"known-1"),
        ObjectV1(type=237, id=1, value=b"unknown"),
        ObjectV1(type=2, id=2, value=b"known-2"),
    ]).encode()


def make_mutant_relay() -> bytes:
    """Container mutante: conocido, desconocido, conocido, futuro."""
    return ContainerV1(objects=[
        ObjectV1(type=1, id=0, value=b"known"),
        ObjectV1(type=237, id=1, value=b"desconocido"),
        ObjectV1(type=2, id=2, value=b"evidence"),
        ObjectV1(type=242, id=3, value=b"futuro"),
    ]).encode()


# Vectores de round-trip con nombre y funcion generadora.
HEX_VECTORS = [
    ("first_contact", make_first_contact),
    ("node_knowledge_cpu", make_node_knowledge_cpu),
    ("measurement_latency", make_measurement_latency),
    ("capability_probe", make_capability_probe),
    ("availability", make_availability),
    ("evidence", make_evidence),
    ("non_ipv7_observed", make_non_ipv7_observed),
    ("nested", make_nested_container),
    ("large_value", make_large_value),
    ("signed", make_signed_container),
]
