"""
IPv7 MVP - Fase 2.5: Validación real de la integración Core <-> MVP

Este script NO es una simulación in-process. Lanza 4 procesos de
sistema operativo independientes (cada uno ejecutando main.py con su
propio socket UDP real), y verifica que:

  - Core SessionManager   (src/core/session_manager.py)
  - Core ChannelManager   (src/core/channel_manager.py)
  - PATH_DISCOVER / PATH_RESPONSE / PATH_MTU
  - SHA-256 (verificado implícitamente en cada paquete recibido)

funcionan de extremo a extremo entre procesos reales comunicados por
UDP en localhost, y no mediante un router in-process compartido
(como el LocalRouter usado en tests.py).

Topología:

    A (UDP 9000, MTU 1500)
      -> B (UDP 9001, MTU 1280)
        -> C (UDP 9002, MTU 1400)
          -> D (UDP 9003, MTU 1500)

PATH_MTU esperado = 1280 (el mínimo de la ruta)
"""

import subprocess
import sys
import os
import time
import threading

NODE_A = {"name": "node-A", "node_id": 101, "port": 9000, "mtu": 1500}
NODE_B = {"name": "node-B", "node_id": 102, "port": 9001, "mtu": 1280}
NODE_C = {"name": "node-C", "node_id": 103, "port": 9002, "mtu": 1400}
NODE_D = {"name": "node-D", "node_id": 104, "port": 9003, "mtu": 1500}

MVP_DIR = os.path.dirname(os.path.abspath(__file__))


def start_node(cfg):
    """Lanza main.py como proceso de sistema operativo independiente"""
    cmd = [
        sys.executable, "main.py",
        "--port", str(cfg["port"]),
        "--mtu", str(cfg["mtu"]),
        "--node-id", str(cfg["node_id"]),
        "--name", cfg["name"],
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=MVP_DIR,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    return proc


def reader_thread(proc, lines, lock):
    for line in proc.stdout:
        with lock:
            lines.append(line.rstrip("\n"))


def send(proc, command):
    proc.stdin.write(command + "\n")
    proc.stdin.flush()


def main():
    print("=" * 60)
    print("IPv7 - Fase 2.5: Validación multiproceso real (UDP real)")
    print("=" * 60)

    procs = {}
    lines = {}
    locks = {}

    for key, cfg in [("A", NODE_A), ("B", NODE_B), ("C", NODE_C), ("D", NODE_D)]:
        print(f"[DRIVER] Starting {cfg['name']} (pid pending) UDP {cfg['port']} MTU={cfg['mtu']}")
        proc = start_node(cfg)
        procs[key] = proc
        lines[key] = []
        locks[key] = threading.Lock()
        t = threading.Thread(target=reader_thread, args=(proc, lines[key], locks[key]), daemon=True)
        t.start()

    # Esperar a que los 4 procesos hagan bind() de su socket UDP real
    time.sleep(2.0)

    for key in ["A", "B", "C", "D"]:
        if procs[key].poll() is not None:
            print(f"[FAIL] Node {key} exited early")
            print("\n".join(lines[key]))
            cleanup(procs)
            return 1

    print("[DRIVER] All 4 independent OS processes are running with real UDP sockets")

    # Configurar rutas estáticas mínimas hacia D (dest_node_id -> next hop)
    # A -> B -> C -> D
    send(procs["A"], f"route {NODE_D['node_id']} 127.0.0.1 {NODE_B['port']}")
    send(procs["B"], f"route {NODE_D['node_id']} 127.0.0.1 {NODE_C['port']}")
    send(procs["C"], f"route {NODE_D['node_id']} 127.0.0.1 {NODE_D['port']}")
    time.sleep(0.5)

    print(f"[DRIVER] Routes configured: A->B->C->D (dest={NODE_D['node_id']})")

    # Disparar PATH_DISCOVER real (paquetes UDP viajando entre 4 procesos distintos)
    send(procs["A"], f"path {NODE_D['node_id']}")
    time.sleep(1.5)
    send(procs["A"], "sessions")
    send(procs["A"], "channels")
    time.sleep(0.5)

    output_a = "\n".join(lines["A"])
    print("\n----- OUTPUT NODE A (proceso independiente) -----")
    print(output_a)
    print("---------------------------------------------------\n")

    checks = {
        "PATH_DISCOVER iniciado": "[PATH] Discovering route to node-104" in output_a,
        "Hop B reportó su MTU": "MTU=1280" in output_a,
        "PATH_MTU calculado = 1280": "PATH_MTU=1280" in output_a,
        "SESSION con MTU=1280": "MTU=1280" in output_a and "[SESSION]" in output_a,
        "ChannelManager real (canales 0-4)": "[CHANNELS] Active channels: 5" in output_a,
    }

    all_pass = True
    print("RESULTADOS:")
    for check, ok in checks.items():
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  {status} {check}")
        if not ok:
            all_pass = False

    send(procs["A"], "quit")
    send(procs["B"], "quit")
    send(procs["C"], "quit")
    send(procs["D"], "quit")
    time.sleep(0.5)

    cleanup(procs)

    print("\n" + "=" * 60)
    if all_pass:
        print("[SUCCESS] Integración Core <-> MVP validada entre procesos reales")
    else:
        print("[WARNING] Alguna verificación falló")
    print("=" * 60)

    return 0 if all_pass else 1


def cleanup(procs):
    for proc in procs.values():
        if proc.poll() is None:
            proc.terminate()
    time.sleep(0.3)
    for proc in procs.values():
        if proc.poll() is None:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
