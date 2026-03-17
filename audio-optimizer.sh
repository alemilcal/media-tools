#!/bin/bash

for f in "$@"; do
  [[ "$f" != *.flac ]] && continue

  # Extraer metadatos manualmente (como en tu script original)
  title=$(metaflac --show-tag=title "$f" | cut -d= -f2)
  artist=$(metaflac --show-tag=artist "$f" | cut -d= -f2)
  albumartist=$(metaflac --show-tag=albumartist "$f" | cut -d= -f2)
  album=$(metaflac --show-tag=album "$f" | cut -d= -f2)
  date=$(metaflac --show-tag=date "$f" | cut -d= -f2)
  genre=$(metaflac --show-tag=genre "$f" | cut -d= -f2)
  track=$(metaflac --show-tag=tracknumber "$f" | cut -d= -f2)

  # Si Album Artist está vacío, usar el Artista normal como respaldo
  if [ -z "$albumartist" ]; then
    albumartist="$artist"
  fi

  output="${f%.flac}.m4a"

  echo "Codificando con fdkaac: $f"

  # -dcs: decodifica flac a stdout de forma silenciosa
  # -m 3: Modo VBR 3 (aprox 120-150kbps, excelente calidad)
  # -o: archivo de salida
  flac -dcs "$f" | fdkaac -m 4 \
    --title "$title" \
    --artist "$artist" \
    --album-artist "$albumartist" \
    --album "$album" \
    --date "$date" \
    --genre "$genre" \
    --track "$track" \
    -o "$output" -

done
