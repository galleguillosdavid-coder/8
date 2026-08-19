"""
IPv7 Container / Object wire format — V1 experimental

Formato congelado (Fase 4.5):

Container Header (5 bytes, big endian)
    VERSION        1 byte  (0x01)
    FLAGS          1 byte  (0x00 reservado)
    OBJECT_COUNT   1 byte  (0..255)
    PAYLOAD_LENGTH 2 bytes (0..65535)

Object Header (4 bytes, big endian)
    TYPE           1 byte  (0 reservado, 1..254 disponibles, 255 reservado)
    ID             1 byte  (0..254 validos, 255 reservado)
    LENGTH         2 bytes (0..65535)

Value: 0..65535 bytes opacos para el Core.

Este modulo no interpreta VALUE.
"""

import struct
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class ContainerError(Exception):
    """Error estructural de un Container u Object."""
    pass


@dataclass(frozen=True)
class ObjectV1:
    """
    Object V1 estructural.
    El Core no interpreta `value`.
    """
    type: int
    id: int
    value: bytes

    HEADER_SIZE = 4
    TYPE_FORMAT = '!B'      # 1 byte big endian
    ID_FORMAT = '!B'        # 1 byte big endian
    LENGTH_FORMAT = '!H'    # 2 bytes big endian

    def encode(self) -> bytes:
        """Codificar a bytes (header + value)."""
        if not (1 <= self.type <= 254):
            raise ContainerError(f"TYPE reservado o invalido: {self.type}")
        if not (0 <= self.id <= 254):
            raise ContainerError(f"ID reservado o invalido: {self.id}")
        length = len(self.value)
        if not (0 <= length <= 65535):
            raise ContainerError(f"VALUE demasiado grande: {length}")
        return (
            struct.pack(self.TYPE_FORMAT, self.type) +
            struct.pack(self.ID_FORMAT, self.id) +
            struct.pack(self.LENGTH_FORMAT, length) +
            self.value
        )

    @classmethod
    def decode(cls, data: bytes, offset: int) -> Tuple['ObjectV1', int]:
        """
        Decodificar un Object desde `data` empezando en `offset`.
        Devuelve (ObjectV1, siguiente_offset).
        """
        if offset + cls.HEADER_SIZE > len(data):
            raise ContainerError("Object header truncado")

        obj_type = struct.unpack(cls.TYPE_FORMAT, data[offset:offset + 1])[0]
        offset += 1
        obj_id = struct.unpack(cls.ID_FORMAT, data[offset:offset + 1])[0]
        offset += 1
        length = struct.unpack(cls.LENGTH_FORMAT, data[offset:offset + 2])[0]
        offset += 2

        if obj_type == 0 or obj_type == 255:
            raise ContainerError(f"TYPE reservado: {obj_type}")
        if obj_id == 255:
            raise ContainerError(f"ID reservado: {obj_id}")

        if offset + length > len(data):
            raise ContainerError(f"VALUE truncado: se requieren {length} bytes desde {offset}")

        value = data[offset:offset + length]
        offset += length
        return cls(type=obj_type, id=obj_id, value=value), offset


@dataclass(frozen=True)
class ContainerV1:
    """
    Container V1 estructural.
    No conoce la semantica de los Objects.
    """
    version: int = 1
    flags: int = 0
    objects: List[ObjectV1] = field(default_factory=list)

    HEADER_SIZE = 5
    VERSION_FORMAT = '!B'
    FLAGS_FORMAT = '!B'
    OBJECT_COUNT_FORMAT = '!B'
    PAYLOAD_LENGTH_FORMAT = '!H'

    @property
    def object_count(self) -> int:
        return len(self.objects)

    @property
    def payload_length(self) -> int:
        return sum(obj.HEADER_SIZE + len(obj.value) for obj in self.objects)

    def encode(self) -> bytes:
        """Codificar todo el Container a bytes."""
        if self.version != 1:
            raise ContainerError(f"VERSION no soportada: {self.version}")
        if self.flags != 0:
            raise ContainerError(f"FLAGS no soportados: {self.flags}")

        payload = b''.join(obj.encode() for obj in self.objects)
        count = self.object_count
        length = self.payload_length

        if count > 255:
            raise ContainerError(f"OBJECT_COUNT excede limite V1: {count}")
        if length > 65535:
            raise ContainerError(f"PAYLOAD_LENGTH excede limite V1: {length}")

        return (
            struct.pack(self.VERSION_FORMAT, self.version) +
            struct.pack(self.FLAGS_FORMAT, self.flags) +
            struct.pack(self.OBJECT_COUNT_FORMAT, count) +
            struct.pack(self.PAYLOAD_LENGTH_FORMAT, length) +
            payload
        )

    @classmethod
    def decode(cls, data: bytes) -> 'ContainerV1':
        """
        Decodificar bytes a ContainerV1 con validacion estructural estricta.
        No interpreta VALUE.
        """
        if len(data) < cls.HEADER_SIZE:
            raise ContainerError("Container header truncado")

        version = struct.unpack(cls.VERSION_FORMAT, data[0:1])[0]
        flags = struct.unpack(cls.FLAGS_FORMAT, data[1:2])[0]
        count = struct.unpack(cls.OBJECT_COUNT_FORMAT, data[2:3])[0]
        payload_length = struct.unpack(cls.PAYLOAD_LENGTH_FORMAT, data[3:5])[0]

        if version != 1:
            raise ContainerError(f"VERSION desconocida: {version}")
        if flags != 0:
            raise ContainerError(f"FLAGS no soportados: {flags}")

        if len(data) != cls.HEADER_SIZE + payload_length:
            raise ContainerError(
                f"Tamanio inconsistente: data={len(data)}, "
                f"header+payload={cls.HEADER_SIZE + payload_length}"
            )

        objects: List[ObjectV1] = []
        offset = cls.HEADER_SIZE
        for _ in range(count):
            obj, offset = ObjectV1.decode(data, offset)
            objects.append(obj)

        if offset != len(data):
            raise ContainerError(
                f"PAYLOAD_LENGTH inconsistente con objetos parseados: "
                f"offset={offset}, total={len(data)}"
            )

        return cls(version=version, flags=flags, objects=objects)


def decode_object_only(data: bytes) -> Optional[ObjectV1]:
    """
    Decodifica un Object aislado (sin Container).
    Util para tests de unidad.
    """
    try:
        obj, _ = ObjectV1.decode(data, 0)
        return obj
    except ContainerError:
        return None
