#!/bin/bash

# Comprobar si se ha pasado un archivo
if [ -z "$1" ]; then
    echo "Uso: $0 archivo.mkv"
    exit 1
fi

INPUT="$1"
# Cambia la extensión .mkv por .mp4 para el nombre de salida
OUTPUT="${INPUT%.mkv}.mp4"

ffmpeg -n -i "$INPUT" \
  -c copy \
  -map 0:v -map 0:a -sn \
  -movflags +faststart \
  "$OUTPUT"

echo "Proceso finalizado: $OUTPUT"
