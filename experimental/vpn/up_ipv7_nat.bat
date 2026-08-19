@echo off
REM IPv7 experimental - levanta tunel con rendezvous NAT via Firebase.
REM Requiere WireGuard instalado, Python en PATH y permisos de administrador.
cd /d "%~dp0"
set /p SESSION="Codigo de sesion (mismo en ambas PCs): "
set /p ROLE="Rol en esta PC (a/b): "
python -m experimental.vpn.nat_setup --session %SESSION% --role %ROLE% --install
pause
