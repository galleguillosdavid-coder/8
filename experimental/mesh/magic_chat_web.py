"""
IPv7 — MagicChat para uso desde la web UI.

Envuelve MagicSocket y ContainerV1 para enviar/recibir chat y archivos.
"""

import asyncio
import json
import queue
import socket
import struct
import threading
import time
from pathlib import Path

from ..container_v1 import ContainerV1, ObjectV1, ContainerError
from ..vpn.keygen import generate_keypair
from ..vpn.nat_setup import STUN_SERVER, discover_public_endpoint, has_internet
from .cert_utils import CERT_PATH
from .magic_socket import MagicSocket
from .packet_v1 import PacketV1
from .tracker import list_peers, load_firebase_url, publish_node
from werkzeug.utils import secure_filename


CHAT_TYPE = 100
FILE_META_TYPE = 101
FILE_CHUNK_TYPE = 102
CHUNK_SIZE = 1200


class IncomingFile:
    def __init__(self, file_id, filename, total_chunks, total_size):
        self.file_id = file_id
        self.filename = filename
        self.total_chunks = total_chunks
        self.total_size = total_size
        self.chunks = {}

    def add_chunk(self, index, data):
        self.chunks[index] = data

    def is_complete(self):
        return len(self.chunks) == self.total_chunks

    def assemble(self):
        return b"".join(self.chunks[i] for i in range(self.total_chunks))


class MagicChat:
    def __init__(
        self,
        session,
        node_id,
        peer_id,
        local_port,
        peer_addr,
        peer_relay,
        incoming,
        data_dir="experimental/mesh/web_data",
        ca_cert=CERT_PATH,
    ):
        self.session = session
        self.node_id = node_id
        self.peer_id = peer_id
        self.incoming = incoming
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.received_dir = self.data_dir / "received"
        self.received_dir.mkdir(exist_ok=True)
        self.uploads_dir = self.data_dir / "uploads"
        self.uploads_dir.mkdir(exist_ok=True)
        self.files = []
        self.files_incoming = {}
        self.file_id_counter = 0
        self.lock = threading.Lock()

        base_url = load_firebase_url()
        try:
            public_endpoint, _ = asyncio.run(discover_public_endpoint(STUN_SERVER))
        except Exception:
            public_endpoint = f"127.0.0.1:{local_port}"
        own_host = public_endpoint.rsplit(":", 1)[0] if ":" in public_endpoint else "127.0.0.1"

        keys = generate_keypair()
        info = {
            "id": node_id,
            "public_key": keys.public_b64,
            "endpoint": public_endpoint,
            "local_port": local_port,
            "relay_port": peer_relay[1] if peer_relay else 0,
            "can_gateway": has_internet(),
            "timestamp": time.time(),
        }
        publish_node(base_url, session, node_id, info)

        peer_addr, peer_relay = self._resolve_peer(
            base_url, session, peer_id, peer_addr, peer_relay, own_host
        )

        use_udp = bool(peer_addr[1])
        self.ms = MagicSocket(
            node_id,
            local_port,
            peer_addr,
            peer_relay=peer_relay,
            ca_cert=ca_cert,
            use_udp=use_udp,
        )
        self.ms.on_packet = self._on_packet
        self.ms.connect()

    @property
    def peer_addr(self):
        return self.ms.peer_addr

    @property
    def port(self):
        return self.ms.local_port

    def _resolve_peer(self, base_url, session, peer_id, peer_addr, peer_relay, own_host):
        if peer_addr and peer_relay:
            return peer_addr, peer_relay
        for _ in range(30):
            time.sleep(1)
            peers = list_peers(base_url, session)
            p = peers.get(peer_id)
            if p:
                endpoint = p.get("endpoint", "")
                if ":" in endpoint:
                    host, port = endpoint.rsplit(":", 1)
                    port = int(port)
                else:
                    host, port = "127.0.0.1", p.get("local_port", 0)
                if not peer_addr:
                    use_ip = "127.0.0.1" if host == own_host else host
                    peer_addr = (use_ip, p.get("local_port", port))
                if not peer_relay:
                    relay_port = p.get("relay_port", 47000)
                    use_ip = "127.0.0.1" if host == own_host else host
                    peer_relay = (use_ip, relay_port)
                break
        if not peer_addr:
            peer_addr = ("127.0.0.1", 0)
        if not peer_relay:
            peer_relay = ("127.0.0.1", 47000)
        return peer_addr, peer_relay

    def _next_file_id(self):
        with self.lock:
            self.file_id_counter += 1
            return self.file_id_counter

    def _on_packet(self, src, payload):
        try:
            container = ContainerV1.decode(PacketV1.unpack(payload))
            for obj in container.objects:
                self._handle_object(obj)
        except ContainerError:
            pass

    def _handle_object(self, obj):
        if obj.type == CHAT_TYPE:
            self.incoming.put({"type": "chat", "text": obj.value.decode("utf-8")})

        elif obj.type == FILE_META_TYPE:
            meta = json.loads(obj.value.decode("utf-8"))
            self.files_incoming[meta["id"]] = IncomingFile(
                meta["id"], meta["filename"], meta["total_chunks"], meta["size"]
            )

        elif obj.type == FILE_CHUNK_TYPE:
            file_id, index = struct.unpack("!H I", obj.value[:6])
            payload = obj.value[6:]
            f = self.files_incoming.get(file_id)
            if f:
                f.add_chunk(index, payload)
                if f.is_complete():
                    full = f.assemble()
                    safe = secure_filename(f.filename)
                    save_path = self.received_dir / f"{file_id}_{safe}"
                    with open(save_path, "wb") as out:
                        out.write(full)
                    del self.files_incoming[file_id]
                    self.files.append({"name": save_path.name, "display": safe})
                    self.incoming.put({
                        "type": "file",
                        "name": save_path.name,
                        "display": safe,
                        "size": len(full),
                    })

    def send_message(self, text):
        container = ContainerV1(objects=[ObjectV1(type=CHAT_TYPE, id=0, value=text.encode("utf-8"))])
        self.ms.send(self.peer_id, PacketV1.pack(container.encode()))

    def send_file(self, path, filename):
        with open(path, "rb") as f:
            data = f.read()
        file_id = self._next_file_id()
        total = (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE

        meta = json.dumps({
            "id": file_id,
            "filename": filename,
            "total_chunks": total,
            "size": len(data),
        }).encode("utf-8")
        container = ContainerV1(objects=[ObjectV1(type=FILE_META_TYPE, id=0, value=meta)])
        self.ms.send(self.peer_id, PacketV1.pack(container.encode()))

        for i in range(total):
            chunk = data[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE]
            payload = struct.pack("!H I", file_id, i) + chunk
            container = ContainerV1(objects=[ObjectV1(type=FILE_CHUNK_TYPE, id=0, value=payload)])
            self.ms.send(self.peer_id, PacketV1.pack(container.encode()))
            if i % 10 == 0:
                time.sleep(0.001)

        self.incoming.put({"type": "system", "text": f"Archivo enviado: {filename}"})

    def close(self):
        self.ms.close()
