# IPv7 — VPN experimental (WireGuard + IPv7 Container encima)

Decisión (ver conversación / `docs/DESARROLLO_CHECK.md`): no se
reinventa criptografía de transporte propia. Se usa **WireGuard**
(oficial, auditado) como túnel cifrado, y el `Container/Object` de
IPv7 (ya probado, 48/48 tests en `experimental/`) viaja como tráfico
de aplicación **dentro** de ese túnel.

```
Tu app / IPv7 (Container, Object, Identity)   <- ya construido, probado
              |
   tunel cifrado WireGuard (sin modificar)     <- WireGuard resuelve esto
              |
            UDP/IP
```

No se modifica ningun archivo de WireGuard. No se modifica
`ipv7_mvp/` ni `experimental/container_v1.py`.

---

## 0. Instalar WireGuard (una vez, en cada maquina)

Descargar e instalar: https://www.wireguard.com/install/ -> "WireGuard
for Windows". Instalador oficial, un click.

## 1. Generar la configuracion de los 2 peers

Sin necesitar WireGuard instalado (usa solo `cryptography`, ya
disponible en este proyecto):

```bash
# Dos maquinas reales, cada una con su IP publica/alcanzable:
python -m experimental.vpn.generate_configs \
    --endpoint-a <ip_publica_de_A>:51820 \
    --endpoint-b <ip_publica_de_B>:51820

# O para probar en la misma maquina (dos tuneles locales via 127.0.0.1):
python -m experimental.vpn.generate_configs --same-machine
```

Esto genera en `experimental/vpn/generated/`:

```
ipv7-a.conf      up_ipv7-a.bat      down_ipv7-a.bat
ipv7-b.conf      up_ipv7-b.bat      down_ipv7-b.bat
```

**Los `.conf` contienen claves privadas.** No se suben a ningun
repositorio; son secretos de cada maquina.

## 2. Doble click

* En la máquina A: copiar `ipv7-a.conf` + `up_ipv7-a.bat` +
  `down_ipv7-a.bat`, y hacer **doble click en `up_ipv7-a.bat`**
  (pide permisos de administrador: instala un servicio de Windows).
* En la máquina B: lo mismo con los archivos `ipv7-b.*`.

Para bajar el tunel: doble click en `down_ipv7-a.bat` /
`down_ipv7-b.bat`.

## 3. Probar que el tunel funciona

Una vez arriba, A puede alcanzar a B en su IP de tunel (por defecto
`10.7.0.1` y `10.7.0.2`) y viceversa, **cifrado**, sin abrir puertos
adicionales manualmente más allá del puerto UDP de WireGuard.

## 4. IPv7 encima del tunel

Reutilizar `experimental/two_nodes_bench.py` (Container V1, ya
probado) apuntando a la IP de tunel en vez de `127.0.0.1`:

```bash
# En B (dentro del tunel, IP 10.7.0.2):
python -m experimental.two_nodes_bench echo --port 9101

# En A (dentro del tunel, IP 10.7.0.1):
python -m experimental.two_nodes_bench bench --port 9102 --peer-port 9101
# (usar la IP de tunel de B como destino; two_nodes_bench.py asume
#  127.0.0.1 para la prueba local — cambiar peer_addr si se corre
#  entre dos maquinas reales)
```

Los `Container`/`Object` (y, si se quiere, `Identity Proof` de
`experimental/identity/`) viajan sin cambios; WireGuard ya los cifra
a nivel de transporte. IPv7 no necesita su propia capa de cifrado de
sesión para esto — ese trabajo lo hace el túnel.

## Archivos

* `keygen.py` — genera pares de claves X25519 compatibles con
  WireGuard (sin `wg.exe`), usando `cryptography` (ya usada en
  `src/core/network.py` y `experimental/identity/`).
* `test_keygen.py` — 6 tests: formato de claves, roundtrip base64,
  ECDH sanity check (A y B derivan el mismo secreto).
* `generate_configs.py` — genera los `.conf` y los `.bat` de doble
  click para 2 peers.
* `generated/` — (no versionado) salida real con claves privadas;
  se genera localmente, nunca se comitea.

## Que NO se tocó

* El núcleo criptográfico de WireGuard (Noise handshake): no se lee,
  no se modifica, no se reimplementa. Se usa el binario oficial.
* `ipv7_mvp/`, `experimental/container_v1.py`,
  `experimental/identity/`: sin cambios.
