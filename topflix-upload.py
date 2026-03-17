#!/usr/bin/python3
# -*- coding: utf8 -*-

import os
import re
import subprocess
import sys

# --- CONFIGURACIÓN ---
# Servidor Destino
USUARIO_DESTINO = "alewian"
HOST_DESTINO = "bear.seedhost.eu"
BASE_DIR_DESTINO = "~/downloads/topflix"

# Mapeo de categorías para destino
CATEGORIAS = {"c": "cine", "t": "tv", "a": "anime", "e": "ecchi"}

# Rutas de búsqueda de origen por categoría
RUTAS_ORIGEN = {
    "c": [
        "/mnt/5plex/MOVIES/movies",
        "/mnt/5plex/MOVIES/input",
    ],
    "t": [
        "/mnt/6media/TVSHOW/shows",
        "/mnt/6media/TVSHOW/input",
    ],
    "a": [
        "/mnt/6media/TVSHOW/shows",
        "/mnt/6media/TVSHOW/input",
    ],
    "e": [
        "/mnt/6media/TVSHOW/shows",
        "/mnt/6media/TVSHOW/input",
    ],
}


def main():
    # Validar que al menos se reciba la categoría y una palabra de búsqueda
    if len(sys.argv) < 3:
        print("Uso: topflix-upload.py <categoría_letra> <nombre_carpeta_aproximado...>")
        print("Categorías: c (cine), t (tv), a (anime), e (ecchi)")
        sys.exit(1)

    # 1. Obtener categoría
    letra_cat = sys.argv[1].lower()
    if letra_cat not in CATEGORIAS:
        print(f"Error: Categoría '{letra_cat}' no válida. Use c, t, a o e.")
        sys.exit(1)

    categoria_nombre = CATEGORIAS[letra_cat]
    rutas_busqueda = RUTAS_ORIGEN[letra_cat]

    # 2. Obtener nombre aproximado (todos los parámetros restantes)
    palabras_busqueda = sys.argv[2:]

    # 3. Localizar la carpeta aproximada (mismo orden, case-insensitive)
    # Construimos un patrón regex que busque las palabras en orden con cualquier cosa entre ellas
    patron_regex = ".*".join(map(re.escape, palabras_busqueda))
    try:
        regex = re.compile(patron_regex, re.IGNORECASE)
    except re.error:
        print("Error: Los términos de búsqueda contienen caracteres no permitidos.")
        sys.exit(1)

    carpeta_encontrada = None
    origen_rsync = None

    try:
        # Buscamos en cada uno de los directorios de origen asignados a la categoría
        for ruta_base in rutas_busqueda:
            if not os.path.isdir(ruta_base):
                continue

            # Listamos los elementos del directorio
            for nombre in os.listdir(ruta_base):
                ruta_completa_item = os.path.join(ruta_base, nombre)
                # Solo buscamos directorios que coincidan con el patrón
                if os.path.isdir(ruta_completa_item) and regex.search(nombre):
                    carpeta_encontrada = nombre
                    origen_rsync = ruta_completa_item
                    break

            # Si ya lo encontramos en una ruta, no seguimos buscando en las demás
            if carpeta_encontrada:
                break
    except Exception as e:
        print(f"Error al leer los directorios de origen: {e}")
        sys.exit(1)

    if not carpeta_encontrada:
        print(
            f"Error: No se encontró ninguna carpeta que coincida con '{' '.join(palabras_busqueda)}' en las rutas de origen para {categoria_nombre}."
        )
        sys.exit(1)

    # 4. Ejecutar RSYNC
    # Rutas para el comando
    destino_rsync = (
        f"{USUARIO_DESTINO}@{HOST_DESTINO}:{BASE_DIR_DESTINO}/{categoria_nombre}/"
    )

    print("=== Iniciando Sincronización Topflix ===")
    print(f"Carpeta localizada: {carpeta_encontrada}")
    print(f"Origen: {origen_rsync}")
    print(f"Destino: {destino_rsync}")
    print("----------------------------------------")

    # Comando rsync solicitado: -crvLP
    # -c: Checksum (ignora fechas, usa contenido)
    # -r: Recurrente
    # -v: Verbose
    # -L: Copia el contenido de los enlaces simbólicos
    # -P: Progreso y transferencias parciales
    comando = [
        "rsync",
        "-crvLP",
        "--bwlimit=8M",
        "-e",
        "ssh",
        origen_rsync,
        destino_rsync,
    ]

    try:
        subprocess.run(comando, check=True)
        print("----------------------------------------")
        print("=== Sincronización Finalizada ===")
    except subprocess.CalledProcessError as e:
        print(f"Error durante la ejecución de rsync: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: No se encontró el comando 'rsync' en el sistema.")
        sys.exit(1)


if __name__ == "__main__":
    main()
