"""
IPv7 — MagicChat para uso desde la web UI.

Envuelve MagicSocket y ContainerV1 para enviar/recibir chat y archivos.
"""

import asyncio
import base64
import json
import queue
import socket
import struct
import threading
import time
from pathlib import Path

import cryptography.exceptions
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from ..container_v1 import ContainerV1, ObjectV1, ContainerError
from ..vpn.keygen import generate_keypair
from ..vpn.nat_setup import STUN_SERVER, discover_public_endpoint, has_internet
from .cert_utils import CERT_PATH
from .channels import CHANNEL_OBJECT_TYPE, CONTROL, WRITE
from .magic_socket import MagicSocket
from .packet_v1 import PacketV1
from .tracker import list_active_peers, load_firebase_url, publish_node
from werkzeug.utils import secure_filename


CHAT_TYPE = 100
FILE_META_TYPE = 101
FILE_CHUNK_TYPE = 102
PATH_DISCOVER_TYPE = 10
PATH_RESPONSE_TYPE = 11
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
        own_mtu=1280,
    ):
        self.session = session
        self.node_id = node_id
        self.peer_did = peer_id
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
        self.own_mtu = own_mtu
        self.lock = threading.Lock()

        base_url = load_firebase_url()
        try:
            public_endpoint, _ = asyncio.run(discover_public_endpoint(STUN_SERVER))
        except Exception:
            public_endpoint = f"127.0.0.1:{local_port}"
        own_host = public_endpoint.rsplit(":", 1)[0] if ":" in public_endpoint else "127.0.0.1"

        sign_key = Ed25519PrivateKey.generate()
        self._sign_private = sign_key
        self._sign_public = sign_key.public_key()
        self.public_b64 = base64.b64encode(
            self._sign_public.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        ).decode("ascii")
        self.did = f"did:ipv7:{self.public_b64}"
        self.peer_did = peer_id
        info = {
            "id": node_id,
            "did": self.did,
            "public_key": self.public_b64,
            "endpoint": public_endpoint,
            "local_port": local_port,
            "relay_port": peer_relay[1] if peer_relay else 0,
            "mtu": own_mtu,
            "can_gateway": has_internet(),
            "capabilities": ["chat", "file_transfer", "path_mtu"],
            "profiles": ["chat.v1"],
            "availability": "available",
            "truth": "declared",
            "source": node_id,
            "expiry": 3600,
            "timestamp": time.time(),
        }
        publish_node(base_url, session, node_id, info)

        peer_addr, peer_relay, peer_did = self._resolve_peer(
            base_url, session, peer_id, peer_addr, peer_relay, own_host
        )
        if peer_did:
            self.peer_did = peer_did

        use_udp = bool(peer_addr[1])
        self.ms = MagicSocket(
            self.did,
            local_port,
            peer_addr,
            peer_relay=peer_relay,
            peer_id=self.peer_did,
            ca_cert=ca_cert,
            use_udp=use_udp,
        )
        self.ms.on_packet = self._on_packet
        self.ms.connect()
        threading.Thread(target=self._path_mtu_discovery, daemon=True).start()

    @property
    def peer_addr(self):
        return self.ms.peer_addr

    @property
    def port(self):
        return self.ms.local_port

    def _path_mtu_discovery(self):
        for _ in range(30):
            time.sleep(1)
            if self.ms.derp and not self.ms.derp.connected:
                continue
            self.send_path_discover()
            break

    def _public_key_from_did(self, did: str):
        try:
            public_b64 = did.split(":", 2)[2]
            public_bytes = base64.b64decode(public_b64)
            return Ed25519PublicKey.from_public_bytes(public_bytes)
        except Exception:
            return None

    def _send_container(self, container):
        cbytes = container.encode()
        signature = self._sign_private.sign(cbytes)
        self.ms.send(self.peer_did, PacketV1.pack(cbytes, signature))

    def _on_packet(self, src, payload):
        try:
            cbytes, signature = PacketV1.unpack(payload)
            public_key = self._public_key_from_did(src)
            if public_key is None:
                return
            try:
                public_key.verify(signature, cbytes)
            except cryptography.exceptions.InvalidSignature:
                return
            container = ContainerV1.decode(cbytes)
            for obj in container.objects:
                self._handle_object(obj)
        except ContainerError:
            pass

    def send_path_discover(self):
        value = json.dumps({"mtu": self.own_mtu}).encode("utf-8")
        container = ContainerV1(objects=[
            self._channel_object(CONTROL),
            ObjectV1(type=PATH_DISCOVER_TYPE, id=0, value=value),
        ])
        self._send_container(container)

    def send_path_response(self):
        value = json.dumps({"mtu": self.own_mtu}).encode("utf-8")
        container = ContainerV1(objects=[
            self._channel_object(CONTROL),
            ObjectV1(type=PATH_RESPONSE_TYPE, id=0, value=value),
        ])
        self._send_container(container)

    def _resolve_peer(self, base_url, session, peer_id, peer_addr, peer_relay, own_host):
        peer_did = None
        if peer_addr and peer_relay:
            return peer_addr, peer_relay, peer_did
        for _ in range(30):
            time.sleep(1)
            peers = list_active_peers(base_url, session)
            p = peers.get(peer_id)
            if p:
                peer_did = p.get("did", peer_id)
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
        if not peer_did:
            peer_did = peer_id
        return peer_addr, peer_relay, peer_did

    def _next_file_id(self):
        with self.lock:
            self.file_id_counter += 1
            return self.file_id_counter


    def _handle_object(self, obj):
        if obj.type == CHANNEL_OBJECT_TYPE:
            return

        if obj.type == CHAT_TYPE:
            self.incoming.put({"type": "chat", "text": obj.value.decode("utf-8")})

        elif obj.type == PATH_DISCOVER_TYPE:
            self.send_path_response()

        elif obj.type == PATH_RESPONSE_TYPE:
            try:
                peer_mtu = json.loads(obj.value.decode("utf-8")).get("mtu", self.own_mtu)
                mtu = min(self.own_mtu, peer_mtu)
                self.ms.set_mtu(mtu)
                self.incoming.put({"type": "system", "text": f"PATH_MTU = {mtu}"})
            except (json.JSONDecodeError, KeyError):
                pass

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

    def _channel_object(self, channel):
        return ObjectV1(type=CHANNEL_OBJECT_TYPE, id=0, value=bytes([channel]))

    def send_message(self, text):
        container = ContainerV1(objects=[
            self._channel_object(WRITE),
            ObjectV1(type=CHAT_TYPE, id=0, value=text.encode("utf-8")),
        ])
        self._send_container(container)

    def send_file(self, path, filename):
        with open(path, "rb") as f:
            data = f.read()
        file_id = self._next_file_id()
        # El overhead aproximado por chunk es ~56 bytes (Container + Object + PacketV1 + nonce).
        chunk_size = min(CHUNK_SIZE, max(1, self.ms.path_mtu - 60))
        total = (len(data) + chunk_size - 1) // chunk_size

        meta = json.dumps({
            "id": file_id,
            "filename": filename,
            "total_chunks": total,
            "size": len(data),
        }).encode("utf-8")
        container = ContainerV1(objects=[
            self._channel_object(WRITE),
            ObjectV1(type=FILE_META_TYPE, id=0, value=meta),
        ])
        self._send_container(container)

        for i in range(total):
            chunk = data[i * chunk_size:(i + 1) * chunk_size]
            payload = struct.pack("!H I", file_id, i) + chunk
            container = ContainerV1(objects=[
                self._channel_object(WRITE),
                ObjectV1(type=FILE_CHUNK_TYPE, id=0, value=payload),
            ])
            self._send_container(container)
            if i % 10 == 0:
                time.sleep(0.001)

        self.incoming.put({"type": "system", "text": f"Archivo enviado: {filename}"})

    def close(self):
        self.ms.close()
