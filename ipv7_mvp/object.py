"""
IPv7 Object - IDTLV básico
FASE 7: IDTLV simple
"""

import struct
from dataclasses import dataclass


@dataclass
class IDTLVObject:
    """
    Objeto IDTLV simple
    TYPE | LENGTH | ID | VALUE
    """
    type: int      # 1 byte (hasta 256 tipos estructurales)
    id: int        # ID local dentro del contenedor
    value: bytes   # Valor del objeto
    
    FORMAT = '!BHI'  # type (1B), length (2H), id (I)
    HEADER_SIZE = struct.calcsize(FORMAT)
    
    def encode(self) -> bytes:
        """Codificar objeto a bytes"""
        length = len(self.value)
        return struct.pack(self.FORMAT, self.type, length, self.id) + self.value
    
    @classmethod
    def decode(cls, data: bytes) -> Optional['IDTLVObject']:
        """Decodificar bytes a objeto"""
        if len(data) < cls.HEADER_SIZE:
            return None
        
        type_val, length, obj_id = struct.unpack(cls.FORMAT, data[:cls.HEADER_SIZE])
        
        if len(data) < cls.HEADER_SIZE + length:
            return None
        
        value = data[cls.HEADER_SIZE:cls.HEADER_SIZE + length]
        
        return cls(type=type_val, id=obj_id, value=value)


# Tipos estructurales básicos (Core NO define semántica)
class ObjectType:
    RAW = 0        # Datos crudos
    STRING = 1     # String UTF-8
    INTEGER = 2    # Entero
    FLOAT = 3      # Flotante
    CONTAINER = 4  # Referencia a otro contenedor
    DELTA = 5      # Cambio/delta