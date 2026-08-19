"""
IPv7 — Control plane mínimo para mesh (tracker sobre Firebase).

Cada nodo publica su información y puede leer la lista de peers.
"""

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path

from experimental.vpn.keygen import generate_keypair
from experimental.vpn.nat_setup import (
    STUN_SERVER,
    db_get,
    db_put,
    discover_public_endpoint,
    has_internet,
    load_firebase_url,
)


SAFE_ID = re.compile(r"^[a-z0-9_-]{1,32}$")


def sanitize_node_id(node_id: str) -> str:
    if not SAFE_ID.match(node_id):
        raise ValueError("node_id solo a-z 0-9 - _")
    return node_id


def publish_node(base_url: str, session: str, node_id: str, info: dict):
    url = f"{base_url}/mesh/{session}/{node_id}"
    return db_put(url, info)


def list_peers(base_url: str, session: str):
    url = f"{base_url}/mesh/{session}"
    return db_get(url) or {}


def list_active_peers(base_url: str, session: str, now=None):
    if now is None:
        now = time.time()
    peers = list_peers(base_url, session)
    active = {}
    for pid, pdata in peers.items():
        ts = pdata.get("timestamp", 0)
        expiry = pdata.get("expiry", 0)
        if expiry and now - ts > expiry:
            continue
        active[pid] = pdata
    return active


async def main():
    parser = argparse.ArgumentParser(description="IPv7 mesh tracker")
    parser.add_argument("--session", required=True, help="codigo de la red mesh")
    parser.add_argument("--node-id", required=True, help="identificador unico del nodo")
    parser.add_argument("--endpoint", help="endpoint publico manual ip:puerto")
    parser.add_argument("--port", type=int, default=0, help="puerto local UDP")
    parser.add_argument("--relay-port", type=int, default=47000, help="puerto TCP del relay")
    parser.add_argument("--stun-host", default=STUN_SERVER[0])
    parser.add_argument("--stun-port", type=int, default=STUN_SERVER[1])
    args = parser.parse_args()

    node_id = sanitize_node_id(args.node_id)
    base_url = load_firebase_url()

    print(f"[tracker] nodo={node_id}")

    if args.endpoint:
        public_endpoint = args.endpoint
        local_port = args.port if args.port else public_endpoint.rsplit(":", 1)[1]
    else:
        print("[tracker] descubriendo endpoint con STUN ...")
        public_endpoint, local_port = await discover_public_endpoint(
            (args.stun_host, args.stun_port)
        )

    print(f"[tracker] publico: {public_endpoint}  local: {local_port}")

    keys = generate_keypair()

    info = {
        "id": node_id,
        "public_key": keys.public_b64,
        "endpoint": public_endpoint,
        "local_port": local_port,
        "relay_port": args.relay_port,
        "can_gateway": has_internet(),
        "capabilities": ["mesh"],
        "profiles": ["mesh.v1"],
        "availability": "available",
        "truth": "declared",
        "source": node_id,
        "expiry": 3600,
        "timestamp": time.time(),
    }

    publish_node(base_url, args.session, node_id, info)
    print(f"[tracker] publicado en /mesh/{args.session}/{node_id}")

    print("[tracker] pares conocidos:")
    for _ in range(15):
        time.sleep(2)
        peers = list_active_peers(base_url, args.session)
        for pid, pdata in peers.items():
            if pid == node_id:
                continue
            print(f"  - {pid}: {pdata.get('endpoint')}  relay={pdata.get('relay_port')}  can_gateway={pdata.get('can_gateway')}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
