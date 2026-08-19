"""
IPv7 — Chat mínimo sobre DERP (experimental).

Uso:
    # terminal 1
    python -m experimental.mesh.derp_relay --port 47000

    # terminal 2
    python -m experimental.mesh.mesh_chat --session s1 --node-id n1 --peer n2 --relay 127.0.0.1:47000

    # terminal 3
    python -m experimental.mesh.mesh_chat --session s1 --node-id n2 --peer n1 --relay 127.0.0.1:47000
"""

import argparse
import asyncio
import sys
import threading
import time

from .derp_client import DerpClient
from .tracker import list_peers, load_firebase_url, publish_node
from ..vpn.keygen import generate_keypair
from ..vpn.nat_setup import STUN_SERVER, discover_public_endpoint, has_internet


def discover_and_publish(session, node_id, relay_host, relay_port):
    """Publica nodo en el tracker con un endpoint STUN."""
    base_url = load_firebase_url()
    try:
        public_endpoint, local_port = asyncio.run(discover_public_endpoint(STUN_SERVER))
    except Exception:
        public_endpoint = f"{relay_host}:{relay_port}"
        local_port = 0

    keys = generate_keypair()
    info = {
        "id": node_id,
        "public_key": keys.public_b64,
        "endpoint": public_endpoint,
        "local_port": local_port,
        "relay_port": relay_port,
        "can_gateway": has_internet(),
        "timestamp": time.time(),
    }
    publish_node(base_url, session, node_id, info)
    return base_url


def find_peer_relay(base_url, session, peer_id):
    for _ in range(30):
        peers = list_peers(base_url, session)
        if peer_id in peers:
            p = peers[peer_id]
            endpoint = p.get("endpoint", "")
            relay_port = p.get("relay_port", 47000)
            if ":" in endpoint:
                host = endpoint.rsplit(":", 1)[0]
                return host, int(relay_port)
        time.sleep(1)
    return None, None


def main():
    parser = argparse.ArgumentParser(description="IPv7 mesh chat")
    parser.add_argument("--session", required=True)
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--peer", required=True)
    parser.add_argument("--relay", default="127.0.0.1:47000", help="ip:puerto del DERP relay")
    args = parser.parse_args()

    relay_host, relay_port = args.relay.rsplit(":", 1)
    relay_port = int(relay_port)

    print(f"[{args.node_id}] publicando en tracker ...")
    base_url = discover_and_publish(args.session, args.node_id, relay_host, relay_port)

    host, port = relay_host, relay_port
    print(f"[{args.node_id}] conectando a DERP {host}:{port} ...")
    client = DerpClient(args.node_id, host, port)
    client.on_packet = lambda src, p: print(f"[{args.node_id}] <- {src}: {p.decode('utf-8', 'replace')}")
    client.connect()
    print(f"[{args.node_id}] listo. Escribi mensajes y apreta Enter.")

    def input_loop():
        while client.connected:
            try:
                text = input()
                if text:
                    client.send(args.peer, text.encode())
            except EOFError:
                break
            except Exception as e:
                print(f"error: {e}", file=sys.stderr)
                break

    threading.Thread(target=input_loop, daemon=True).start()
    try:
        while client.connected:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        client.close()


if __name__ == "__main__":
    main()
