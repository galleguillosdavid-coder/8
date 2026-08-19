"""
IPv7 — Generador de configuracion WireGuard para 2 peers (experimental).

Genera:
  - un par de claves X25519 por cada peer (via keygen.py, sin `wg.exe`)
  - dos archivos .conf listos para `wireguard.exe /installtunnelservice`
  - dos scripts .bat de doble click (subir/bajar el tunel)

No instala nada. No requiere WireGuard instalado para generar los
archivos; solo se necesita WireGuard instalado para USARLOS
(ejecutar los .bat).

Uso tipico (dos maquinas reales):

    python -m experimental.vpn.generate_configs \\
        --endpoint-a 203.0.113.10:51820 \\
        --endpoint-b 203.0.113.20:51820

Uso tipico (prueba en la misma maquina, dos tuneles locales):

    python -m experimental.vpn.generate_configs --same-machine
"""

import argparse
import os

from .keygen import generate_keypair

CONF_TEMPLATE = """[Interface]
PrivateKey = {private_key}
Address = {address}
ListenPort = {listen_port}

[Peer]
PublicKey = {peer_public_key}
Endpoint = {peer_endpoint}
AllowedIPs = {allowed_ips}
PersistentKeepalive = 25
"""

UP_BAT_TEMPLATE = """@echo off
REM IPv7 experimental - levanta el tunel WireGuard "{tunnel_name}".
REM Requiere WireGuard instalado (https://www.wireguard.com/install/)
REM y permisos de administrador (instala un servicio de Windows).
"%ProgramFiles%\\WireGuard\\wireguard.exe" /installtunnelservice "%~dp0{tunnel_name}.conf"
pause
"""

DOWN_BAT_TEMPLATE = """@echo off
REM IPv7 experimental - baja el tunel WireGuard "{tunnel_name}".
"%ProgramFiles%\\WireGuard\\wireguard.exe" /uninstalltunnelservice "{tunnel_name}"
pause
"""


def _write(path: str, content: str) -> None:
    with open(path, "w", newline="\r\n") as f:
        f.write(content)


def generate(
    outdir: str,
    name_a: str,
    name_b: str,
    address_a: str,
    address_b: str,
    port_a: int,
    port_b: int,
    endpoint_a: str,
    endpoint_b: str,
) -> None:
    os.makedirs(outdir, exist_ok=True)

    key_a = generate_keypair()
    key_b = generate_keypair()

    conf_a = CONF_TEMPLATE.format(
        private_key=key_a.private_b64,
        address=address_a,
        listen_port=port_a,
        peer_public_key=key_b.public_b64,
        peer_endpoint=endpoint_b,
        allowed_ips=address_b.split("/")[0] + "/32",
    )
    conf_b = CONF_TEMPLATE.format(
        private_key=key_b.private_b64,
        address=address_b,
        listen_port=port_b,
        peer_public_key=key_a.public_b64,
        peer_endpoint=endpoint_a,
        allowed_ips=address_a.split("/")[0] + "/32",
    )

    _write(os.path.join(outdir, f"{name_a}.conf"), conf_a)
    _write(os.path.join(outdir, f"{name_b}.conf"), conf_b)

    for name in (name_a, name_b):
        _write(os.path.join(outdir, f"up_{name}.bat"), UP_BAT_TEMPLATE.format(tunnel_name=name))
        _write(os.path.join(outdir, f"down_{name}.bat"), DOWN_BAT_TEMPLATE.format(tunnel_name=name))

    print(f"Generado en: {outdir}")
    print(f"  {name_a}.conf  (Address={address_a}, ListenPort={port_a}, Endpoint del peer={endpoint_b})")
    print(f"  {name_b}.conf  (Address={address_b}, ListenPort={port_b}, Endpoint del peer={endpoint_a})")
    print()
    print("En la maquina A: copiar {0}.conf, up_{0}.bat, down_{0}.bat y hacer doble click en up_{0}.bat".format(name_a))
    print("En la maquina B: copiar {0}.conf, up_{0}.bat, down_{0}.bat y hacer doble click en up_{0}.bat".format(name_b))
    print()
    print(f"Una vez levantado el tunel, A vera a B en {address_b.split('/')[0]} y viceversa.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generar configuracion WireGuard para 2 peers (IPv7 experimental)")
    parser.add_argument("--outdir", default=os.path.join(os.path.dirname(__file__), "generated"))
    parser.add_argument("--name-a", default="ipv7-a")
    parser.add_argument("--name-b", default="ipv7-b")
    parser.add_argument("--subnet", default="10.7.0.0/24", help="Subred interna del tunel")
    parser.add_argument("--port-a", type=int, default=51820)
    parser.add_argument("--port-b", type=int, default=51820)
    parser.add_argument("--endpoint-a", default=None, help="ip_publica_de_A:puerto (para el .conf de B)")
    parser.add_argument("--endpoint-b", default=None, help="ip_publica_de_B:puerto (para el .conf de A)")
    parser.add_argument(
        "--same-machine", action="store_true",
        help="Generar ambos tuneles para probar en la misma maquina via 127.0.0.1 (usa puertos distintos)"
    )
    args = parser.parse_args()

    subnet_base = args.subnet.split("/")[0].rsplit(".", 1)[0]
    address_a = f"{subnet_base}.1/24"
    address_b = f"{subnet_base}.2/24"

    if args.same_machine:
        port_b = args.port_b if args.port_b != args.port_a else args.port_a + 1
        endpoint_a = f"127.0.0.1:{args.port_a}"
        endpoint_b = f"127.0.0.1:{port_b}"
        port_a = args.port_a
    else:
        port_a = args.port_a
        port_b = args.port_b
        endpoint_a = args.endpoint_a or "CAMBIAR_IP_PUBLICA_DE_A:51820"
        endpoint_b = args.endpoint_b or "CAMBIAR_IP_PUBLICA_DE_B:51820"

    generate(
        outdir=args.outdir,
        name_a=args.name_a,
        name_b=args.name_b,
        address_a=address_a,
        address_b=address_b,
        port_a=port_a,
        port_b=port_b,
        endpoint_a=endpoint_a,
        endpoint_b=endpoint_b,
    )


if __name__ == "__main__":
    main()
