"""
IPv7 — DERP-like relay mínimo (experimental).

Reenvía paquetes opacos entre nodos usando un ID como dirección.
No descifra el payload.
"""

import socket
import struct
import threading


HOST = "0.0.0.0"
PORT = 47000


def send_frame(conn, msg_type: int, src: bytes | None, payload: bytes):
    """Envia un frame con tipo, origen (opcional) y payload."""
    if src is None:
        src = b""
    header = struct.pack("!B B H", msg_type, len(src), len(payload)) + src
    conn.sendall(header + payload)


def recv_frame(conn):
    """Recibe un frame. Devuelve (msg_type, src, payload) o None si cierra."""
    buf = b""
    while len(buf) < 4:
        chunk = conn.recv(4 - len(buf))
        if not chunk:
            return None
        buf += chunk
    msg_type, src_len, payload_len = struct.unpack("!B B H", buf)

    extra = src_len + payload_len
    buf = b""
    while len(buf) < extra:
        chunk = conn.recv(extra - len(buf))
        if not chunk:
            return None
        buf += chunk
    src = buf[:src_len]
    payload = buf[src_len:]
    return msg_type, src, payload


def run_relay(host=HOST, port=PORT):
    clients = {}
    lock = threading.Lock()

    def client_thread(conn, addr):
        node_id = None
        try:
            frame = recv_frame(conn)
            if not frame or frame[0] != 1:
                conn.close()
                return
            node_id = frame[2]
            with lock:
                clients[node_id] = conn
            print(f"[relay] registrado {node_id.decode()} desde {addr}", flush=True)

            while True:
                frame = recv_frame(conn)
                if not frame:
                    break
                msg_type, _, payload = frame
                if msg_type != 2:
                    continue
                if len(payload) < 1:
                    continue
                dest_len = payload[0]
                dest = payload[1:1 + dest_len]
                packet = payload[1 + dest_len:]
                with lock:
                    dest_conn = clients.get(dest)
                if dest_conn:
                    send_frame(dest_conn, 3, node_id, packet)
                    print(f"[relay] {node_id.decode()} -> {dest.decode()}", flush=True)
                else:
                    print(f"[relay] destino no conectado: {dest.decode()}", flush=True)
        except OSError:
            pass
        finally:
            if node_id:
                with lock:
                    clients.pop(node_id, None)
            try:
                conn.close()
            except OSError:
                pass

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(16)
    print(f"[relay] escuchando en {host}:{port}", flush=True)
    while True:
        conn, addr = sock.accept()
        threading.Thread(target=client_thread, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    run_relay()
