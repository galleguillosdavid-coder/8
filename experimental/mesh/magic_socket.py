"""
IPv7 — MagicSocket: UDP directo + DERP fallback sin duplicados.

Cada mensaje lleva un nonce de 4 bytes. El receptor descarta duplicados.
Si no hay confirmación de UDP directo, se dispara el fallback DERP.
"""

import collections
import socket
import struct
import threading
import time

from .cert_utils import CERT_PATH
from .derp_client import DerpClient


class MagicSocket:
    """Envia por UDP; si no confirma a tiempo, reenvia por DERP."""

    def __init__(self, node_id, local_port, peer_addr, peer_relay=None, peer_id=None, ca_cert=CERT_PATH, use_udp=True):
        self.node_id = node_id
        self.peer_id = peer_id
        self.local_port = local_port
        self.peer_addr = peer_addr
        self.use_udp = use_udp

        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.settimeout(0.2)
        self.udp.bind(("0.0.0.0", local_port))

        self.derp = None
        if peer_relay:
            host, port = peer_relay
            self.derp = DerpClient(node_id, host, port, ca_cert=ca_cert)
            self.derp.on_packet = self._on_derp
        self.on_packet = None
        self.direct_confirmed = False
        self._running = False
        self.path_mtu = 1500
        self._nonce = 0
        self._seen = set()
        self._seen_order = collections.deque(maxlen=1024)
        self._dedup_lock = threading.Lock()

    def connect(self):
        if self.derp:
            self.derp.connect()
        self._running = True
        threading.Thread(target=self._recv_udp, daemon=True).start()

    def _make_packet(self, payload: bytes) -> bytes:
        with self._dedup_lock:
            self._nonce = (self._nonce + 1) % (2 ** 32)
            return struct.pack("!I", self._nonce) + payload

    def _add_seen(self, nonce: bytes) -> bool:
        with self._dedup_lock:
            if nonce in self._seen:
                return False
            if len(self._seen) >= 1024:
                old = self._seen_order.popleft()
                self._seen.discard(old)
            self._seen.add(nonce)
            self._seen_order.append(nonce)
            return True

    def _recv_udp(self):
        while self._running:
            try:
                data, _ = self.udp.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break
            if len(data) < 4:
                continue
            nonce = data[:4]
            payload = data[4:]
            print(f"[recv_udp] nonce={nonce.hex()} len={len(payload)}", flush=True)
            if not self._add_seen(nonce):
                print(f"[recv_udp] duplicate nonce", flush=True)
                continue
            self.direct_confirmed = True
            print(f"[recv_udp] new packet -> on_packet", flush=True)
            if self.on_packet:
                self.on_packet(self.peer_id or self.node_id, payload)

    def _on_derp(self, src, payload):
        if len(payload) < 4:
            return
        nonce = payload[:4]
        data = payload[4:]
        print(f"[on_derp] src={src} nonce={nonce.hex()} len={len(data)}", flush=True)
        if not self._add_seen(nonce):
            print(f"[on_derp] duplicate nonce", flush=True)
            return
        print(f"[on_derp] new packet -> on_packet", flush=True)
        if self.on_packet:
            self.on_packet(src, data)

    def _derp_fallback(self, dest, data):
        if not self.direct_confirmed and self.derp:
            try:
                self.derp.send(dest, data)
            except RuntimeError:
                pass

    def set_mtu(self, mtu):
        self.path_mtu = min(1500, max(1280, int(mtu)))

    def send(self, dest: str, payload: bytes):
        data = self._make_packet(payload)
        print(f"[send] peer_addr={self.peer_addr} use_udp={self.use_udp} mtu={self.path_mtu} len={len(data)} direct={self.direct_confirmed}", flush=True)
        if self.use_udp and self.peer_addr and self.peer_addr[1] and len(data) <= self.path_mtu:
            try:
                sent = self.udp.sendto(data, self.peer_addr)
                print(f"[send] udp sent {sent} bytes to {self.peer_addr}", flush=True)
            except OSError as e:
                print(f"[send] udp error {e}", flush=True)
            if self.derp and not self.direct_confirmed:
                threading.Timer(0.05, self._derp_fallback, args=(dest, data)).start()
        elif self.derp:
            try:
                self.derp.send(dest, data)
                print(f"[send] derp sent to {dest}", flush=True)
            except RuntimeError as e:
                print(f"[send] derp error {e}", flush=True)

    def close(self):
        self._running = False
        self.udp.close()
        if self.derp:
            self.derp.close()
