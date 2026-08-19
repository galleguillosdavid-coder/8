"""
IPv7 Object Manager
Gestión de objetos como elementos semánticos dentro de contenedores
Un objeto identifica aquello que realmente estamos transportando
"""

from typing import Dict, Optional, List
import struct


class Object:
    """
    Representación de un objeto semántico
    El ID del objeto es un índice local dentro del contenedor
    No es una dirección global, no es un DID
    """
    
    def __init__(self, object_id: int, object_type: str, context: str):
        self.object_id = object_id  # Índice local (14, 15, 16, etc.)
        self.object_type = object_type  # "sensor_temperatura", "imagen", etc.
        self.context = context  # "edificio/2/piso/4", "vehiculo/ABC123", etc.
        self.data: bytes = b''  # Datos codificados (IDTLV)
        self.metadata: Dict = {}
        self.version: int = 1
    
    def set_data(self, data: bytes):
        """Establecer datos del objeto (codificados IDTLV)"""
        self.data = data
    
    def get_data(self) -> bytes:
        """Obtener datos del objeto"""
        return self.data
    
    def to_dict(self) -> Dict:
        """Convertir objeto a diccionario"""
        return {
            'id': self.object_id,
            'type': self.object_type,
            'context': self.context,
            'data': self.data,
            'metadata': self.metadata,
            'version': self.version
        }


class Container:
    """
    Contenedor lógico que agrupa objetos relacionados
    Un contenedor puede tener múltiples objetos
    """
    
    def __init__(self, container_id: str, schema: str = "default"):
        self.container_id = container_id  # "temp_sensors", "video_streams", etc.
        self.schema = schema  # Schema de validación
        self.objects: Dict[int, Object] = {}  # object_id -> Object
        self.object_counter = 0
        self.metadata: Dict = {}
    
    def add_object(self, object_type: str, context: str, data: bytes = None) -> Object:
        """
        Agregar objeto al contenedor
        
        Args:
            object_type: Tipo de objeto
            context: Contexto del objeto
            data: Datos codificados IDTLV (opcional)
            
        Returns:
            Object creado
        """
        object_id = self.object_counter
        self.object_counter += 1
        
        obj = Object(object_id, object_type, context)
        if data:
            obj.set_data(data)
        
        self.objects[object_id] = obj
        return obj
    
    def get_object(self, object_id: int) -> Optional[Object]:
        """Obtener objeto por ID local"""
        return self.objects.get(object_id)
    
    def remove_object(self, object_id: int) -> bool:
        """Eliminar objeto del contenedor"""
        if object_id in self.objects:
            del self.objects[object_id]
            return True
        return False
    
    def get_objects_by_type(self, object_type: str) -> List[Object]:
        """Obtener todos los objetos de un tipo específico"""
        return [obj for obj in self.objects.values() if obj.object_type == object_type]
    
    def get_objects_by_context(self, context: str) -> List[Object]:
        """Obtener todos los objetos de un contexto específico"""
        return [obj for obj in self.objects.values() if obj.context == context]


class ObjectManager:
    """
    Gestor de objetos del Core
    El Core maneja la estructura de objetos, no su semántica
    """
    
    def __init__(self):
        self.containers: Dict[str, Container] = {}  # container_id -> Container
    
    def create_container(self, container_id: str, schema: str = "default") -> Container:
        """
        Crear nuevo contenedor
        
        Args:
            container_id: ID del contenedor
            schema: Schema de validación
            
        Returns:
            Container creado
        """
        container = Container(container_id, schema)
        self.containers[container_id] = container
        return container
    
    def get_container(self, container_id: str) -> Optional[Container]:
        """Obtener contenedor por ID"""
        return self.containers.get(container_id)
    
    def remove_container(self, container_id: str) -> bool:
        """Eliminar contenedor"""
        if container_id in self.containers:
            del self.containers[container_id]
            return True
        return False
    
    def route_to_object(self, container_id: str, object_id: int) -> Optional[Object]:
        """
        Enrutamiento hacia un objeto específico
        El Core no necesita saber qué es el objeto, solo enruta
        """
        container = self.get_container(container_id)
        if container:
            return container.get_object(object_id)
        return None
    
    def find_objects_by_semantic(self, object_type: str, context: str = None) -> List[Object]:
        """
        Búsqueda semántica de objetos
        El Core puede buscar por tipo y contexto sin entender semántica
        """
        results = []
        for container in self.containers.values():
            matching_objects = container.get_objects_by_type(object_type)
            if context:
                matching_objects = [obj for obj in matching_objects if obj.context == context]
            results.extend(matching_objects)
        return results