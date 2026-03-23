@echo off
setlocal enabledelayedexpansion

:: Configuración inicial
set "INPUT_DIR="
set "OUTPUT_DIR=E:\transcode\input-film\shows"
set "FILEBOT_EXE=C:\bin\filebot\filebot.exe"
set "ACTION=copy"

:: Procesar argumentos uno a uno con SHIFT para no romper las rutas con espacios
:parse
if "%~1"=="" goto end_parse
if /i "%~1"=="-c" (
    set "OUTPUT_DIR=E:\transcode\input-cartoon\shows"
) else if /i "%~1"=="-n" (
    set "ACTION=test"
) else (
    :: %~1 quita las comillas exteriores, pero guarda la ruta completa con sus espacios
    set "INPUT_DIR=%~1"
)
shift
goto parse
:end_parse

:: Comprobar si se ha pasado una carpeta
if "!INPUT_DIR!"=="" (
    echo [ERROR] Por favor, especifica la carpeta de entrada.
    echo Uso: %~n0 [-c para cartoon] [-n para test] "ruta de carpeta"
    pause
    exit /b
)

echo Procesando: "!INPUT_DIR!"
echo Destino:    "!OUTPUT_DIR!"
echo Accion:     !ACTION!
echo -------------------------------------------------------

:: Si es modo copy, hacemos un test previo
if "!ACTION!"=="copy" (
    echo [PREVIEW] Ejecutando test previo...
    "!FILEBOT_EXE!" -rename "!INPUT_DIR!" ^
     --output "!OUTPUT_DIR!" ^
     --format "{n}/Season {any{s.pad(2)}{episode.season.pad(2)}{'00'}}/{n} {s00e00} {t}" ^
     --db TheMovieDB::TV ^
     -non-strict ^
     --action test
    
    echo.
    echo -------------------------------------------------------
    echo Presiona una tecla para confirmar la COPIA REAL...
    echo -------------------------------------------------------
    pause
)

:: Ejecución final
"!FILEBOT_EXE!" -rename "!INPUT_DIR!" ^
 --output "!OUTPUT_DIR!" ^
 --format "{n}/Season {any{s.pad(2)}{episode.season.pad(2)}{'00'}}/{n} {s00e00} {t}" ^
 --db TheMovieDB::TV ^
 -non-strict ^
 --action !ACTION!

echo -------------------------------------------------------
echo Proceso finalizado.
pause