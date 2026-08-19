"""
IPv7 — Two Nodes Benchmark (experimental, standalone).

Dos instancias UDP reales hablando entre si, usando Container V1
(experimental/container_v1.py, ya validado 27/27 en Fase 4.7).

Deliberadamente NO incluye Identity, Session ni Channel: es la base
minima funcional para verificar que dos nodos se hablan y medir
rendimiento real (latencia + throughput). Se puede agregar o quitar
cosas del Core con el tiempo; esto es el punto de partida ejecutable.

Uso (dos terminales distintas):

    # Terminal 1 — Nodo B (echo):
    python -m experimental.two_nodes_bench echo --port 9101

    # Terminal 2 — Nodo A (mide latencia + throughput contra B):
    python -m experimental.two_nodes_bench bench --port 9102 --peer-port 9101
"""

import argparse
import socket
import struct
import time

from .container_v1 import ContainerV1, ObjectV1

TYPE_PING = 1
TYPE_PONG = 2
TYPE_DATA = 3

_SEQ_FORMAT = '!Q'  # 8 bytes, big endian


def make_container(obj_type: int, seq: int, payload: bytes) -> bytes:
    """Construir un Container V1 con un unico Object: [seq(8B)] + payload."""
    value = struct.pack(_SEQ_FORMAT, seq) + payload
    return ContainerV1(objects=[ObjectV1(type=obj_type, id=0, value=value)]).encode()


def parse_container(raw: bytes):
    """Devuelve (obj_type, seq, payload) desde un Container V1 de un solo Object."""
    container = ContainerV1.decode(raw)
    obj = container.objects[0]
    seq = struct.unpack(_SEQ_FORMAT, obj.value[:8])[0]
    payload = obj.value[8:]
    return obj.type, seq, payload


class UdpEndpoint:
    """Socket UDP minimo, sin Session ni Channel: transporte crudo."""

    def __init__(self, port: int):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
        self.sock.bind(("0.0.0.0", port))

    def send(self, data: bytes, addr) -> None:
        self.sock.sendto(data, addr)

    def recv(self, bufsize: int = 65535):
        return self.sock.recvfrom(bufsize)


def run_echo(port: int) -> None:
    """Nodo B: responde PING con PONG; cuenta throughput de DATA recibido."""
    ep = UdpEndpoint(port)
    print(f"[echo] escuchando en UDP :{port} (Ctrl+C para salir)")

    count = 0
    t_start = None
    try:
        while True:
            data, addr = ep.recv()
            if t_start is None:
                t_start = time.perf_counter()
            try:
                obj_type, seq, payload = parse_container(data)
            except Exception:
                continue  # Container corrupto o ruido: ignorar, no crashear.

            if obj_type == TYPE_PING:
                ep.send(make_container(TYPE_PONG, seq, payload), addr)
                t_start = None  # reiniciar ventana de throughput tras cada rafaga de pings
            elif obj_type == TYPE_DATA:
                count += 1
                if count % 10000 == 0:
                    elapsed = time.perf_counter() - t_start
                    print(f"[echo] recibidos {count} DATA en {elapsed:.3f}s "
                          f"({count / elapsed:.0f} msg/s)")
    except KeyboardInterrupt:
        print("\n[echo] detenido")


def run_bench(port: int, peer_ip: str, peer_port: int, pings: int, burst: int, size: int) -> None:
    """Nodo A: mide latencia (ping-pong) y throughput (rafaga unidireccional) contra B."""
    ep = UdpEndpoint(port)
    peer_addr = (peer_ip, peer_port)
    payload = b"x" * size

    # --- Latencia: ping-pong secuencial ---
    latencies = []
    ep.sock.settimeout(2.0)
    for seq in range(pings):
        msg = make_container(TYPE_PING, seq, payload)
        t0 = time.perf_counter()
        ep.send(msg, peer_addr)
        try:
            data, _ = ep.recv()
        except socket.timeout:
            print(f"[bench] timeout esperando pong seq={seq}")
            continue
        t1 = time.perf_counter()
        obj_type, rseq, _ = parse_container(data)
        if obj_type == TYPE_PONG and rseq == seq:
            latencies.append((t1 - t0) * 1000.0)

    if latencies:
        latencies.sort()
        n = len(latencies)
        avg = sum(latencies) / n
        p50 = latencies[n // 2]
        p99 = latencies[min(int(n * 0.99), n - 1)]
        print(f"[bench] latencia RTT sobre {n}/{pings} pings: "
              f"avg={avg:.3f}ms  min={latencies[0]:.3f}ms  "
              f"p50={p50:.3f}ms  p99={p99:.3f}ms  max={latencies[-1]:.3f}ms")
    else:
        print("[bench] no se recibio ningun pong; revisar que 'echo' este corriendo")

    # --- Throughput: rafaga unidireccional (fire-and-forget) ---
    ep.sock.settimeout(None)
    total_bytes = 0
    t0 = time.perf_counter()
    for seq in range(burst):
        msg = make_container(TYPE_DATA, seq, payload)
        ep.send(msg, peer_addr)
        total_bytes += len(msg)
    elapsed = time.perf_counter() - t0
    mb = total_bytes / (1024 * 1024)
    if elapsed > 0:
        print(f"[bench] throughput (envio): {burst} mensajes ({mb:.2f} MB) en "
              f"{elapsed:.3f}s = {burst / elapsed:.0f} msg/s, {mb / elapsed:.2f} MB/s")


def main() -> None:
    parser = argparse.ArgumentParser(description="IPv7 Two Nodes Benchmark (experimental)")
    sub = parser.add_subparsers(dest="role", required=True)

    p_echo = sub.add_parser("echo", help="Nodo B: responde ping/pong, cuenta throughput de DATA")
    p_echo.add_argument("--port", type=int, required=True)

    p_bench = sub.add_parser("bench", help="Nodo A: mide latencia y throughput contra 'echo'")
    p_bench.add_argument("--port", type=int, required=True)
    p_bench.add_argument("--peer-port", type=int, required=True)
    p_bench.add_argument("--peer-ip", default="127.0.0.1")
    p_bench.add_argument("--pings", type=int, default=200)
    p_bench.add_argument("--burst", type=int, default=5000)
    p_bench.add_argument("--size", type=int, default=64)

    args = parser.parse_args()
    if args.role == "echo":
        run_echo(args.port)
    else:
        run_bench(args.port, args.peer_ip, args.peer_port, args.pings, args.burst, args.size)


if __name__ == "__main__":
    main()
