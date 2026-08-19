@echo off
REM IPv7 experimental - chat web Flask sobre WireGuard.
REM Requiere que el tunel WireGuard ya este levantado.
cd /d "%~dp0"
set /p PEER="Peer (ip:puerto, ej 10.7.0.2:9100): "
start "" "http://127.0.0.1:8080"
python -m experimental.vpn.web_ui --port 9100 --peer %PEER% --http 8080
