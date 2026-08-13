@echo off
title Permitir iPhone en Wi-Fi - Carnes Luevanos
net session >nul 2>&1
if not "%errorlevel%"=="0" (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

netsh advfirewall firewall delete rule name="Carnes Luevanos iPhone" >nul 2>&1
netsh advfirewall firewall add rule name="Carnes Luevanos iPhone" dir=in action=allow protocol=TCP localport=5173,8000 profile=any remoteip=LocalSubnet interfacetype=wireless

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$route = Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' ^| Where-Object { $_.NextHop -ne '0.0.0.0' } ^| Sort-Object RouteMetric,InterfaceMetric ^| Select-Object -First 1; if ($route) { Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $route.InterfaceIndex ^| Where-Object { $_.IPAddress -notlike '169.254.*' } ^| Select-Object -First 1 -ExpandProperty IPAddress }"`) do set "WIFI_IP=%%I"
if not defined WIFI_IP set "WIFI_IP=IP-DE-ESTA-PC"

echo.
echo Acceso habilitado para la PWA y la API desde la red Wi-Fi local.
echo Ya puedes abrir http://%WIFI_IP%:5173 desde Safari.
echo.
pause
