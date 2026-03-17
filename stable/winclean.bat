@echo off
setlocal enabledelayedexpansion

:: --- CONFIGURACION ---
set "PATH_EXE=C:\Program Files\Transmission"
set "DESTINO=E:\SYNC"
set "AUTH=raptor:DaqhbmKYrKAX"
:: Dias limite (4 semanas = 28 dias)
set "DIAS=28"

echo === INICIANDO LIMPIEZA POR ANTIGUEDAD (28 DIAS) ===

cd /d "%PATH_EXE%"

:: 1. Sacamos los IDs de los torrents
for /f "tokens=1" %%i in ('transmission-remote.exe -n %AUTH% -l ^| findstr /R "^[ ]*[0-9]"') do (
    set "ID=%%i"
    set "FECHA="
    set "DIR="
    set "NOMBRE="

    :: 2. Capturamos la fecha de añadido, la ruta y el nombre
    for /f "tokens=2*" %%f in ('transmission-remote.exe -n %AUTH% -t !ID! -i ^| findstr /C:"Date added:"') do set "FECHA=%%g"
    for /f "tokens=2*" %%l in ('transmission-remote.exe -n %AUTH% -t !ID! -i ^| findstr /C:"Location:"') do set "DIR=%%m"
    for /f "tokens=2*" %%n in ('transmission-remote.exe -n %AUTH% -t !ID! -i ^| findstr /C:"Name:"') do set "NOMBRE=%%o"

    :: 3. Verificamos si la fecha cumple los 28 dias usando un calculo rapido
    if not "!FECHA!"=="" (
        :: Esta linea hace el calculo y devuelve 1 si es antiguo, 0 si es nuevo
        powershell -NoProfile -Command "if ((Get-Date) - (Get-Date '!FECHA!') -ge [TimeSpan]::FromDays(%DIAS%)) { exit 1 } else { exit 0 }" >nul 2>&1

        if !errorlevel! equ 1 (
            echo.
            echo [CUMPLE] ID: !ID! - !NOMBRE!
            echo Añadido el: !FECHA! (Hace mas de %DIAS% dias)

            :: --- ACCIONES REALES ---
            echo [1/2] Moviendo a %DESTINO%...
            move "!DIR!\!NOMBRE!" "%DESTINO%\" >nul

            echo [2/2] Quitante de Transmission...
            transmission-remote.exe -n %AUTH% -t !ID! -r

            echo [OK] Completado.
        ) else (
            echo [IGNORADO] ID: !ID! - !NOMBRE! (Aun es reciente)
        )
    )
)

echo.
echo === PROCESO FINALIZADO ===
pause
