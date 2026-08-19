"""
IPv7 MVP Tests - PATH MTU + SHA-256 real
Tests obligatorios según especificaciones
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from packet import IPv7Packet, MessageType
from node import IPv7Node  # node.py ya importa el SessionManager/ChannelManager oficiales
from core.session_manager import SessionManager
from core.channel_manager import ChannelManager
import struct


class LocalRouter:
    """Router in-process para tests: entrega paquetes entre nodos"""
    def __init__(self):
        self.nodes = {}
    
    def add_node(self, node):
        self.nodes[node.port] = node
        node.network = self
    
    def send(self, sender, encoded, dest_addr):
        ip, port = dest_addr
        target = self.nodes.get(port)
        if target is None:
            raise RuntimeError(f"No node at port {port}")
        target._handle_packet(encoded, (sender.public_address, sender.port))


def test_sha256_correct():
    """Test 1: SHA-256 correcto"""
    print("\n=== TEST 1: SHA-256 Correcto ===")
    
    packet = IPv7Packet(
        source_id=100,
        dest_id=200,
        channel=0,
        session_id=12345,
        payload=b"test data"
    )
    
    encoded = packet.encode()
    print(f"Encoded packet size: {len(encoded)} bytes")
    
    decoded = IPv7Packet.decode(encoded)
    
    if decoded.verify_checksum():
        print("[PASS] SHA-256 verification PASSED")
        return True
    else:
        print("[FAIL] SHA-256 verification FAILED")
        return False


def test_corruption():
    """Test 2: Corrupción de payload"""
    print("\n=== TEST 2: Corrupción ===")
    
    packet = IPv7Packet(
        source_id=100,
        dest_id=200,
        channel=0,
        session_id=12345,
        payload=b"test data"
    )
    
    encoded = packet.encode()
    
    payload_start = IPv7Packet.HEADER_SIZE
    corrupted = bytearray(encoded)
    corrupted[payload_start + 2] ^= 0xFF
    
    corrupted_packet = IPv7Packet.decode(bytes(corrupted))
    
    if not corrupted_packet.verify_checksum():
        print("[PASS] Corrupted packet correctly REJECTED")
        return True
    else:
        print("[FAIL] Corrupted packet incorrectly ACCEPTED")
        return False


def test_real_path_mtu():
    """Test 3: PATH_MTU real atravesando A -> B -> C -> D"""
    print("\n=== TEST 3: PATH MTU Real (A -> B -> C -> D) ===")
    
    router = LocalRouter()
    
    A = IPv7Node(port=9001, mtu=1500, name="node-A")
    B = IPv7Node(port=9002, mtu=1400, name="node-B")
    C = IPv7Node(port=9003, mtu=1280, name="node-C")
    D = IPv7Node(port=9004, mtu=1500, name="node-D")
    
    for node in [A, B, C, D]:
        router.add_node(node)
    
    # Tablas de ruta mínimas
    A.routes[D.node_id] = (B.public_address, B.port)
    B.routes[D.node_id] = (C.public_address, C.port)
    C.routes[D.node_id] = (D.public_address, D.port)
    
    # Descubrir ruta desde A a D
    session = A.discover_path_to_node(D.node_id)
    if session is None:
        print("[FAIL] discover_path_to_node returned None")
        return False
    
    if session.path_mtu is None:
        print("[FAIL] PATH_MTU not discovered")
        return False
    
    if session.path_mtu == 1280:
        print(f"[PASS] PATH_MTU correctly discovered: {session.path_mtu}")
        return True
    else:
        print(f"[FAIL] PATH_MTU expected 1280, got {session.path_mtu}")
        return False


def test_mtu_boundary():
    """Test 4: Paquetes en el límite del MTU"""
    print("\n=== TEST 4: MTU Boundary ===")
    
    A = IPv7Node(port=9010, mtu=1500, name="node-A-boundary")
    A._send_raw = lambda encoded, dest_addr: None  # evitar envío real
    
    session = A.session_manager.create_session(123, 0, path_mtu=1280)
    dest_addr = ("127.0.0.1", 9100)
    
    # Tamaño del paquete completo = HEADER_SIZE + 1 (type DATA) + len(data) + CHECKSUM_SIZE
    # 1280 = 18 + 1 + len(data) + 32  -> len(data) = 1229
    
    results = []
    
    # 1279 bytes -> OK
    data_1279 = b"X" * 1228
    try:
        A._send_data(123, dest_addr, data_1279, session.session_id)
        results.append(("1279", True))
        print("[PASS] Packet 1279 bytes accepted")
    except RuntimeError as e:
        print(f"[FAIL] Packet 1279 bytes rejected: {e}")
        results.append(("1279", False))
    
    # 1280 bytes -> OK
    data_1280 = b"X" * 1229
    try:
        A._send_data(123, dest_addr, data_1280, session.session_id)
        results.append(("1280", True))
        print("[PASS] Packet 1280 bytes accepted")
    except RuntimeError as e:
        print(f"[FAIL] Packet 1280 bytes rejected: {e}")
        results.append(("1280", False))
    
    # 1281 bytes -> REJECT
    data_1281 = b"X" * 1230
    try:
        A._send_data(123, dest_addr, data_1281, session.session_id)
        print("[FAIL] Packet 1281 bytes accepted")
        results.append(("1281", False))
    except RuntimeError as e:
        print(f"[PASS] Packet 1281 bytes correctly rejected: {e}")
        results.append(("1281", True))
    
    return all(r[1] for r in results)


def test_path_change():
    """Test 5: Cambio de ruta invalida PATH_MTU y redescubre"""
    print("\n=== TEST 5: Path Change ===")
    
    router = LocalRouter()
    
    A = IPv7Node(port=9021, mtu=1500, name="node-A")
    B = IPv7Node(port=9022, mtu=1400, name="node-B")
    C = IPv7Node(port=9023, mtu=1400, name="node-C")
    D = IPv7Node(port=9024, mtu=1100, name="node-D")
    
    for node in [A, B, C, D]:
        router.add_node(node)
    
    # Ruta 1: A -> B -> C (min 1400)
    A.routes[C.node_id] = (B.public_address, B.port)
    B.routes[C.node_id] = (C.public_address, C.port)
    
    session = A.discover_path_to_node(C.node_id)
    if session is None or session.path_mtu != 1400:
        print(f"[FAIL] Route 1 PATH_MTU expected 1400, got {session.path_mtu if session else None}")
        return False
    print(f"[PASS] Route 1 PATH_MTU={session.path_mtu}")
    
    # PATH_CHANGED: invalidar sesión
    changed_packet = IPv7Packet(
        source_id=B.node_id,
        dest_id=A.node_id,
        session_id=session.session_id,
        payload=bytes([MessageType.PATH_CHANGED])
    )
    A._handle_path_changed(changed_packet, (B.public_address, B.port))
    
    if session.path_mtu is not None:
        print(f"[FAIL] Session MTU not invalidated: {session.path_mtu}")
        return False
    print("[PASS] Session MTU invalidated to None")
    
    # Ruta 2: A -> B -> D -> C (min 1100)
    B.routes[C.node_id] = (D.public_address, D.port)
    D.routes[C.node_id] = (C.public_address, C.port)
    
    session = A.discover_path_to_node(C.node_id)
    if session is None or session.path_mtu != 1100:
        print(f"[FAIL] Route 2 PATH_MTU expected 1100, got {session.path_mtu if session else None}")
        return False
    print(f"[PASS] Route 2 PATH_MTU={session.path_mtu}")
    
    return True


def test_channel_manager():
    """Test 6: ChannelManager - creación y consulta de canales"""
    print("\n=== TEST 6: ChannelManager ===")
    
    cm = ChannelManager()
    
    for channel_id in [0, 1, 2]:
        cm.create_channel(channel_id=channel_id, profile="core")
    
    for channel_id in [0, 1, 2]:
        channel = cm.get_channel(channel_id)
        if channel is None:
            print(f"[FAIL] Channel {channel_id} not found after creation")
            return False
        if not cm.is_predefined_channel(channel_id):
            print(f"[FAIL] Channel {channel_id} should be predefined")
            return False
    
    print(f"[PASS] Channels 0,1,2 created and queryable: {cm.get_active_channels()}")
    return True


def test_session_manager_core():
    """Test 7: SessionManager (Core) - channel, remote_node, path_mtu"""
    print("\n=== TEST 7: SessionManager Core ===")
    
    sm = SessionManager()
    session = sm.create_session(remote_node_id=200, channel=1, path_mtu=1280)
    
    if session.remote_node_id != 200:
        print(f"[FAIL] remote_node_id incorrect: {session.remote_node_id}")
        return False
    if session.channel != 1:
        print(f"[FAIL] channel incorrect: {session.channel}")
        return False
    if session.path_mtu != 1280:
        print(f"[FAIL] path_mtu incorrect: {session.path_mtu}")
        return False
    
    print(f"[PASS] Session created: channel={session.channel} remote_node={session.remote_node_id} path_mtu={session.path_mtu}")
    return True


def test_core_session_path_mtu():
    """Test 8: Core + Session - path_mtu sigue funcionando end-to-end"""
    print("\n=== TEST 8: Core + Session (PATH_MTU) ===")
    
    A = IPv7Node(port=9031, mtu=1500, name="node-A-core")
    B = IPv7Node(port=9032, mtu=1280, name="node-B-core")
    
    router = LocalRouter()
    router.add_node(A)
    router.add_node(B)
    
    A.routes[B.node_id] = (B.public_address, B.port)
    
    session = A.discover_path_to_node(B.node_id)
    
    if session is None or session.path_mtu != 1280:
        print(f"[FAIL] Expected path_mtu=1280, got {session.path_mtu if session else None}")
        return False
    
    # Confirmar que la sesión vive en el SessionManager oficial (Core)
    from_manager = A.session_manager.get_session(session.session_id)
    if from_manager is None or from_manager.path_mtu != 1280:
        print("[FAIL] Session not retrievable from Core SessionManager")
        return False
    
    print(f"[PASS] Core Session path_mtu={session.path_mtu} (session_id={session.session_id})")
    return True


def test_core_channel_session():
    """Test 9: Core + Channel - session usa ChannelManager real, no el dict antiguo del MVP"""
    print("\n=== TEST 9: Core + Channel ===")
    
    A = IPv7Node(port=9041, mtu=1500, name="node-A-channel")
    
    # El nodo ya no debe tener un dict estático 'channels'; debe usar channel_manager
    if hasattr(A, "channels"):
        print("[FAIL] node still has legacy 'channels' dict attribute")
        return False
    
    active = A.channel_manager.get_active_channels()
    if not {0, 1, 2, 3, 4}.issubset(active):
        print(f"[FAIL] Expected channels 0-4 registered, got {active}")
        return False
    
    session = A.session_manager.create_session(remote_node_id=999, channel=2)
    if session.channel != 2:
        print(f"[FAIL] Session channel mismatch: {session.channel}")
        return False
    
    print(f"[PASS] ChannelManager active channels: {sorted(active)}, session.channel={session.channel}")
    return True


def run_all_tests():
    """Ejecutar todos los tests"""
    print("=" * 50)
    print("IPv7 MVP Tests - PATH MTU + SHA-256")
    print("=" * 50)
    
    results = []
    
    results.append(("SHA-256 Correcto", test_sha256_correct()))
    results.append(("Corrupción", test_corruption()))
    results.append(("PATH MTU Real", test_real_path_mtu()))
    results.append(("MTU Boundary", test_mtu_boundary()))
    results.append(("Path Change", test_path_change()))
    results.append(("ChannelManager", test_channel_manager()))
    results.append(("SessionManager Core", test_session_manager_core()))
    results.append(("Core + Session (PATH_MTU)", test_core_session_path_mtu()))
    results.append(("Core + Channel", test_core_channel_session()))
    
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] All tests PASSED")
        return 0
    else:
        print("[WARNING] Some tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())