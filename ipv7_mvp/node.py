"""
IPv7 Node - Nodo básico con CLI
FASE 2: Node funcional
"""

import socket
import threading
import time
import struct
import os
import sys
from typing import Dict, Set, Optional, Tuple
from dataclasses import dataclass

from packet import IPv7Packet, MessageType
from object import IDTLVObject, ObjectType

# Integración Core <-> MVP (Fase 2): usar las implementaciones oficiales
# de src/core en lugar de duplicarlas dentro de ipv7_mvp.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from core.session_manager import SessionManager, Session  # noqa: E402
from core.channel_manager import ChannelManager  # noqa: E402


@dataclass
class Peer:
    """Información básica de un peer descubierto"""
    node_id: int
    address: str
    port: int
    last_seen: float
    mtu: int = 1280  # MTU del peer


class IPv7Node:
    """
    Nodo IPv7 básico con funcionalidad mínima
    """
    
    def __init__(self, port: int = 9000, mtu: int = 1280, name: Optional[str] = None,
                 public_address: str = "127.0.0.1", network=None, node_id: Optional[int] = None):
        self.port = port
        self.mtu = mtu  # MTU local configurable
        self.public_address = public_address
        # node_id fijo (para pruebas multiproceso reproducibles) o generado
        self.node_id = node_id if node_id is not None else (hash(f"node_{port}_{time.time()}") & 0xFFFFFFFF)
        self.name = name or f"node-{self.node_id}"
        self.running = False
        self.socket = None
        self.network = network  # LocalRouter para tests, None para UDP real
        
        # Componentes básicos (Core oficial, ver src/core/)
        self.session_manager = SessionManager()
        self.channel_manager = ChannelManager()
        self.peers: Dict[int, Peer] = {}  # node_id -> Peer
        
        # Tabla de rutas mínima: dest_id -> (ip, port) del siguiente salto
        self.routes: Dict[int, Tuple[str, int]] = {}
        
        # Registrar los canales lógicos predefinidos en el ChannelManager real.
        # El Core solo conoce channel_id/estado, NO su semántica (eso es
        # responsabilidad de los Profiles).
        for channel_id in self.channel_manager.predefined_channels:
            self.channel_manager.create_channel(channel_id=int(channel_id), profile="core")
    
    def start(self):
        """Iniciar el nodo (CLI interactiva)"""
        self.start_network()
        self._cli()
    
    def start_network(self):
        """Iniciar la red (socket UDP) si no se usa un router in-process"""
        if self.network:
            self.running = True
            return
        
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("0.0.0.0", self.port))
        
        print(f"[INFO] IPv7 node started")
        print(f"[INFO] Node ID: {self.node_id}")
        print(f"[INFO] Listening on UDP 0.0.0.0:{self.port}")
        print(f"[INFO] Local MTU: {self.mtu}")
        
        # Iniciar hilo receptor
        receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
        receiver_thread.start()

    def stop(self):
        """Detener el nodo"""
        self.running = False
        if self.socket:
            self.socket.close()
        print("[INFO] Node stopped")
    
    def _receive_loop(self):
        """Bucle de recepción de paquetes"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65535)
                self._handle_packet(data, addr)
            except Exception as e:
                if self.running:
                    print(f"[ERROR] Receive error: {e}")
    
    def _handle_packet(self, data: bytes, addr):
        """Manejar paquete recibido"""
        packet = IPv7Packet.decode(data)
        if not packet:
            print(f"[ERROR] Invalid packet from {addr}")
            return
        
        # Reenviar paquetes cuyo destino no sea este nodo.
        # PATH_DISCOVER y PATH_RESPONSE deben ser procesados por cada salto
        # para acumular/reportar informacion de MTU.
        if packet.dest_id != self.node_id:
            if packet.payload:
                msg_type = packet.payload[0]
                if msg_type == MessageType.PATH_DISCOVER:
                    self._handle_path_discover(packet, addr)
                    return
                elif msg_type == MessageType.PATH_RESPONSE:
                    self._handle_path_response(packet, addr)
                    return
            self._forward_packet(packet, addr)
            return
        
        # Manejar tipos de mensajes básicos
        if packet.payload:
            msg_type = packet.payload[0] if len(packet.payload) > 0 else 0
            
            if msg_type == MessageType.HELLO:
                self._handle_hello(packet, addr)
            elif msg_type == MessageType.PING:
                self._handle_ping(packet, addr)
            elif msg_type == MessageType.PONG:
                self._handle_pong(packet, addr)
            elif msg_type == MessageType.DISCOVER:
                self._handle_discover(packet, addr)
            elif msg_type == MessageType.HERE:
                self._handle_here(packet, addr)
            elif msg_type == MessageType.PATH_DISCOVER:
                self._handle_path_discover(packet, addr)
            elif msg_type == MessageType.PATH_RESPONSE:
                self._handle_path_response(packet, addr)
            elif msg_type == MessageType.PATH_CHANGED:
                self._handle_path_changed(packet, addr)
            elif msg_type == MessageType.DATA:
                self._handle_data(packet, addr)
    
    def _handle_hello(self, packet: IPv7Packet, addr):
        """Manejar mensaje HELLO"""
        print(f"[HELLO] Hello from node {packet.source_id} at {addr}")
        # Responder con HELLO
        self._send_hello(packet.source_id, addr)
    
    def _handle_ping(self, packet: IPv7Packet, addr):
        """Manejar PING"""
        print(f"[PING] Ping from node {packet.source_id}")
        # Responder con PONG
        self._send_pong(packet.source_id, addr)
    
    def _handle_pong(self, packet: IPv7Packet, addr):
        """Manejar PONG"""
        print(f"[PONG] Pong from node {packet.source_id}")
    
    def _handle_discover(self, packet: IPv7Packet, addr):
        """Manejar DISCOVER"""
        print(f"[DISCOVERY] Discover request from {addr}")
        # Responder con HERE
        self._send_here(addr)
    
    def _handle_here(self, packet: IPv7Packet, addr):
        """Manejar HERE"""
        peer = Peer(packet.source_id, addr[0], addr[1], time.time())
        self.peers[packet.source_id] = peer
        print(f"[DISCOVERY] Node found: {packet.source_id} at {addr}")
    
    def _handle_path_discover(self, packet: IPv7Packet, addr):
        """Manejar PATH_DISCOVER: agregar MTU local y reenviar o responder"""
        try:
            payload = packet.payload
            
            # Formato: type(1) request_id(4) origin_node_id(4) origin_ip(4) origin_port(2) dest_id(4) ttl(1) path_count(1) [hops]
            if len(payload) < 21:
                print("[PATH] Invalid PATH_DISCOVER payload length")
                return
            
            (msg_type, request_id, origin_node_id, origin_ip_b, origin_port,
             dest_id, ttl, path_count) = struct.unpack('!B I I 4s H I B B', payload[:21])
            
            if msg_type != MessageType.PATH_DISCOVER:
                return
            
            # Parsear path actual
            hop_fmt = '!II4sH'
            hop_size = struct.calcsize(hop_fmt)
            expected_len = 21 + path_count * hop_size
            if len(payload) != expected_len:
                print(f"[PATH] Invalid PATH_DISCOVER length: {len(payload)} != {expected_len}")
                return
            
            path = []
            offset = 21
            for i in range(path_count):
                node_id, mtu, ip_b, port = struct.unpack(hop_fmt, payload[offset:offset+hop_size])
                path.append({
                    'node_id': node_id,
                    'mtu': mtu,
                    'ip': socket.inet_ntoa(ip_b),
                    'port': port
                })
                offset += hop_size
            
            # Protección contra loops
            if any(h['node_id'] == self.node_id for h in path):
                print(f"[PATH] Loop detected, dropping discovery for {dest_id}")
                return
            
            # TTL
            ttl -= 1
            if ttl <= 0:
                print(f"[PATH] TTL expired for discovery to {dest_id}")
                return
            
            # Agregar nodo actual al path
            path.append({
                'node_id': self.node_id,
                'mtu': self.mtu,
                'ip': self.public_address,
                'port': self.port
            })
            path_count += 1
            
            if dest_id == self.node_id:
                # Somos el destino: construir PATH_RESPONSE
                path_mtu = min(h['mtu'] for h in path)
                print(f"[PATH] {self.name} MTU={self.mtu}")
                print(f"[PATH] PATH_MTU={path_mtu}")
                
                # Enviar response de vuelta por el path
                current_index = path_count - 1
                response_payload = struct.pack('!B I I I B',
                    MessageType.PATH_RESPONSE,
                    request_id,
                    dest_id,
                    path_mtu,
                    path_count
                )
                for hop in path:
                    response_payload += struct.pack('!II4sH',
                        hop['node_id'], hop['mtu'], socket.inet_aton(hop['ip']), hop['port'])
                response_payload += struct.pack('!B', current_index)
                
                prev_hop = path[current_index - 1]
                self._send_packet(prev_hop['node_id'], (prev_hop['ip'], prev_hop['port']), 0, response_payload, request_id)
            else:
                # Reenviar al siguiente salto
                next_hop_addr = self.routes.get(dest_id)
                if not next_hop_addr:
                    peer = self.peers.get(dest_id)
                    if not peer:
                        print(f"[PATH] No route to {dest_id}")
                        return
                    next_hop_addr = (peer.address, peer.port)
                
                new_payload = struct.pack('!B I I 4s H I B B',
                    MessageType.PATH_DISCOVER,
                    request_id,
                    origin_node_id,
                    origin_ip_b,
                    origin_port,
                    dest_id,
                    ttl,
                    path_count
                )
                for hop in path:
                    new_payload += struct.pack('!II4sH',
                        hop['node_id'], hop['mtu'], socket.inet_aton(hop['ip']), hop['port'])
                
                print(f"[PATH] {self.name} MTU={self.mtu}")
                self._send_packet(dest_id, next_hop_addr, 0, new_payload, request_id)
        except Exception as e:
            print(f"[ERROR] PATH_DISCOVER handling failed: {e}")
    
    def _handle_path_response(self, packet: IPv7Packet, addr):
        """Manejar PATH_RESPONSE: reenviar hacia el origen o entregar a la sesión"""
        try:
            payload = packet.payload
            
            # type(1) request_id(4) dest_id(4) path_mtu(4) path_count(1) [hops] current_index(1)
            header_size = struct.calcsize('!B I I I B')
            if len(payload) < header_size + 1:
                print("[PATH] Invalid PATH_RESPONSE payload length")
                return
            
            (msg_type, request_id, dest_id, path_mtu, path_count) = struct.unpack('!B I I I B', payload[:header_size])
            
            if msg_type != MessageType.PATH_RESPONSE:
                return
            
            hop_fmt = '!II4sH'
            hop_size = struct.calcsize(hop_fmt)
            hops_end = header_size + path_count * hop_size
            if len(payload) < hops_end + 1:
                print("[PATH] Invalid PATH_RESPONSE hop data")
                return
            
            path = []
            offset = header_size
            for i in range(path_count):
                node_id, mtu, ip_b, port = struct.unpack(hop_fmt, payload[offset:offset+hop_size])
                path.append({
                    'node_id': node_id,
                    'mtu': mtu,
                    'ip': socket.inet_ntoa(ip_b),
                    'port': port
                })
                offset += hop_size
            
            current_index = struct.unpack('!B', payload[hops_end:hops_end+1])[0]
            
            # Encontrar posición propia en el path
            own_index = None
            for i, hop in enumerate(path):
                if hop['node_id'] == self.node_id:
                    own_index = i
                    break
            
            if own_index is None:
                print("[PATH] Response not for this node")
                return
            
            # Verificar que vino del nodo anterior en el camino de retorno
            if current_index != own_index + 1:
                print(f"[PATH] Invalid response current_index: {current_index} != {own_index + 1}")
                return
            
            if own_index == 0:
                # Somos el origen: actualizar sesión
                session = self.session_manager.get_session(request_id)
                if session:
                    session.update_path_mtu(path_mtu)
                    session.path = path
                    for hop in path:
                        print(f"[PATH] Node {hop['node_id']} MTU={hop['mtu']}")
                    print(f"[PATH] PATH_MTU={path_mtu}")
                    print(f"[SESSION] session={request_id} MTU={path_mtu}")
                else:
                    print(f"[SESSION] No session for request {request_id}")
            else:
                # Reenviar al nodo anterior en el path
                prev_hop = path[own_index - 1]
                new_payload = struct.pack('!B I I I B',
                    MessageType.PATH_RESPONSE,
                    request_id,
                    dest_id,
                    path_mtu,
                    path_count
                )
                for hop in path:
                    new_payload += struct.pack('!II4sH',
                        hop['node_id'], hop['mtu'], socket.inet_aton(hop['ip']), hop['port'])
                new_payload += struct.pack('!B', own_index)
                self._send_packet(prev_hop['node_id'], (prev_hop['ip'], prev_hop['port']), 0, new_payload, request_id)
        except Exception as e:
            print(f"[ERROR] PATH_RESPONSE handling failed: {e}")
    
    def _handle_path_changed(self, packet: IPv7Packet, addr):
        """Manejar PATH_CHANGED: invalidar PATH_MTU de la sesión"""
        print(f"[PATH] Path changed notification for session {packet.session_id}")
        session = self.session_manager.get_session(packet.session_id)
        if session:
            session.update_path_mtu(None)
            session.path = []
            print(f"[SESSION] session={session.session_id} MTU=None (invalidated)")
    
    def _handle_data(self, packet: IPv7Packet, addr):
        """Manejar DATA con validación de integridad"""
        # Verificar SHA-256 antes de procesar
        if not packet.verify_checksum():
            print(f"[ERROR] Integrity check failed from node {packet.source_id}")
            return  # DROP el paquete
        
        print("[DATA] SHA-256 verified")
        print("[DATA] Accepted")
        # Intentar decodificar como IDTLV
        obj = IDTLVObject.decode(packet.payload[1:])  # Skip message type
        if obj:
            print(f"[DATA] Object: type={obj.type}, id={obj.id}, value={obj.value[:20]}...")
    
    def _send_packet(self, dest_id: int, dest_addr: tuple, channel: int = 0, payload: bytes = b'', session_id: int = 0):
        """Enviar paquete con SHA-256"""
        packet = IPv7Packet(
            source_id=self.node_id,
            dest_id=dest_id,
            channel=channel,
            session_id=session_id,
            payload=payload
        )
        self._send_raw(packet.encode(), dest_addr)
    
    def _send_raw(self, encoded: bytes, dest_addr: tuple):
        """Enviar bytes crudos por UDP o por router in-process"""
        if self.network:
            self.network.send(self, encoded, dest_addr)
        elif self.socket:
            self.socket.sendto(encoded, dest_addr)
        else:
            raise RuntimeError("Node has no network or socket")
    
    def _forward_packet(self, packet: IPv7Packet, from_addr: tuple):
        """Reenviar un paquete cuyo destino es otro nodo"""
        next_hop_addr = self.routes.get(packet.dest_id)
        if not next_hop_addr:
            peer = self.peers.get(packet.dest_id)
            if not peer:
                print(f"[FORWARD] No route to {packet.dest_id}, dropping")
                return
            next_hop_addr = (peer.address, peer.port)
        
        # Evitar devolver el paquete al nodo del que acaba de llegar
        if next_hop_addr == from_addr:
            print(f"[FORWARD] Avoiding bounce back to {from_addr}")
            return
        
        print(f"[FORWARD] Relaying packet src={packet.source_id} dst={packet.dest_id} to {next_hop_addr}")
        self._send_raw(packet.encode(), next_hop_addr)
    
    def _send_hello(self, dest_id: int, dest_addr: tuple):
        """Enviar HELLO"""
        self._send_packet(dest_id, dest_addr, 0, bytes([MessageType.HELLO]))
    
    def _send_ping(self, dest_id: int, dest_addr: tuple):
        """Enviar PING"""
        self._send_packet(dest_id, dest_addr, 0, bytes([MessageType.PING]))
    
    def _send_pong(self, dest_id: int, dest_addr: tuple):
        """Enviar PONG"""
        self._send_packet(dest_id, dest_addr, 0, bytes([MessageType.PONG]))
    
    def _send_discover(self, broadcast_addr: tuple = ("255.255.255.255", 9000)):
        """Enviar DISCOVER"""
        self._send_packet(0, broadcast_addr, 0, bytes([MessageType.DISCOVER]))
    
    def _send_here(self, dest_addr: tuple):
        """Enviar HERE"""
        self._send_packet(self.node_id, dest_addr, 0, bytes([MessageType.HERE]))
    
    def discover_path_to_node(self, dest_node_id: int) -> Optional[Session]:
        """
        Descubrir ruta hacia un nodo y calcular PATH_MTU.
        Retorna la sesión creada para la ruta.
        """
        print(f"[PATH] Discovering route to node-{dest_node_id}")
        
        # Buscar sesión existente o crear una nueva (SessionManager oficial)
        existing = self.session_manager.get_sessions_for_remote_node(dest_node_id)
        session = existing[0] if existing else self.session_manager.create_session(dest_node_id, 0, path_mtu=None)
        
        request_id = session.session_id
        
        # Determinar siguiente salto
        next_hop_addr = self.routes.get(dest_node_id)
        if not next_hop_addr:
            peer = self.peers.get(dest_node_id)
            if not peer:
                print(f"[ERROR] No route to node {dest_node_id}")
                return None
            next_hop_addr = (peer.address, peer.port)
        
        # Construir PATH_DISCOVER inicial
        payload = struct.pack('!B I I 4s H I B B',
            MessageType.PATH_DISCOVER,
            request_id,
            self.node_id,
            socket.inet_aton(self.public_address),
            self.port,
            dest_node_id,
            5,  # TTL
            1
        )
        payload += struct.pack('!II4sH',
            self.node_id, self.mtu, socket.inet_aton(self.public_address), self.port)
        
        # Enviar al siguiente salto
        self._send_packet(dest_node_id, next_hop_addr, 0, payload, request_id)
        return session
    
    # _send_path_discover ya no se usa; el descubrimiento inicia en discover_path_to_node
    
    def _send_data(self, dest_id: int, dest_addr: tuple, data: bytes, session_id: int = 0):
        """Enviar DATA con verificación de MTU usando el paquete completo"""
        session = self.session_manager.get_session(session_id)
        if session is None:
            raise RuntimeError("Session not found")
        
        if session.path_mtu is None:
            raise RuntimeError("Session path MTU is not established")
        
        payload = bytes([MessageType.DATA]) + data
        packet = IPv7Packet(
            source_id=self.node_id,
            dest_id=dest_id,
            channel=0,
            session_id=session_id,
            payload=payload
        )
        encoded = packet.encode()
        
        if len(encoded) > session.path_mtu:
            raise RuntimeError(f"Packet size={len(encoded)} exceeds PATH_MTU={session.path_mtu}")
        
        print(f"[DATA] Packet size={len(encoded)} MTU={session.path_mtu}")
        self._send_raw(encoded, dest_addr)
    
    def _cli(self):
        """Interfaz de línea de comandos"""
        print("\nIPv7 Node CLI")
        print("Commands: discover, peers, path <node_id>, sessions, channels, route <node_id> <ip> <port>, ping <node_id>, send <node_id> <message>, quit")
        
        while self.running:
            try:
                cmd = input(f"ipv7[{self.node_id}]> ").strip()
                if not cmd:
                    continue
                
                parts = cmd.split()
                command = parts[0].lower()
                
                if command == "discover":
                    self._cmd_discover()
                elif command == "peers":
                    self._cmd_peers()
                elif command == "path":
                    self._cmd_path(parts)
                elif command == "sessions":
                    self._cmd_sessions()
                elif command == "channels":
                    self._cmd_channels()
                elif command == "route":
                    self._cmd_route(parts)
                elif command == "ping":
                    self._cmd_ping(parts)
                elif command == "send":
                    self._cmd_send(parts)
                elif command == "quit":
                    self.stop()
                    break
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                print(f"[ERROR] Command error: {e}")
    
    def _cmd_discover(self):
        """Comando discover"""
        print("[DISCOVERY] Sending discover broadcast...")
        self._send_discover()
    
    def _cmd_peers(self):
        """Comando peers"""
        print(f"[PEERS] Known peers: {len(self.peers)}")
        for node_id, peer in self.peers.items():
            print(f"  Node {node_id}: {peer.address}:{peer.port} (MTU: {peer.mtu})")
    
    def _cmd_path(self, parts):
        """Comando path - descubrir ruta y MTU"""
        if len(parts) < 2:
            print("Usage: path <node_id>")
            return
        
        try:
            node_id = int(parts[1])
            session = self.discover_path_to_node(node_id)
            if session is None:
                print(f"[ERROR] Unknown node: {node_id}")
                return
            
            print(f"[PATH_DISCOVERY] Waiting for PATH_RESPONSE...")
            if session.path_mtu is not None:
                print(f"[PATH_DISCOVERY] PATH_MTU={session.path_mtu}")
            else:
                print("[PATH_DISCOVERY] PATH_MTU not yet available (real network)")
        except ValueError:
            print("Invalid node_id")
    
    def _cmd_sessions(self):
        """Comando sessions - mostrar sesiones activas"""
        print(f"[SESSIONS] Active sessions: {len(self.session_manager.sessions)}")
        print("SESSION     DESTINATION     MTU")
        for session_id, session in self.session_manager.sessions.items():
            mtu = session.path_mtu if session.path_mtu is not None else "None"
            print(f"{session_id}      {session.remote_node_id}          {mtu}")
    
    def _cmd_route(self, parts):
        """Comando route - fijar manualmente el siguiente salto hacia un destino
        Uso: route <dest_node_id> <ip> <port>
        Mecanismo de enrutamiento minimo: tabla estatica dest_id -> next hop.
        """
        if len(parts) < 4:
            print("Usage: route <dest_node_id> <ip> <port>")
            return
        
        try:
            dest_id = int(parts[1])
            ip = parts[2]
            port = int(parts[3])
            self.routes[dest_id] = (ip, port)
            print(f"[ROUTE] {dest_id} -> {ip}:{port}")
        except ValueError:
            print("Invalid route arguments")
    
    def _cmd_channels(self):
        """Comando channels - mostrar canales registrados en el ChannelManager"""
        active = self.channel_manager.get_active_channels()
        print(f"[CHANNELS] Active channels: {len(active)}")
        for channel_id in sorted(active):
            info = self.channel_manager.get_predefined_channel_info(channel_id)
            name = info["name"] if info else "custom"
            print(f"  {channel_id}: {name}")
    
    def _cmd_ping(self, parts):
        """Comando ping"""
        if len(parts) < 2:
            print("Usage: ping <node_id>")
            return
        
        try:
            node_id = int(parts[1])
            dest_addr = self.routes.get(node_id)
            if not dest_addr:
                peer = self.peers.get(node_id)
                if not peer:
                    print(f"[ERROR] Unknown node: {node_id}")
                    return
                dest_addr = (peer.address, peer.port)
            print(f"[PING] Pinging node {node_id}...")
            self._send_ping(node_id, dest_addr)
        except ValueError:
            print("Invalid node_id")
    
    def _cmd_send(self, parts):
        """Comando send"""
        if len(parts) < 3:
            print("Usage: send <node_id> <message>")
            return
        
        try:
            node_id = int(parts[1])
            message = ' '.join(parts[2:])
            
            # Determinar siguiente salto: ruta explícita o peer conocido
            dest_addr = self.routes.get(node_id)
            if not dest_addr:
                peer = self.peers.get(node_id)
                if not peer:
                    print(f"[ERROR] Unknown node: {node_id}")
                    return
                dest_addr = (peer.address, peer.port)
            
            # Crear o recuperar sesión (SessionManager oficial)
            existing = self.session_manager.get_sessions_for_remote_node(node_id)
            session = existing[0] if existing else self.session_manager.create_session(node_id, 0, path_mtu=None)
            
            # Descubrir ruta si es necesario
            if session.path_mtu is None:
                self.discover_path_to_node(node_id)
                if session.path_mtu is None:
                    print("[ERROR] Path MTU not established yet")
                    return
            
            # Crear objeto IDTLV simple
            obj = IDTLVObject(
                type=ObjectType.STRING,
                id=1,
                value=message.encode('utf-8')
            )
            
            print(f"[SEND] Sending to node {node_id}: {message}")
            self._send_data(node_id, dest_addr, obj.encode(), session.session_id)
        except ValueError:
            print("Invalid node_id")


if __name__ == "__main__":
    import sys
    
    port = 9000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port")
            sys.exit(1)
    
    node = IPv7Node(port)
    try:
        node.start()
    except KeyboardInterrupt:
        node.stop()