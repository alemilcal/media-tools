@echo off
setlocal enabledelayedexpansion

:: Configuración inicial
set "INPUT_DIR="
set "OUTPUT_DIR=E:\transcode\input-film\shows"
set "FILEBOT_EXE=C:\bin\filebot\filebot.exe"
set "ACTION=copy"

:parse
set "arg=%~1"
if "!arg!"=="" goto end_parse

:: Comparaciones usando saltos GOTO para evitar el error de paréntesis
if /i "!arg!"=="-c" (
    set "OUTPUT_DIR=E:\transcode\input-cartoon\shows"
    goto next_arg
)
if /i "!arg!"=="-n" (
    set "ACTION=test"
    goto next_arg
)

:: Si no es un flag, es la ruta de entrada
set "INPUT_DIR=!arg!"

:next_arg
shift
goto parse
:end_parse

:: Verificación de seguridad
if "!INPUT_DIR!"=="" (
    echo [ERROR] No has indicado la carpeta de entrada.
    pause
    exit /b
)

echo -------------------------------------------------------
echo PROCESANDO: "!INPUT_DIR!"
echo DESTINO:    "!OUTPUT_DIR!"
echo ACCION:     !ACTION!
echo -------------------------------------------------------

:: Si es modo COPY, primero forzamos un TEST silencioso para seguridad
if "!ACTION!"=="copy" (
    echo [PREVIEW] Verificando nombres...
    "!FILEBOT_EXE!" -rename "!INPUT_DIR!" --output "!OUTPUT_DIR!" --format "{n}/Season {any{s.pad(2)}{episode.season.pad(2)}{'00'}}/{n} {s00e00} {t}" --db TheMovieDB::TV -non-strict --action test
    
    echo.
    echo -------------------------------------------------------
    echo Si el test anterior es correcto, PULSA UNA TECLA PARA COPIAR.
    echo -------------------------------------------------------
    pause > nul
)

:: Ejecución final de FileBot
"!FILEBOT_EXE!" -rename "!INPUT_DIR!" ^
 --output "!OUTPUT_DIR!" ^
 --format "{n}/Season {any{s.pad(2)}{episode.season.pad(2)}{'00'}}/{n} {s00e00} {t}" ^
 --db TheMovieDB::TV ^
 -non-strict ^
 --action !ACTION!

echo -------------------------------------------------------
echo Proceso finalizado.
pause