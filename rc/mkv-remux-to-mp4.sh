#!/bin/bash

# Comprobar si se ha pasado un archivo
if [ -z "$1" ]; then
    echo "Uso: $0 archivo.mkv"
    exit 1
fi

INPUT="$1"
# Cambia la extensión .mkv por .mp4 para el nombre de salida
OUTPUTTMP="${INPUT%.mkv}.tmp.mp4"
OUTPUT="${INPUT%.mkv}.mp4"

nice ffmpeg -n -i "$INPUT" \
  -c copy \
  -map 0:v -map 0:a -sn \
  -movflags +faststart \
  "$OUTPUTTMP"

# $? captura el código de salida del último comando (ffmpeg)
if [ $? -eq 0 ]; then
    echo "Conversión exitosa: $OUTPUTTMP"

    # Renombrar el original a .mkv.bak
    if [ ! -f "${INPUT}.bak" ]; then
        mv "$INPUT" "${INPUT}.bak"
        echo "Original renombrado a: ${INPUT}.bak"
    else
        echo "Aviso: El archivo de respaldo ${INPUT}.bak ya existe. No se ha renombrado."
    fi

    mv "$OUTPUTTMP" "$OUTPUT"
    echo "${OUTPUTTMP} renombrado a ${OUTPUT}"

else
    echo "Error: ffmpeg falló o el archivo de salida ya existía. No se ha creado el respaldo."
    exit 1
fi

echo "Proceso finalizado."
