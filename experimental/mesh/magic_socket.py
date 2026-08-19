"""
IPv7 — MagicSocket mínimo: intenta UDP directo y usa DERP como fallback.
"""

import socket
import threading
import time

from .cert_utils import CERT_PATH
from .derp_client import DerpClient


class MagicSocket:
    """Envia por UDP; si no confirma en un tiempo, reenvia por DERP."""

    def __init__(self, node_id, local_port, peer_addr, peer_relay=None, ca_cert=CERT_PATH, use_udp=True):
        self.node_id = node_id
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

    def connect(self):
        if self.derp:
            self.derp.connect()
        self._running = True
        threading.Thread(target=self._recv_udp, daemon=True).start()

    def _recv_udp(self):
        while self._running:
            try:
                data, _ = self.udp.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break
            self.direct_confirmed = True
            if self.on_packet:
                self.on_packet(self.node_id, data)

    def _on_derp(self, src, payload):
        if self.on_packet:
            self.on_packet(src, payload)

    def send(self, dest: str, payload: bytes):
        if self.use_udp and self.peer_addr and self.peer_addr[1]:
            try:
                self.udp.sendto(payload, self.peer_addr)
            except OSError:
                pass
            if not self.direct_confirmed:
                time.sleep(0.1)
        if self.derp and not self.direct_confirmed:
            self.derp.send(dest, payload)

    def close(self):
        self._running = False
        self.udp.close()
        if self.derp:
            self.derp.close()
