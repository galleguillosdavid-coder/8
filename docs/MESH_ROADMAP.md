# IPv7 — Mesh / VPN Roadmap y Checklist

> Fecha: 2026-08-19
> Estado: Fases 1-5 del mesh implementadas y probadas localmente.

---

## Resumen de lo implementado

### Core del mesh (experimental/mesh/)

- `tracker.py` — control plane en Firebase (STUN, publicación, descubrimiento).
- `derp_relay.py` — relay DERP-like con TLS.
- `derp_client.py` — cliente DERP con TLS.
- `mesh_chat.py` — chat CLI sobre DERP.
- `magic_socket.py` — UDP directo + fallback DERP, PATH_MTU.
- `magic_chat.py` — chat CLI con MagicSocket.
- `magic_chat_web.py` — MagicChat para la web UI.
- `packet_v1.py` — wrapper de integridad SHA-256 sobre ContainerV1.
- `channels.py` — canales lógicos del Core (control, write, etc.).
- `cert_utils.py` — certificado autofirmado para TLS.

### Web UI

- `web_ui.py` soporta modo `--mesh` con tracker, DERP, chat, archivos y lista `/peers`.

### Transporte IPv7

- `ContainerV1`/`ObjectV1` estructural en `experimental/container_v1.py`.
- SHA-256 como objeto adicional de integridad del paquete.
- PATH_DISCOVER / PATH_RESPONSE para negociar `PATH_MTU`.
- Canales lógicos insertados como objeto de control en cada mensaje.

### Identidad

- `MagicChat` genera `did:ipv7:<clave publica>` por nodo.
- El DERP se registra y envía por DID.
- El tracker resuelve `label -> DID`.

### Pruebas que pasaron

```text
OK: DERP relay funciona
[n1] <- n2: hola n1
[a] <- b: hola a
PATH_MTU = 1280
{"type": "chat", "text": "hola b con DID y SHA"}
```

---

## Lo que falta implementar

### 1. Evitar duplicados en MagicSocket

- [ ] `MagicSocket.send()` debe evitar enviar por UDP y DERP al mismo tiempo.
- [ ] Esperar confirmación UDP brevemente antes de fallback, o descartar duplicados en receptor.

### 2. Fragmentación de archivos > PATH_MTU

- [ ] `MagicChat.send_file()` actualmente usa chunks de 1200 bytes.
- [ ] Validar que `PacketV1.pack(Container)` no supere `PATH_MTU` antes de enviar.
- [ ] Si un chunk supera MTU, fragmentar en objetos más pequeños.

### 3. TTL / limpieza de nodos en tracker

- [ ] `tracker.py` no borra entradas expiradas de Firebase.
- [ ] Agregar `DELETE` o `PATCH` para limpiar `stale`/`expired` peers.
- [ ] `list_active_peers()` filtra por `expiry`, pero no borra del RTDB.

### 4. Web UI multi-peer / selección de destino

- [ ] `/send` acepta `peer` dinámico en el body.
- [ ] `MagicChat` soporta múltiples `MagicSocket` (uno por peer).
- [ ] UI dropdown para elegir peer destino sin reiniciar instancia.

### 5. Autenticidad del DID

- [ ] Ahora el DID es `did:ipv7:<public_b64>` pero no se firma nada.
- [ ] Verificar que `public_b64` en tracker coincide con el remitente del DERP.
- [ ] Agregar firma del `Container` para autenticar mensajes (no solo SHA-256).

### 6. Sesiones IPv7 reales

- [ ] `uint32 session_id` (wire format `!I`) del diseño de Core.
- [ ] `ChannelManager` / `SessionManager` de `src/core/` no están conectados al mesh.
- [ ] Reemplazar sesión string de Firebase por `session_id` numérico en `MagicSocket`.

### 7. Path MTU real con múltiples saltos

- [ ] Ahora se negocia con un solo peer.
- [ ] PATH_DISCOVER debería recorrer relays y calcular mínimo real cuando hay A → relay → B.

### 8. DERP multi-relay

- [ ] Descubrir y conectar a varios relays por tracker.
- [ ] Failover entre relays si uno cae.
- [ ] Relay-to-relay forwarding federado.

### 9. Integración con WireGuard

- [ ] `MagicSocket` UDP debería enviar/receive a través del túnel WireGuard.
- [ ] Integrar `wintun` / WireGuard como data plane cifrado.
- [ ] No recrear criptografía VPN desde cero.

### 10. Gateway automático / salida a Internet

- [ ] `nat_setup.py` ya selecciona gateway según disponibilidad.
- [ ] Conectar mesh con gateway para que un peer salga por otro.
- [ ] Evitar routing loops.

### 11. Perfiles reales (chat, file, media)

- [ ] Hoy usamos tipos mágicos 100, 101, 102.
- [ ] Definir `chat_profile.v1`, `file_profile.v1` como objetos declarados en tracker.
- [ ] Registrar perfiles soportados y rechazar tipos desconocidos en UI.

### 12. Audio / video / multimedia

- [ ] No implementado aún.
- [ ] Diseñar `media_profile` con canales de telemetry y streaming.
- [ ] RTP-like sobre Container/Object o canal dedicado.

### 13. Tests reales entre dos PCs

- [ ] Todo probado en una sola máquina.
- [ ] Probar con dos computadoras separadas con NAT distinto.
- [ ] Validar DERP fallback cuando UDP directo no funciona.

### 14. Build y empaquetado

- [ ] `build.py` existe pero no empaqueta el mesh actual.
- [ ] Generar `.exe` con PyInstaller si es necesario.

### 15. Documentación de configuración

- [ ] Ejemplo de `firebase_config.example.json` ya existe.
- [ ] Documentar cómo correr relay, web_ui y peer en distintas máquinas.
- [ ] Instrucciones de línea de comando en `README.md` del mesh.

---

## Checklist de prioridades sugeridas

- [ ] Arreglar duplicados (rápido, alto impacto)
- [ ] Verificar MTU en send (rápido, previene bugs)
- [ ] Limpieza de peers expirados en RTDB (medio)
- [ ] Autenticidad del DID (medio, seguridad)
- [ ] Probar dos PCs (validación real)
- [ ] Web UI multi-peer (funcionalidad)
- [ ] Integrar WireGuard (VPN real)
- [ ] Gateway automático (Internet por peer)
- [ ] Perfiles formales (arquitectura)
- [ ] Multimedia (a futuro)

---

## Notas

- El Core transporta estructura, Profiles aportan semántica. Esta regla se respeta en `ContainerV1` y `channels.py`.
- WireGuard sigue siendo el transporte cifrado; IPv7 funciona como capa de estructura/aplicación sobre él.
- Firebase RTDB es un control plane temporal; a futuro debería migrar a discovery orientado.
