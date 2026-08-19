"""
IPv7 — Rendezvous NAT + Firebase + WireGuard (experimental).

Cada nodo:
  1. Descubre su IP/puerto publico con STUN usando aioice.
  2. Publica el par (clave publica, endpoint publico) en Firebase RTDB.
  3. Lee el mismo par del otro nodo.
  4. Genera la configuracion WireGuard y (opcional) instala el tunel.

Uso (en cada PC, con el mismo --session):

    python -m experimental.vpn.nat_setup --session 12345 --role a --install
    python -m experimental.vpn.nat_setup --session 12345 --role b --install

O doble click en experimental/vpn/up_ipv7_nat.bat

Notas:
- Requiere reglas de Firebase RTDB abiertas (modo test) para el prototipo.
- La clave privada nunca sale de la PC.
- Si ambos NAT son simetricos, el STUN basico fallara y hara falta TURN/relay.
"""

import argparse
import asyncio
import ipaddress
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import aioice

from .keygen import generate_keypair
from .generate_configs import CONF_TEMPLATE, UP_BAT_TEMPLATE, DOWN_BAT_TEMPLATE, _write


FIREBASE_CONFIG = Path(__file__).with_name("firebase_config.json")
WIREGUARD_EXE = Path(r"C:\Program Files\WireGuard\wireguard.exe")

STUN_SERVER = ("stun.l.google.com", 19302)


def load_firebase_url() -> str:
    with open(FIREBASE_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)["databaseURL"].rstrip("/")


def db_put(url: str, data: dict):
    req = urllib.request.Request(
        f"{url}.json",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status == 200


def db_get(url: str):
    with urllib.request.urlopen(f"{url}.json", timeout=15) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body) if body != "null" and body else None


def is_ipv4(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).version == 4
    except ValueError:
        return False


def pick_public_endpoint(conn: aioice.Connection):
    """Elige primer candidato srflx IPv4; si no, un host IPv4 (LAN)."""
    for c in conn.local_candidates:
        if c.type == "srflx" and is_ipv4(c.host):
            return c
    for c in conn.local_candidates:
        if c.type == "host" and is_ipv4(c.host):
            return c
    return None


async def discover_public_endpoint(stun_server):
    conn = aioice.Connection(ice_controlling=True, stun_server=stun_server)
    try:
        await conn.gather_candidates()
        cand = pick_public_endpoint(conn)
        if cand is None:
            raise RuntimeError("No se obtuvo candidato IPv4 valido (STUN fallo)")
        public = f"{cand.host}:{cand.port}"
        local_port = cand.related_port if cand.related_port is not None else cand.port
        return public, local_port
    finally:
        await conn.close()


def wait_for_peer(base_url: str, session: str, role: str, timeout: int = 60):
    other = "b" if role == "a" else "a"
    url = f"{base_url}/sessions/{session}/{other}"
    print(f"Esperando al peer '{other}' en {url} ...")
    for i in range(timeout // 2):
        remote = db_get(url)
        if remote:
            return remote
        print(f"  ... intento {i+1}/{timeout//2}")
        time.sleep(2)
    return None


def install_tunnel(conf_path: Path):
    if not WIREGUARD_EXE.exists():
        raise RuntimeError(f"No se encontro {WIREGUARD_EXE}; instale WireGuard")
    subprocess.run([str(WIREGUARD_EXE), "/installtunnelservice", str(conf_path)], check=True)


def main():
    parser = argparse.ArgumentParser(description="IPv7 NAT rendezvous + WireGuard")
    parser.add_argument("--session", required=True, help="codigo compartido entre ambas PCs")
    parser.add_argument("--role", required=True, choices=["a", "b"], help="rol de esta PC")
    parser.add_argument("--install", action="store_true", help="instalar el tunel WireGuard")
    parser.add_argument("--stun-host", default=STUN_SERVER[0])
    parser.add_argument("--stun-port", type=int, default=STUN_SERVER[1])
    args = parser.parse_args()

    base_url = load_firebase_url()
    stun = (args.stun_host, args.stun_port)
    local_role = args.role
    other_role = "b" if local_role == "a" else "a"

    print("[1/4] Descubriendo endpoint publico con STUN ...")
    public_endpoint, local_port = asyncio.run(discover_public_endpoint(stun))
    print(f"  publico: {public_endpoint}  (puerto local: {local_port})")

    print("[2/4] Generando claves WireGuard ...")
    keys = generate_keypair()

    own = {
        "public_key": keys.public_b64,
        "public_endpoint": public_endpoint,
        "local_port": local_port,
        "timestamp": time.time(),
    }
    own_url = f"{base_url}/sessions/{args.session}/{local_role}"
    db_put(own_url, own)
    print(f"[3/4] Publicados datos de '{local_role}' en Firebase")

    remote = wait_for_peer(base_url, args.session, local_role, timeout=60)
    if remote is None:
        print(f"Timeout esperando al peer '{other_role}'", file=sys.stderr)
        sys.exit(1)

    print(f"  peer remoto: {remote['public_endpoint']}  key: {remote['public_key'][:20]}...")

    address = "10.7.0.1/24" if local_role == "a" else "10.7.0.2/24"
    allowed = "10.7.0.2/32" if local_role == "a" else "10.7.0.1/32"

    conf = CONF_TEMPLATE.format(
        private_key=keys.private_b64,
        address=address,
        listen_port=local_port,
        peer_public_key=remote["public_key"],
        peer_endpoint=remote["public_endpoint"],
        allowed_ips=allowed,
    )

    outdir = Path(__file__).with_name("generated_nat")
    outdir.mkdir(exist_ok=True)
    tunnel_name = f"ipv7-{local_role}-{args.session}"
    conf_path = outdir / f"{tunnel_name}.conf"
    _write(str(conf_path), conf)
    _write(str(outdir / f"up_{tunnel_name}.bat"), UP_BAT_TEMPLATE.format(tunnel_name=tunnel_name))
    _write(str(outdir / f"down_{tunnel_name}.bat"), DOWN_BAT_TEMPLATE.format(tunnel_name=tunnel_name))

    print(f"[4/4] Configuracion generada: {conf_path}")

    if args.install:
        print("Instalando servicio de tunel (requiere admin) ...")
        install_tunnel(conf_path)
        print("Tunel instalado.")
    else:
        print("Ejecuta el .bat generado como administrador para levantar el tunel.")


if __name__ == "__main__":
    main()
