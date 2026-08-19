"""
IPv7 — MagicSocket chat: UDP directo + DERP fallback.

Uso local:
    # terminal 1
    python -m experimental.mesh.magic_chat --session m1 --node-id a --peer b --peer-port 9001 --peer-relay 127.0.0.1:47000 --local-port 9000

    # terminal 2
    python -m experimental.mesh.magic_chat --session m1 --node-id b --peer a --peer-port 9000 --peer-relay 127.0.0.1:47000 --local-port 9001

    # terminal 3 (relay)
    python -m experimental.mesh.derp_relay
"""

import argparse
import asyncio
import socket
import sys
import threading
import time

from .cert_utils import CERT_PATH
from .magic_socket import MagicSocket
from .tracker import list_peers, load_firebase_url, publish_node
from ..vpn.keygen import generate_keypair
from ..vpn.nat_setup import STUN_SERVER, discover_public_endpoint, has_internet


def discover_and_publish(session, node_id, local_port, can_relay=False):
    base_url = load_firebase_url()
    try:
        public_endpoint, _ = asyncio.run(discover_public_endpoint(STUN_SERVER))
    except Exception:
        public_endpoint = f"127.0.0.1:{local_port}"
    keys = generate_keypair()
    info = {
        "id": node_id,
        "public_key": keys.public_b64,
        "endpoint": public_endpoint,
        "local_port": local_port,
        "can_gateway": has_internet(),
        "can_relay": can_relay,
        "timestamp": time.time(),
    }
    publish_node(base_url, session, node_id, info)
    return base_url


def main():
    parser = argparse.ArgumentParser(description="IPv7 MagicSocket chat")
    parser.add_argument("--session", required=True)
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--peer", required=True, help="destino (node_id)")
    parser.add_argument("--peer-port", type=int, default=9001)
    parser.add_argument("--peer-relay", default="127.0.0.1:47000")
    parser.add_argument("--local-port", type=int, default=9000)
    parser.add_argument("--no-udp", action="store_true")
    parser.add_argument("--no-tls", action="store_true")
    args = parser.parse_args()

    ca = None if args.no_tls else CERT_PATH
    relay_host, relay_port = args.peer_relay.rsplit(":", 1)
    relay_port = int(relay_port)
    peer_addr = ("127.0.0.1", args.peer_port)

    print(f"[{args.node_id}] publicando ...", flush=True)
    discover_and_publish(args.session, args.node_id, args.local_port)

    print(f"[{args.node_id}] abriendo UDP :{args.local_port} ...", flush=True)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", args.local_port))
    s.close()

    ms = MagicSocket(
        args.node_id,
        args.local_port,
        peer_addr,
        peer_relay=(relay_host, relay_port),
        ca_cert=ca,
        use_udp=not args.no_udp,
    )
    ms.on_packet = lambda src, p: print(f"[{args.node_id}] <- {src}: {p.decode('utf-8', 'replace')}", flush=True)
    ms.connect()
    print(f"[{args.node_id}] listo.", flush=True)

    def input_loop():
        while True:
            try:
                text = input()
                if text:
                    ms.send(args.peer, text.encode())
            except EOFError:
                break
            except Exception as e:
                print(f"error: {e}", file=sys.stderr)
                break

    threading.Thread(target=input_loop, daemon=True).start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        ms.close()


if __name__ == "__main__":
    main()
