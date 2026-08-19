"""
IPv7 — Chat minimo sobre ContainerV1 + WireGuard (experimental).

Uso en PC A:
    python -m experimental.vpn.chat --port 9100 --peer 10.7.0.2:9100

Uso en PC B:
    python -m experimental.vpn.chat --port 9100 --peer 10.7.0.1:9100

Cada mensaje viaja como un ContainerV1 con un Object type=CHAT.
"""

import argparse
import socket
import sys
import threading
import time

from ..container_v1 import ContainerV1, ObjectV1, ContainerError


CHAT_TYPE = 100  # reservado para el perfil de chat en este namespace experimental


def encode_message(text: str) -> bytes:
    return ContainerV1(
        objects=[ObjectV1(type=CHAT_TYPE, id=0, value=text.encode("utf-8"))]
    ).encode()


def decode_message(raw: bytes) -> str:
    container = ContainerV1.decode(raw)
    if not container.objects:
        raise ContainerError("Container vacio")
    obj = container.objects[0]
    return obj.value.decode("utf-8")


class UdpChat:
    def __init__(self, port: int, peer_addr: tuple):
        self.peer_addr = peer_addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
        self.sock.bind(("0.0.0.0", port))

    def send(self, text: str) -> None:
        self.sock.sendto(encode_message(text), self.peer_addr)

    def receive_loop(self) -> None:
        while True:
            try:
                data, addr = self.sock.recvfrom(65535)
                try:
                    msg = decode_message(data)
                    print(f"\n[peer] {msg}\n> ", end="", flush=True)
                except ContainerError:
                    pass
            except OSError:
                break


def main() -> None:
    parser = argparse.ArgumentParser(description="IPv7 chat experimental")
    parser.add_argument("--port", type=int, default=9100)
    parser.add_argument("--peer", required=True, help="ip:puerto del otro nodo")
    args = parser.parse_args()

    host, port = args.peer.rsplit(":", 1)
    peer_addr = (host, int(port))
    chat = UdpChat(args.port, peer_addr)

    print(f"[chat] escuchando en UDP :{args.port}")
    print(f"[chat] enviar a {args.peer}")
    print("Escribi mensajes y apreta Enter. Ctrl+C para salir.\n")

    receiver = threading.Thread(target=chat.receive_loop, daemon=True)
    receiver.start()

    try:
        while True:
            text = input("> ")
            if not text:
                continue
            if text.lower() in ("exit", "quit", "salir"):
                break
            chat.send(text)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        chat.sock.close()
        print("[chat] cerrado")
        time.sleep(0.1)


if __name__ == "__main__":
    main()
