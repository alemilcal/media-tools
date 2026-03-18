#!/bin/bash

# --- CONFIGURACIÓN ---
# Servidor Origen (donde estás ahora)
ORIGEN="$HOME/topflix/"

# Servidor Destino
USUARIO_DESTINO="alewian"  # <--- CAMBIA ESTO (ej: user123)
HOST_DESTINO="bear.seedhost.eu"
DIR_DESTINO="~/downloads/topflix/"

# --- COMANDO RSYNC ---
# -a: Archivo (mantiene permisos y fechas)
# -v: Verbose (muestra lo que hace)
# -z: Comprime durante el envío (ahorra ancho de banda)
# -L: IMPORTANTE: Convierte enlaces simbólicos en archivos reales al copiar
# --delete: Borra en el destino lo que hayas quitado de tus listas .txt
# --progress: Muestra la velocidad y el tiempo restante

echo "=== Iniciando Sincronización Topflix ==="
echo "Origen: $ORIGEN"
echo "Destino: $USUARIO_DESTINO@$HOST_DESTINO:$DIR_DESTINO"
echo "----------------------------------------"

#rsync -avPL --delete --progress \
#rsync -rvLP --size-only --partial \
rsync -crvLP \
    -e "ssh" \
    "$ORIGEN" \
    "$USUARIO_DESTINO@$HOST_DESTINO:$DIR_DESTINO"

echo "----------------------------------------"
echo "=== Sincronización Finalizada ==="
