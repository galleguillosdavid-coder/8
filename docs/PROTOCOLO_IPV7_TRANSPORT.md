# IPv7 Transport Layer Specification
# NOTA: Este documento representa una propuesta anterior. La arquitectura actual es CHANNEL → SESSION → OBJECT.

## ⚠️ ARQUITECTURA ACTUALIZADA

**Este documento describe una propuesta de puertos de 32 bits que ha sido SUPERADA por la arquitectura actual.**

La arquitectura actual de IPv7 NO se basa en puertos globales, sino en:

```
CHANNEL → SESSION → CONTAINER → OBJECT
```

Consulte `ARQUITECTURA_CANAL_SESION_OBJETO.md` para la arquitectura actual.

---

## Propuesta Anterior (Superada)

Esta propuesta originalmente sugería puertos de 32 bits para superar el límite de 65,536 puertos del TCP/IP tradicional. Sin embargo, esta solución mantenía el paradigma antiguo:

```
IP + PORT = SERVICE
```

La arquitectura actual rechaza este paradigma y en su lugar implementa:

```
Identidad → Objeto → Contexto → Sesión
```

### Por qué esta propuesta fue superada:

1. **Mismo paradigma antiguo**: Puertos de 32 bits siguen siendo `IP + PORT = SERVICE`
2. **No resuelve el problema fundamental**: La identidad sigue ligada a la ubicación
3. **Complejidad innecesaria**: Gestión de 4.2 mil millones de puertos no resuelve la semántica
4. **Arquitectura superior**: Canales, sesiones y objetos proporcionan mejor escalabilidad y semántica

### Arquitectura Actual Recomendada

En lugar de puertos de 32 bits, IPv7 ahora implementa:

- **Canales lógicos (subports)**: 0=control, 1=telemetry, 2=query, etc.
- **Sesiones dinámicas**: Comunicación con OPEN/DATA/CLOSE
- **Objetos IDTLV**: TYPE | LENGTH | ID | VALUE con IDs locales
- **Profiles**: Semántica separada del Core

Esta arquitectura sí es digna de llamarse un nuevo internet.


# Implementación Python del protocolo
import struct
import hashlib

