@echo off
setlocal enabledelayedexpansion

:: Configuración inicial
set "INPUT_DIR="
set "OUTPUT_DIR=E:\transcode\input-film\shows"
set "FILEBOT_EXE=C:\bin\filebot\filebot.exe"
set "ACTION=copy"

:: Procesar todos los argumentos
for %%A in (%*) do (
    if "%%A"=="-c" (
        set "OUTPUT_DIR=E:\transcode\input-cartoon\shows"
    ) else if "%%A"=="-n" (
        set "ACTION=test"
    ) else (
        set "INPUT_DIR=%%A"
    )
)

:: Comprobar si se ha pasado una carpeta como argumento
if "!INPUT_DIR!"=="" (
    echo [ERROR] Por favor, especifica la carpeta de entrada.
    echo Uso: %~n0 [-c para cartoon] [-n para test] ^<carpeta^>
    pause
    exit /b
)

echo Procesando: "!INPUT_DIR!"
echo Destino:    "!OUTPUT_DIR!"
echo Accion:     !ACTION!
echo -------------------------------------------------------

:: Ejecución de FileBot
"!FILEBOT_EXE!" -rename "!INPUT_DIR!" ^
 --output "!OUTPUT_DIR!" ^
 --format "{n}/Season {any{s.pad(2)}{episode.season.pad(2)}{'00'}}/{n} {s00e00} {t}" ^
 --db TheMovieDB::TV ^
 -non-strict ^
 --action !ACTION!

echo -------------------------------------------------------
echo Proceso finalizado.
