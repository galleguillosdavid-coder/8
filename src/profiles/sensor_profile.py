"""
IPv7 Sensor Profile
Profile define qué significa un canal QUERY para sensores
El Profile aporta semántica, el Core transporta estructura
"""

from typing import Dict, Any, Optional
import struct


class SensorProfile:
    """
    Profile para sensores IoT
    Define semántica de canales QUERY, TELEMETRY, etc. para sensores
    """
    
    def __init__(self):
        self.profile_name = "sensor_profile"
        self.version = "1.0"
        self.capabilities = {
            "telemetry": True,
            "query": True,
            "write": False,
            "emergency": True
        }
        
        # Definición de tipos de sensores soportados
        self.sensor_types = {
            "temperature": {"unit": "celsius", "precision": 0.1, "range": (-40, 100)},
            "humidity": {"unit": "percent", "precision": 0.1, "range": (0, 100)},
            "pressure": {"unit": "hpa", "precision": 1, "range": (800, 1200)},
            "battery": {"unit": "percent", "precision": 1, "range": (0, 100)},
            "light": {"unit": "lux", "precision": 10, "range": (0, 100000)}
        }
    
    def handle_query(self, object_id: int, context: str) -> Dict[str, Any]:
        """
        El Profile sabe qué es una consulta de temperatura
        El Core solo sabe que existe un canal QUERY
        """
        if context.startswith("edificio"):
            return self._query_building_sensor(object_id, context)
        elif context.startswith("vehiculo"):
            return self._query_vehicle_sensor(object_id, context)
        elif context.startswith("industrial"):
            return self._query_industrial_sensor(object_id, context)
        else:
            return {"error": "contexto_no_soportado"}
    
    def _query_building_sensor(self, object_id: int, context: str) -> Dict[str, Any]:
        """Consulta específica para sensores de edificio"""
        # Extraer información del contexto: edificio/2/piso/4
        parts = context.split("/")
        edificio = parts[1] if len(parts) > 1 else "desconocido"
        piso = parts[3] if len(parts) > 3 else "desconocido"
        
        return {
            "context_type": "building",
            "edificio": edificio,
            "piso": piso,
            "sensor_id": object_id,
            "data": self._get_sensor_data(object_id, context)
        }
    
    def _query_vehicle_sensor(self, object_id: int, context: str) -> Dict[str, Any]:
        """Consulta específica para sensores de vehículo"""
        parts = context.split("/")
        vehiculo = parts[1] if len(parts) > 1 else "desconocido"
        
        return {
            "context_type": "vehicle",
            "vehiculo": vehiculo,
            "sensor_id": object_id,
            "data": self._get_sensor_data(object_id, context)
        }
    
    def _query_industrial_sensor(self, object_id: int, context: str) -> Dict[str, Any]:
        """Consulta específica para sensores industriales"""
        parts = context.split("/")
        planta = parts[1] if len(parts) > 1 else "desconocido"
        maquina = parts[3] if len(parts) > 3 else "desconocido"
        
        return {
            "context_type": "industrial",
            "planta": planta,
            "maquina": maquina,
            "sensor_id": object_id,
            "data": self._get_sensor_data(object_id, context)
        }
    
    def _get_sensor_data(self, object_id: int, context: str) -> Dict[str, Any]:
        """Obtener datos simulados del sensor"""
        # En implementación real, esto leería del hardware
        import random
        
        # Simular diferentes tipos de sensores basado en object_id
        sensor_type_map = {
            14: "temperature",
            15: "humidity", 
            16: "pressure",
            17: "battery"
        }
        
        sensor_type = sensor_type_map.get(object_id, "temperature")
        sensor_spec = self.sensor_types.get(sensor_type, self.sensor_types["temperature"])
        
        min_val, max_val = sensor_spec["range"]
        value = random.uniform(min_val, max_val)
        
        return {
            "type": sensor_type,
            "value": round(value, sensor_spec["precision"]),
            "unit": sensor_spec["unit"],
            "timestamp": self._get_timestamp()
        }
    
    def encode_telemetry(self, sensor_data: Dict[str, Any]) -> bytes:
        """
        Codificar datos de sensor usando IDTLV
        El Profile sabe cómo codificar datos de sensor específicos
        """
        # Implementación simplificada de IDTLV
        # En implementación real, usaría la librería IDTLV completa
        
        encoded = bytearray()
        
        # Type (1 byte)
        sensor_type = sensor_data.get("type", "temperature")
        type_map = {"temperature": 1, "humidity": 2, "pressure": 3, "battery": 4}
        encoded.append(type_map.get(sensor_type, 1))
        
        # Value (4 bytes float)
        value = sensor_data.get("value", 0.0)
        encoded.extend(struct.pack('!f', value))
        
        # Timestamp (8 bytes)
        timestamp = sensor_data.get("timestamp", 0)
        encoded.extend(struct.pack('!Q', timestamp))
        
        return bytes(encoded)
    
    def decode_telemetry(self, data: bytes) -> Dict[str, Any]:
        """
        Decodificar datos de sensor usando IDTLV
        El Profile sabe cómo decodificar datos de sensor específicos
        """
        if len(data) < 13:  # 1 + 4 + 8 bytes mínimos
            return {"error": "datos_insuficientes"}
        
        decoded = {}
        
        # Type (1 byte)
        type_map_inv = {1: "temperature", 2: "humidity", 3: "pressure", 4: "battery"}
        decoded["type"] = type_map_inv.get(data[0], "unknown")
        
        # Value (4 bytes float)
        decoded["value"] = struct.unpack('!f', data[1:5])[0]
        
        # Timestamp (8 bytes)
        decoded["timestamp"] = struct.unpack('!Q', data[5:13])[0]
        
        return decoded
    
    def _get_timestamp(self) -> int:
        """Obtener timestamp actual"""
        import time
        return int(time.time())
    
    def validate_sensor_data(self, sensor_data: Dict[str, Any]) -> bool:
        """
        Validar datos de sensor según su tipo
        El Profile conoce las reglas de validación específicas
        """
        sensor_type = sensor_data.get("type")
        value = sensor_data.get("value")
        
        if sensor_type not in self.sensor_types:
            return False
        
        spec = self.sensor_types[sensor_type]
        min_val, max_val = spec["range"]
        
        return min_val <= value <= max_val
    
    def get_emergency_protocol(self, context: str) -> Dict[str, Any]:
        """
        Definir protocolo de emergencia para sensores
        El Profile sabe qué constituye una emergencia para diferentes contextos
        """
        if context.startswith("edificio"):
            return {
                "emergency_type": "building_fire",
                "thresholds": {
                    "temperature": 80,  # °C
                    "smoke": "high"
                },
                "actions": ["activate_alarms", "notify_authorities", "unlock_exits"]
            }
        elif context.startswith("industrial"):
            return {
                "emergency_type": "industrial_accident",
                "thresholds": {
                    "pressure": 900,  # hPa
                    "temperature": 150  # °C
                },
                "actions": ["shutdown_machinery", "evacuate_area", "notify_safety"]
            }
        else:
            return {
                "emergency_type": "general",
                "actions": ["log_incident", "notify_admin"]
            }