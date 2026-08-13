@echo off
title Carnes Luevanos - PWA iPhone
cd /d "%~dp0"
set "CODEX_NODE=C:\Users\josss\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin"
set "CODEX_TOOLS=C:\Users\josss\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback"
set "PATH=%CODEX_NODE%;%CODEX_TOOLS%;%PATH%"
set "WRANGLER_LOG_PATH=.wrangler\wrangler-5173.log"
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$route = Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' ^| Where-Object { $_.NextHop -ne '0.0.0.0' } ^| Sort-Object RouteMetric,InterfaceMetric ^| Select-Object -First 1; if ($route) { Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $route.InterfaceIndex ^| Where-Object { $_.IPAddress -notlike '169.254.*' } ^| Select-Object -First 1 -ExpandProperty IPAddress }"`) do set "WIFI_IP=%%I"
if not defined WIFI_IP set "WIFI_IP=localhost"
echo.
echo =====================================================
echo   CARNES LUEVANOS - CONEXION PARA IPHONE
echo =====================================================
echo.
echo Abre en Safari: http://%WIFI_IP%:5173
echo API del sistema: http://%WIFI_IP%:8000
echo.
echo Mantenga esta ventana y el sistema administrativo abiertos.
echo Para detener la conexion presione Ctrl+C.
echo.
if not exist "node_modules\.bin\vinext.cmd" (
  echo Instalando dependencias de la PWA. Esto solo tarda la primera vez...
  call pnpm install --frozen-lockfile
  if errorlevel 1 (
    echo.
    echo No se pudieron instalar las dependencias de la PWA.
    pause
    exit /b 1
  )
)
call node_modules\.bin\vinext.cmd dev --hostname 0.0.0.0 --port 5173
pause
