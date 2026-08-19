"""
IPv7 — Chat + transferencia de archivos con UI web Flask (experimental).

Cada nodo corre un servidor web local en --http y se comunica con el peer
por UDP a traves del tunel WireGuard.

Uso en PC A:
    python -m experimental.vpn.web_ui --port 9100 --peer 10.7.0.2:9100 --http 8080

Uso en PC B:
    python -m experimental.vpn.web_ui --port 9100 --peer 10.7.0.1:9100 --http 8080

Abrir navegador en http://127.0.0.1:8080
"""

import argparse
import json
import os
import queue
import socket
import struct
import threading
import time
from pathlib import Path

from flask import Flask, request, render_template_string, send_file, jsonify
from werkzeug.utils import secure_filename

from ..container_v1 import ContainerV1, ObjectV1, ContainerError


CHAT_TYPE = 100
FILE_META_TYPE = 101
FILE_CHUNK_TYPE = 102

CHUNK_SIZE = 1200

app = Flask(__name__)

# Configuracion global seteada en main()
chat = None
incoming = queue.Queue()


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


class UdpChat:
    def __init__(self, port, peer_addr, data_dir):
        self.peer_addr = peer_addr
        self.port = port
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.received_dir = self.data_dir / "received"
        self.received_dir.mkdir(exist_ok=True)
        self.uploads_dir = self.data_dir / "uploads"
        self.uploads_dir.mkdir(exist_ok=True)
        self.files_incoming = {}
        self.files = []
        self.file_id_counter = 0
        self.lock = threading.Lock()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
        self.sock.bind(("0.0.0.0", port))

        self.listener = threading.Thread(target=self._receive_loop, daemon=True)
        self.listener.start()

    def _next_file_id(self):
        with self.lock:
            self.file_id_counter += 1
            return self.file_id_counter

    def _send(self, data):
        with self.lock:
            self.sock.sendto(data, self.peer_addr)

    def send_message(self, text):
        container = ContainerV1(objects=[ObjectV1(type=CHAT_TYPE, id=0, value=text.encode("utf-8"))])
        self._send(container.encode())

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
        self._send(container.encode())

        for i in range(total):
            chunk = data[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE]
            payload = struct.pack("!H I", file_id, i) + chunk
            container = ContainerV1(objects=[ObjectV1(type=FILE_CHUNK_TYPE, id=0, value=payload)])
            self._send(container.encode())
            if i % 10 == 0:
                time.sleep(0.001)

        incoming.put({"type": "system", "text": f"Archivo enviado: {filename}"})

    def _receive_loop(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(65535)
            except OSError:
                break
            try:
                container = ContainerV1.decode(data)
                for obj in container.objects:
                    self._handle_object(obj)
            except ContainerError:
                pass

    def _handle_object(self, obj):
        if obj.type == CHAT_TYPE:
            incoming.put({"type": "chat", "text": obj.value.decode("utf-8")})

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
                    incoming.put({
                        "type": "file",
                        "name": save_path.name,
                        "display": safe,
                        "size": len(full),
                    })


INDEX_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>IPv7 Chat</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 20px; background: #111; color: #eee; }
    h1 { font-size: 1.3rem; margin: 0 0 10px; }
    #messages, #files {
      border: 1px solid #444; border-radius: 6px; padding: 10px;
      background: #1a1a1a; height: 300px; overflow-y: auto; margin-bottom: 10px;
    }
    .msg { margin: 4px 0; padding: 6px 8px; background: #222; border-radius: 4px; }
    .msg b { color: #0f0; }
    .system { color: #888; font-style: italic; }
    #inputRow { display: flex; gap: 8px; margin-bottom: 10px; }
    #text { flex: 1; padding: 8px; background: #222; color: #eee; border: 1px solid #444; border-radius: 4px; }
    button { padding: 8px 14px; background: #0a84ff; color: white; border: none; border-radius: 4px; cursor: pointer; }
    button:hover { background: #007aff; }
    #drop {
      border: 2px dashed #555; border-radius: 6px; padding: 20px; text-align: center;
      color: #888; margin-bottom: 10px;
    }
    #drop.dragover { background: #222; border-color: #0a84ff; color: #eee; }
    a { color: #0f0; }
  </style>
</head>
<body>
  <h1>IPv7 Chat & Archivos</h1>
  <p>Peer: <code>{{ peer }}</code> | UDP local: <code>:{{ port }}</code></p>

  <div id="messages"></div>

  <div id="inputRow">
    <input type="text" id="text" placeholder="Escribi un mensaje..." autocomplete="off">
    <button onclick="send()">Enviar</button>
  </div>

  <div id="drop">Arrastra un archivo aqui o hace click para subirlo</div>
  <input type="file" id="file" style="display:none">

  <h3>Archivos recibidos</h3>
  <ul id="files"></ul>

  <script>
    const messages = document.getElementById('messages');
    const text = document.getElementById('text');
    const drop = document.getElementById('drop');
    const fileInput = document.getElementById('file');

    function append(data) {
      const div = document.createElement('div');
      div.className = 'msg' + (data.type === 'system' ? ' system' : '');
      if (data.type === 'chat') div.innerHTML = '<b>peer:</b> ' + escapeHtml(data.text);
      else if (data.type === 'system') div.textContent = data.text;
      else if (data.type === 'file') div.innerHTML = 'Archivo recibido: <a href="/download/' + data.name + '" download>' + escapeHtml(data.display || data.name) + '</a> (' + data.size + ' bytes)';
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    function escapeHtml(s) {
      return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    async function send() {
      const t = text.value.trim();
      if (!t) return;
      await fetch('/send', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text: t})});
      text.value = '';
    }

    text.addEventListener('keydown', (e) => { if (e.key === 'Enter') send(); });

    drop.addEventListener('click', () => fileInput.click());
    drop.addEventListener('dragover', (e) => { e.preventDefault(); drop.classList.add('dragover'); });
    drop.addEventListener('dragleave', () => drop.classList.remove('dragover'));
    drop.addEventListener('drop', (e) => {
      e.preventDefault(); drop.classList.remove('dragover');
      if (e.dataTransfer.files.length) upload(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', () => { if (fileInput.files.length) upload(fileInput.files[0]); });

    async function upload(file) {
      const fd = new FormData();
      fd.append('file', file);
      drop.textContent = 'Subiendo ' + file.name + '...';
      await fetch('/upload', {method: 'POST', body: fd});
      drop.textContent = 'Arrastra un archivo aqui o hace click para subirlo';
    }

    async function loadFiles() {
      const res = await fetch('/files');
      const list = await res.json();
      const ul = document.getElementById('files');
      ul.innerHTML = '';
      for (const f of list) {
        const li = document.createElement('li');
        const display = f.display || f.name;
        li.innerHTML = '<a href="/download/' + f.name + '" download>' + escapeHtml(display) + '</a>';
        ul.appendChild(li);
      }
    }

    const es = new EventSource('/events');
    es.onmessage = (e) => { append(JSON.parse(e.data)); if (e.data.includes('"type":"file"')) loadFiles(); };
    es.onerror = () => append({type: 'system', text: 'Conexion de eventos perdida'});

    loadFiles();
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML, peer=chat.peer_addr, port=chat.port)


@app.route("/send", methods=["POST"])
def send_message():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if text:
        chat.send_message(text)
    return jsonify({"ok": True})


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "empty filename"}), 400
    safe = secure_filename(f.filename)
    path = chat.uploads_dir / f"{int(time.time())}_{safe}"
    f.save(path)
    threading.Thread(target=chat.send_file, args=(path, safe), daemon=True).start()
    return jsonify({"ok": True, "filename": safe})


@app.route("/events")
def events():
    def generator():
        while True:
            try:
                event = incoming.get(timeout=1)
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                yield ":\n\n"  # keep-alive
    return generator(), {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }


@app.route("/files")
def list_files():
    return jsonify(chat.files)


@app.route("/download/<name>")
def download_file(name):
    path = (chat.received_dir / name).resolve()
    if not path.exists() or not str(path).startswith(str(chat.received_dir)):
        return jsonify({"error": "not found"}), 404
    return send_file(path, as_attachment=True)


def main():
    parser = argparse.ArgumentParser(description="IPv7 Web Chat + File Transfer")
    parser.add_argument("--port", type=int, default=9100, help="puerto UDP local")
    parser.add_argument("--peer", required=True, help="ip:puerto del otro nodo")
    parser.add_argument("--http", type=int, default=8080, help="puerto del servidor web")
    parser.add_argument("--data-dir", default="experimental/vpn/web_data", help="directorio para archivos")
    args = parser.parse_args()

    host, port = args.peer.rsplit(":", 1)
    peer_addr = (host, int(port))

    global chat
    chat = UdpChat(args.port, peer_addr, args.data_dir)

    print(f"[web] abrir navegador en http://127.0.0.1:{args.http}")
    app.run(host="127.0.0.1", port=args.http, threaded=True, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
