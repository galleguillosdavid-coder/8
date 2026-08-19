@echo off
REM IPv7 experimental - chat sobre WireGuard.
REM Requiere que el tunel WireGuard ya este levantado.
cd /d "%~dp0"
set /p PEER="Peer (ip:puerto, ej 10.7.0.2:9100): "
python -m experimental.vpn.chat --port 9100 --peer %PEER%
pause
