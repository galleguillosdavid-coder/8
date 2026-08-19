"""
Test local del relay DERP: dos clientes en la misma PC.
"""

import socket
import struct
import threading
import time

from .derp_client import DerpClient
from .derp_relay import run_relay


def test_relay():
    threading.Thread(target=run_relay, args=("127.0.0.1", 47001), daemon=True).start()
    time.sleep(0.2)

    received = {}

    a = DerpClient("alice", "127.0.0.1", 47001)
    a.on_packet = lambda src, p: received.setdefault(src, p)
    a.connect()

    b = DerpClient("bob", "127.0.0.1", 47001)
    b.on_packet = lambda src, p: received.setdefault(src, p)
    b.connect()

    time.sleep(0.2)
    a.send("bob", b"hola bob")
    b.send("alice", b"hola alice")

    time.sleep(0.5)

    assert "bob" in received, f"alice no recibio: {received}"
    assert "alice" in received, f"bob no recibio: {received}"
    assert received["bob"] == b"hola alice"
    assert received["alice"] == b"hola bob"
    print("OK: DERP relay funciona")

    a.close()
    b.close()


if __name__ == "__main__":
    test_relay()