class IPv7Transport:
    """Implementación del protocolo de transporte IPv7"""
    
    def __init__(self):
        self.header_size = 64  # 64 bytes cabecera fija
    
    def create_packet(self, source_port: int, dest_port: int, 
                     source_did: str, dest_did: str, 
                     payload: bytes) -> bytes:
        """
        Crear un paquete IPv7 de transporte
        
        Args:
            source_port: Puerto origen (32-bit)
            dest_port: Puerto destino (32-bit)  
            source_did: DID origen
            dest_did: DID destino
            payload: Datos a transmitir
            
        Returns:
            Paquete completo en bytes
        """
        # Validar puertos de 32 bits
        if not (0 <= source_port < 2**32):
            raise ValueError(f"Puerto origen inválido: {source_port}")
        if not (0 <= dest_port < 2**32):
            raise ValueError(f"Puerto destino inválido: {dest_port}")
        
        # Convertir DIDs a bytes fijos (16 bytes cada uno)
        source_did_bytes = self._did_to_bytes(source_did)
        dest_did_bytes = self._did_to_bytes(dest_did)
        
        # Empaquetar cabecera
        header = struct.pack(
            '!BBHIIII16s16sIIHH',
            1,                      # version
            0,                      # flags
            0,                      # reserved
            source_port,            # source_port (32-bit)
            dest_port,              # dest_port (32-bit)
            0,                      # sequence
            0,                      # acknowledgment
            source_did_bytes,       # source_did (16 bytes)
            dest_did_bytes,         # dest_did (16 bytes)
            len(payload),           # length
            0,                      # checksum (calcular después)
            0,                      # extension_type
            0                       # extension_length
        )
        
        # Calcular checksum
        checksum_data = header[:56] + payload  # Excluir campo checksum
        checksum = self._calculate_checksum(checksum_data)
        
        # Reemplazar checksum en cabecera
        header = header[:56] + struct.pack('!I', checksum) + header[60:]
        
        return header + payload
    
    def parse_packet(self, packet: bytes) -> dict:
        """
        Parsear un paquete IPv7 de transporte
        
        Args:
            packet: Paquete recibido en bytes
            
        Returns:
            Diccionario con los campos del paquete
        """
        if len(packet) < self.header_size:
            raise ValueError("Paquete demasiado corto")
        
        # Desempaquetar cabecera
        header_data = struct.unpack(
            '!BBHIIII16s16sIIHH',
            packet[:self.header_size]
        )
        
        parsed = {
            'version': header_data[0],
            'flags': header_data[1],
            'reserved': header_data[2],
            'source_port': header_data[3],
            'dest_port': header_data[4],
            'sequence': header_data[5],
            'acknowledgment': header_data[6],
            'source_did': self._bytes_to_did(header_data[7]),
            'dest_did': self._bytes_to_did(header_data[8]),
            'length': header_data[9],
            'checksum': header_data[10],
            'extension_type': header_data[11],
            'extension_length': header_data[12],
            'payload': packet[self.header_size:]
        }
        
        # Verificar checksum
        if not self._verify_checksum(packet):
            raise ValueError("Checksum inválido")
        
        return parsed
    
    def _did_to_bytes(self, did: str) -> bytes:
        """Convertir DID string a 16 bytes fijos"""
        did_bytes = did.encode('utf-8')[:16]  # Truncar a 16 bytes
        return did_bytes.ljust(16, b'\x00')    # Padding con ceros
    
    def _bytes_to_did(self, did_bytes: bytes) -> str:
        """Convertir 16 bytes a DID string"""
        return did_bytes.rstrip(b'\x00').decode('utf-8')
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Calcular checksum SHA-256 (primeros 4 bytes)"""
        hash_obj = hashlib.sha256(data)
        return int.from_bytes(hash_obj.digest()[:4], byteorder='big')
    
    def _verify_checksum(self, packet: bytes) -> bool:
        """Verificar integridad del paquete"""
        header = packet[:56] + b'\x00\x00\x00\x00' + packet[60:self.header_size]
        payload = packet[self.header_size:]
        checksum_data = header + payload
        calculated = self._calculate_checksum(checksum_data)
        received = struct.unpack('!I', packet[56:60])[0]
        return calculated == received


# Gestión de puertos de 32 bits
class PortManager32:
    """Gestor de puertos IPv7 de 32 bits"""
    
    def __init__(self):
        self.allocated_ports = set()
        self.port_ranges = IPv7TransportHeader.port_ranges()
    
    def allocate_port(self, port_type: str = 'dynamic') -> int:
        """
        Asignar un puerto disponible
        
        Args:
            port_type: 'system', 'user', o 'dynamic'
            
        Returns:
            Puerto asignado (32-bit)
        """
        start, end = self.port_ranges[port_type]
        
        for port in range(start, end):
            if port not in self.allocated_ports:
                self.allocated_ports.add(port)
                return port
        
        raise Exception(f"No hay puertos disponibles en rango {port_type}")
    
    def allocate_specific_port(self, port: int) -> bool:
        """Asignar un puerto específico"""
        if port in self.allocated_ports:
            return False
        
        self.allocated_ports.add(port)
        return True
    
    def release_port(self, port: int):
        """Liberar un puerto"""
        self.allocated_ports.discard(port)
    
    def get_port_info(self, port: int) -> dict:
        """Obtener información sobre un puerto"""
        info = {
            'port': port,
            'allocated': port in self.allocated_ports,
            'range': None,
            'type': None
        }
        
        for range_name, (start, end) in self.port_ranges.items():
            if start <= port < end:
                info['range'] = range_name
                info['type'] = range_name.replace('_reserved', '')
                break
        
        return info


# Ejemplos de uso
if __name__ == "__main__":
    # Crear protocolo de transporte
    transport = IPv7Transport()
    
    # Crear gestor de puertos
    port_manager = PortManager32()
    
    print("=== IPv7 TRANSPORT LAYER ===")
    print(f"Puertos máximos soportados: {transport.header_size:,}")
    print(f"Rango de puertos: 0 - {IPv7TransportHeader.max_ports():,}")
    print()
    
    # Asignar puertos
    print("Asignando puertos:")
    port1 = port_manager.allocate_port('system')
    print(f"  Puerto sistema: {port1}")
    
    port2 = port_manager.allocate_port('user') 
    print(f"  Puerto usuario: {port2}")
    
    port3 = port_manager.allocate_port('dynamic')
    print(f"  Puerto dinámico: {port3}")
    
    # Crear paquete
    print("\nCreando paquete de prueba:")
    packet = transport.create_packet(
        source_port=port1,
        dest_port=port2,
        source_did="did:ipv7:ABCDEFGH",
        dest_did="did:ipv7:12345678",
        payload=b"Hola desde el nuevo internet!"
    )
    print(f"  Tamaño total: {len(packet)} bytes")
    print(f"  Cabecera: {transport.header_size} bytes")
    print(f"  Payload: {len(packet) - transport.header_size} bytes")
    
    # Parsear paquete
    print("\nParseando paquete:")
    parsed = transport.parse_packet(packet)
    print(f"  Puerto origen: {parsed['source_port']}")
    print(f"  Puerto destino: {parsed['dest_port']}")
    print(f"  DID origen: {parsed['source_did']}")
    print(f"  DID destino: {parsed['dest_did']}")
    print(f"  Payload: {parsed['payload'].decode('utf-8')}")