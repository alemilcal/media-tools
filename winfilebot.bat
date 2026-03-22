@echo off
setlocal enabledelayedexpansion

:: Comprobar si se ha pasado una carpeta como argumento
if "%~1"=="" (
    echo [ERROR] Por favor, arrastra una carpeta sobre este archivo .bat o especifica la ruta.
    pause
    exit /b
)

:: Configuración de rutas y parámetros
set "INPUT_DIR=%~1"
set "OUTPUT_DIR=E:\transcode\input-film\shows"
set "FILEBOT_EXE=C:\bin\filebot\filebot.exe"

echo Procesando: "%INPUT_DIR%"
echo Destino:    "%OUTPUT_DIR%"
echo -------------------------------------------------------

:: Ejecución de FileBot
"%FILEBOT_EXE%" -rename "%INPUT_DIR%" ^
 --output "%OUTPUT_DIR%" ^
 --format "{n}/Season {any{s.pad(2)}{episode.season.pad(2)}{'00'}}/{n} {s00e00} {t}" ^
 --db TheMovieDB::TV ^
 -non-strict ^
 --action test

echo -------------------------------------------------------
echo Proceso finalizado.
pause