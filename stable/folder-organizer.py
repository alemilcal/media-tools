#!/usr/bin/python3
# -*- coding: utf8 -*-

import argparse
import os
import re
import shutil
from pathlib import Path


def limpiar_nombre_carpeta(nombre_archivo):
    # Elimina extensiones finales para crear el nombre de la carpeta
    return re.sub(r"(\.[a-zA-Z0-9]{2,6})+$", "", nombre_archivo)


def organizar_peliculas(ruta_base, dry_run):
    path_root = Path(ruta_base).resolve()

    if not path_root.exists():
        print(f"[ERROR] La ruta no existe: {path_root}")
        return

    conteo_items = 0
    conteo_movimientos = 0

    # Lista de nombres que el script debe ignorar para no entrar en bucle
    # (las carpetas de iniciales que vamos creando)
    iniciales_validas = set("abcdefghijklmnopqrstuvwxyz0123456789")
    ignorar = iniciales_validas.union({"0-9", "otros"})

    print(f"--- Modo {'SIMULACIÓN (-n)' if dry_run else 'EJECUCIÓN REAL'} ---")
    print(f"Directorio: {path_root}\n")

    # Listamos todo el contenido de la raíz (archivos y carpetas)
    for item in sorted(path_root.iterdir()):
        # Ignorar archivos ocultos, el propio script y las carpetas de destino A-Z
        if (
            item.name.startswith(".")
            or item.name.lower() in ignorar
            or item.name == "organizar_nas.py"
        ):
            continue

        # --- CASO A: Es un ARCHIVO MKV suelto ---
        if item.is_file() and item.suffix.lower() == ".mkv":
            nombre_carpeta = limpiar_nombre_carpeta(item.name)
            inicial = nombre_carpeta[0].lower()
            if not inicial.isalnum():
                inicial = "otros"

            dir_destino = path_root / inicial / nombre_carpeta
            prefijo = item.stem  # 'Beta (2022).q20'

            # Buscamos todos los archivos que empiecen igual que el MKV
            asociados = [
                f
                for f in path_root.iterdir()
                if f.is_file() and f.name.startswith(prefijo)
            ]

            print(f"[+] Archivo detectado: {item.name} -> {inicial}/{nombre_carpeta}/")
            for f in asociados:
                print(f"    {'[Moviendo]' if not dry_run else '(Simulando)'} {f.name}")
                if not dry_run:
                    dir_destino.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(f), str(dir_destino / f.name))
                conteo_movimientos += 1
            conteo_items += 1

        # --- CASO B: Ya es una CARPETA (como 'Alex (2000)') ---
        elif item.is_dir():
            inicial = item.name[0].lower()
            if not inicial.isalnum():
                inicial = "otros"

            dir_destino_padre = path_root / inicial

            print(f"[+] Carpeta detectada: {item.name} -> {inicial}/{item.name}/")
            if not dry_run:
                dir_destino_padre.mkdir(parents=True, exist_ok=True)
                # Movemos la carpeta completa dentro de la carpeta de la inicial
                try:
                    shutil.move(str(item), str(dir_destino_padre / item.name))
                except Exception as e:
                    print(f"    [!] Error al mover carpeta: {e}")
            else:
                print(f"    (Simulando) Mover carpeta completa")

            conteo_movimientos += 1
            conteo_items += 1

    print("\n" + "=" * 40)
    print(f"RESUMEN FINAL:")
    print(f"Películas/Items procesados: {conteo_items}")
    print(f"Total movimientos realizados/simulados: {conteo_movimientos}")
    print("=" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Organiza películas en carpetas por iniciales."
    )
    parser.add_argument("ruta", help="Ruta donde están los archivos/carpetas")
    parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Simula sin mover nada"
    )

    args = parser.parse_args()
    organizar_peliculas(args.ruta, args.dry_run)
