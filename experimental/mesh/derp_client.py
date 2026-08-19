"""
IPv7 — Cliente DERP-like mínimo (experimental).
"""

import argparse
import socket
import struct
import sys
import threading
import time


def send_frame(sock, msg_type: int, src: bytes | None, payload: bytes):
    if src is None:
        src = b""
    header = struct.pack("!B B H", msg_type, len(src), len(payload)) + src
    sock.sendall(header + payload)


def recv_frame(sock):
    buf = b""
    while len(buf) < 4:
        chunk = sock.recv(4 - len(buf))
        if not chunk:
            return None
        buf += chunk
    msg_type, src_len, payload_len = struct.unpack("!B B H", buf)

    extra = src_len + payload_len
    buf = b""
    while len(buf) < extra:
        chunk = sock.recv(extra - len(buf))
        if not chunk:
            return None
        buf += chunk
    src = buf[:src_len]
    payload = buf[src_len:]
    return msg_type, src, payload


class DerpClient:
    def __init__(self, node_id, relay_host="127.0.0.1", relay_port=47000):
        self.node_id = node_id.encode() if isinstance(node_id, str) else node_id
        self.relay_host = relay_host
        self.relay_port = relay_port
        self.sock = None
        self.on_packet = None
        self.connected = False

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.relay_host, self.relay_port))
        send_frame(self.sock, 1, None, self.node_id)
        self.connected = True
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def _recv_loop(self):
        while self.connected:
            try:
                frame = recv_frame(self.sock)
                if not frame:
                    break
                msg_type, src, payload = frame
                if msg_type == 3 and self.on_packet:
                    self.on_packet(src.decode(), payload)
            except OSError:
                break
        self.connected = False

    def send(self, dest: str, payload: bytes):
        if not self.connected or not self.sock:
            raise RuntimeError("no conectado")
        dest_bytes = dest.encode() if isinstance(dest, str) else dest
        data = bytes([len(dest_bytes)]) + dest_bytes + payload
        send_frame(self.sock, 2, None, data)

    def close(self):
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--relay", default="127.0.0.1:47000")
    parser.add_argument("--to")
    parser.add_argument("--text")
    args = parser.parse_args()

    host, port = args.relay.rsplit(":", 1)
    client = DerpClient(args.id, host, int(port))
    client.on_packet = lambda src, p: print(f"[{args.id}] de {src}: {p.decode('utf-8', 'replace')}")
    client.connect()
    print(f"[{args.id}] conectado a {args.relay}")

    if args.to and args.text:
        time.sleep(0.2)
        client.send(args.to, args.text.encode())
        print(f"[{args.id}] enviado a {args.to}: {args.text}")

    try:
        while client.connected:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        client.close()


if __name__ == "__main__":
    main()
