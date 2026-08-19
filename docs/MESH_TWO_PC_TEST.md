# IPv7 Mesh — Prueba entre dos PCs en redes distintas

> Estado: guía para validar IPv7 Mesh v0.1 con NAT real.  
> Fecha: 2026-08-19

---

## Objetivo

Verificar que dos computadoras separadas, cada una con su propia NAT, pueden:

1. Descubrirse por Firebase.
2. Conectarse directamente por UDP cuando sea posible.
3. Caer a DERP/TLS si UDP directo falla.
4. Enviar/recibir mensajes con firma Ed25519 y sin duplicados.

---

## Requisitos

- Ambos PCs con Python 3.11+ y el repositorio clonado.
- Conexión a Internet en ambos PCs.
- `firebase_config.json` válido en ambos PCs (misma base de datos).
- Un relay DERP accesible para ambos PCs.

Opciones de relay:

- **Opción A:** un PC público con IP fija y puerto `47000` abierto.
- **Opción B:** un VPS/cloud con `47000` abierto.
- **Opción C:** para pruebas controladas, usar un tercer PC en la misma red con IP accesible.

---

## Preparar el relay (PC Relay)

Si no hay relay público, correrlo en un tercer PC con IP accesible:

```powershell
python -m experimental.mesh.derp_relay --host 0.0.0.0 --port 47000
```

Obtener la IP pública del relay (por ejemplo `203.0.113.10`) y asegurarse de que el puerto `47000/tcp` esté abierto en el firewall/router.

---

## PC A — primer peer

```powershell
python -m experimental.vpn.web_ui `
    --mesh `
    --mesh-session twopc01 `
    --mesh-node-id a `
    --mesh-peer b `
    --port 9000 `
    --http 8080 `
    --mesh-relay <IP-RELAY>:47000
```

Reemplazar `<IP-RELAY>` por la IP real del relay.

Abrir navegador en `http://127.0.0.1:8080`.

---

## PC B — segundo peer

```powershell
python -m experimental.vpn.web_ui `
    --mesh `
    --mesh-session twopc01 `
    --mesh-node-id b `
    --mesh-peer a `
    --port 9001 `
    --http 8081 `
    --mesh-relay <IP-RELAY>:47000
```

Abrir navegador en `http://127.0.0.1:8081`.

---

## Verificar descubrimiento

En PC A:

```powershell
curl http://127.0.0.1:8080/peers
```

Debería devolver un JSON con el peer `b` y sus datos de endpoint.

En PC B:

```powershell
curl http://127.0.0.1:8081/peers
```

Debería devolver el peer `a`.

---

## Enviar un mensaje de chat

En PC A:

```powershell
$body = '{"text":"hola desde PC A"}'
curl -X POST -H "Content-Type: application/json" -d $body http://127.0.0.1:8080/send
```

---

## Recibir el mensaje en PC B

En PC B, abrir un SSE:

```powershell
curl -N http://127.0.0.1:8081/events
```

Debería aparecer:

```text
data: {"type": "chat", "text": "hola desde PC A"}
```

---

## Transferir un archivo

En PC A:

```powershell
curl -X POST -F "file=@C:\ruta\al\archivo.txt" http://127.0.0.1:8080/upload
```

En PC B, el SSE debería reportar:

```text
data: {"type": "file", "name": "...", "size": 1234}
```

---

## Qué se está probando

| Comportamiento | Cómo se observa |
|----------------|-----------------|
| Descubrimiento | `/peers` devuelve el otro nodo. |
| DERP como fallback | Si UDP directo no funciona, el mensaje llega igual. |
| Sin duplicados | Cada chat aparece una sola vez en `/events`. |
| Firma Ed25519 | El receptor verifica el DID y la firma; mensajes inválidos se descartan. |
| PATH_MTU | Evento `system: PATH_MTU = 1280` (o el valor negociado). |

---

## Solución de problemas

### Los peers no aparecen en `/peers`

- Revisar que ambos usen el mismo `--mesh-session`.
- Verificar `firebase_config.json` y permisos de la base de datos.
- Revisar conectividad a Firebase desde ambos PCs.

### El mensaje no llega

- Verificar que el relay DERP esté accesible: `telnet <IP-RELAY> 47000`.
- Abrir puertos locales `9000/udp` y `9001/udp` en el firewall de Windows.
- Si ambos están bajo NAT simétrico, el tráfico irá por DERP.
- Revisar que el DID del peer se resuelva correctamente en `/peers` (`did:ipv7:...`).

### Duplicados

- Verificar que ambos PCs usen el código con `nonce` y deduplicación (microfase A).

### Error de firma

- El DID del emisor debe coincidir con la clave pública publicada en el tracker.
- Mensajes sin firma válida se descartan silenciosamente.

---

## Notas

- El firewall de Windows puede bloquear UDP; añadir regla para Python.
- Si los dos PCs están en la misma red, el tráfico puede usar IP local (127.0.0.1) y no prueba NAT real.
- Para prueba real de NAT, usar dos redes separadas (por ejemplo: una WiFi y otra 4G/5G).
