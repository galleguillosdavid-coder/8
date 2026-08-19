"""
IPv7 MVP - Demo de 3 nodos con A lejos de C, obligado a usar B como relay.

Topologia:

    A (UDP 9000, MTU 1500, node_id 101)
      -> B (UDP 9001, MTU 1280, node_id 102)
        -> C (UDP 9002, MTU 1400, node_id 103)

A no puede ver directamente a C; todo el trafico pasa por B.
"""

import subprocess
import sys
import os
import time
import threading

NODE_A = {"name": "node-A", "node_id": 101, "port": 9000, "mtu": 1500}
NODE_B = {"name": "node-B", "node_id": 102, "port": 9001, "mtu": 1280}
NODE_C = {"name": "node-C", "node_id": 103, "port": 9002, "mtu": 1400}

MVP_DIR = os.path.dirname(os.path.abspath(__file__))


def start_node(cfg):
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


def dump_output(label, lines, lock):
    with lock:
        print(f"\n===== OUTPUT {label} =====")
        for line in lines:
            print(line)
        print(f"===== END {label} =====")


def cleanup(procs):
    for proc in procs.values():
        if proc.poll() is None:
            proc.terminate()
    time.sleep(0.3)
    for proc in procs.values():
        if proc.poll() is None:
            proc.kill()


def main():
    print("=" * 60)
    print("IPv7 - Demo: A -> B -> C (A lejos de C, relay por B)")
    print("=" * 60)

    procs = {}
    lines = {}
    locks = {}

    for key, cfg in [("A", NODE_A), ("B", NODE_B), ("C", NODE_C)]:
        print(f"[DRIVER] Iniciando {cfg['name']} en UDP {cfg['port']} MTU={cfg['mtu']}")
        proc = start_node(cfg)
        procs[key] = proc
        lines[key] = []
        locks[key] = threading.Lock()
        t = threading.Thread(target=reader_thread, args=(proc, lines[key], locks[key]), daemon=True)
        t.start()

    time.sleep(2.0)

    for key in ["A", "B", "C"]:
        if procs[key].poll() is not None:
            print(f"[FAIL] Nodo {key} termino antes de tiempo")
            dump_output(key, lines[key], locks[key])
            cleanup(procs)
            return 1

    print("[DRIVER] Los 3 nodos estan activos con sockets UDP reales")

    # Configurar rutas estaticas
    # A: para llegar a C pasar por B; B tambien conocido por A
    send(procs["A"], f"route {NODE_C['node_id']} 127.0.0.1 {NODE_B['port']}")
    send(procs["A"], f"route {NODE_B['node_id']} 127.0.0.1 {NODE_B['port']}")

    # B: conoce a A y a C directamente
    send(procs["B"], f"route {NODE_A['node_id']} 127.0.0.1 {NODE_A['port']}")
    send(procs["B"], f"route {NODE_C['node_id']} 127.0.0.1 {NODE_C['port']}")

    # C: para llegar a A pasar por B; B tambien conocido por C
    send(procs["C"], f"route {NODE_A['node_id']} 127.0.0.1 {NODE_B['port']}")
    send(procs["C"], f"route {NODE_B['node_id']} 127.0.0.1 {NODE_B['port']}")

    time.sleep(0.5)
    print("[DRIVER] Rutas configuradas: A -> B -> C")

    # Descubrir ruta desde A hacia C
    print(f"[DRIVER] A inicia PATH_DISCOVER hacia C ({NODE_C['node_id']})")
    send(procs["A"], f"path {NODE_C['node_id']}")
    time.sleep(1.5)

    # Enviar mensaje de A a C via B
    print("[DRIVER] A envia mensaje a C via B")
    send(procs["A"], f"send {NODE_C['node_id']} hola desde A via B")
    time.sleep(1.5)

    # Pedir estado en cada nodo
    send(procs["A"], "sessions")
    send(procs["A"], "peers")
    send(procs["B"], "sessions")
    send(procs["B"], "peers")
    send(procs["C"], "sessions")
    send(procs["C"], "peers")
    time.sleep(0.5)

    # Detener nodos
    for key in ["A", "B", "C"]:
        send(procs[key], "quit")
    time.sleep(0.5)

    cleanup(procs)

    # Mostrar output completo
    for key in ["A", "B", "C"]:
        dump_output(key, lines[key], locks[key])

    # Verificaciones simples
    output_a = "\n".join(lines["A"])
    output_b = "\n".join(lines["B"])
    output_c = "\n".join(lines["C"])

    checks = {
        "A inicio descubrimiento hacia C": "[PATH] Discovering route to node-103" in output_a,
        "PATH_MTU = 1280 (minimo de la ruta)": "PATH_MTU=1280" in output_a,
        "B reenvio PATH_DISCOVER hacia C": "[FORWARD] Relaying packet" in output_b,
        "A envio mensaje a C": "[SEND] Sending to node 103" in output_a,
        "B reenvio DATA de A hacia C": "[FORWARD] Relaying packet src=101 dst=103" in output_b,
        "C recibio el mensaje": "[DATA] Accepted" in output_c,
    }

    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)
    all_pass = True
    for check, ok in checks.items():
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  {status} {check}")
        if not ok:
            all_pass = False

    print("=" * 60)
    if all_pass:
        print("[SUCCESS] A y C se comunicaron exitosamente via B")
    else:
        print("[WARNING] Algunas verificaciones fallaron")
    print("=" * 60)

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
