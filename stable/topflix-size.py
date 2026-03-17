#!/usr/bin/python3
# -*- coding: utf8 -*-


import os
from pathlib import Path

# --- CONFIGURACIÓN ---
TOPFLIX_BASE = Path.home() / "topflix"


def obtener_tamaño_real(ruta):
    """Calcula el tamaño total en bytes de un archivo o carpeta, siguiendo el enlace simbólico."""
    total = 0
    try:
        # Resolvemos el enlace simbólico para obtener la ruta real en /mnt/...
        ruta_real = ruta.resolve()

        if ruta_real.is_file():
            total = ruta_real.stat().st_size
        elif ruta_real.is_dir():
            for dirpath, dirnames, filenames in os.walk(ruta_real):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    # No sumamos si es un enlace simbólico interno para evitar duplicados
                    if not os.path.islink(fp):
                        total += os.path.getsize(fp)
    except Exception as e:
        print(f"  [!] Error calculando tamaño de {ruta.name}: {e}")
    return total


def calcular_espacio_total():
    print(f"--- Calculando espacio real de la biblioteca Topflix ---")
    print(f"(Siguiendo enlaces simbólicos a los discos de montaje)\n")

    total_bytes = 0
    subcarpetas = ["movies", "spanish-movies", "shows", "spanish-shows"]

    for sub in subcarpetas:
        ruta_sub = TOPFLIX_BASE / sub
        if not ruta_sub.exists():
            continue

        print(f"> Analizando sección: {sub}...")
        tamaño_seccion = 0

        # Listamos los enlaces simbólicos dentro de cada subcarpeta
        for item in ruta_sub.iterdir():
            if item.is_symlink():
                tamaño_seccion += obtener_tamaño_real(item)

        gb_seccion = tamaño_seccion / (1024**3)
        print(f"  Subtotal {sub}: {gb_seccion:.2f} GB\n")
        total_bytes += tamaño_seccion

    total_gb = total_bytes / (1024**3)

    print("-" * 40)
    print(f"ESPACIO TOTAL SELECCIONADO: {total_gb:.2f} GB")
    print("-" * 40)


if __name__ == "__main__":
    calcular_espacio_total()
