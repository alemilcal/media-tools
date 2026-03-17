#!/usr/bin/python3
# -*- coding: utf8 -*-


import os
from pathlib import Path

# --- CONFIGURACIÓN ---
TOPFLIX_BASE = Path.home() / "topflix"

BIBLIOTECAS = {
    "movies.txt": ("/mnt/5plex/MOVIES/movies", "movies"),
    "spanish-movies.txt": ("/mnt/5plex/MOVIES/spanish-movies", "spanish-movies"),
    "shows.txt": ("/mnt/6media/TVSHOW/shows", "shows"),
    "spanish-shows.txt": ("/mnt/6media/TVSHOW/spanish-shows", "spanish-shows"),
}


def obtener_mapa_carpetas(ruta_origen):
    """Crea un diccionario {nombre_minusculas: nombre_real} de una carpeta."""
    ruta = Path(ruta_origen)
    if not ruta.exists():
        return {}
    # Solo mapeamos directorios reales
    return {item.name.lower(): item.name for item in ruta.iterdir() if item.is_dir()}


def preparar_biblioteca():
    print(f"--- Iniciando creación de biblioteca Topflix (Modo Insensible) ---")

    for txt_file, (src_dir, dst_subdir) in BIBLIOTECAS.items():
        txt_path = TOPFLIX_BASE / txt_file
        target_dir = TOPFLIX_BASE / dst_subdir

        if not txt_path.exists():
            print(f"[!] Saltando {txt_file}: No existe en el home.")
            continue

        target_dir.mkdir(parents=True, exist_ok=True)

        # Escaneamos la carpeta de origen una sola vez para ser eficientes
        print(f"\n> Mapeando origen: {src_dir}...")
        mapa_origen = obtener_mapa_carpetas(src_dir)

        print(f"> Procesando {txt_file}...")
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                item_buscado = line.strip()
                if not item_buscado:
                    continue

                # Buscamos el nombre real usando la versión en minúsculas
                nombre_real = mapa_origen.get(item_buscado.lower())

                if nombre_real:
                    source_path = Path(src_dir) / nombre_real
                    link_path = target_dir / nombre_real

                    if not link_path.exists():
                        try:
                            os.symlink(source_path, link_path)
                            print(f"  [OK] Enlazado: {nombre_real}")
                        except Exception as e:
                            print(f"  [ERROR] {nombre_real}: {e}")
                    else:
                        print(f"  [-] Ya existe: {nombre_real}")
                else:
                    print(f"  [FALLO] No encontrado (Mayús/Minús): {item_buscado}")


if __name__ == "__main__":
    preparar_biblioteca()
    print(f"\n--- Proceso finalizado ---")
