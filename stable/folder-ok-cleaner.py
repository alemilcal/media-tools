#!/usr/bin/python3
# -*- coding: utf8 -*-

import argparse
import os
import shutil
import stat
from pathlib import Path


def handle_remove_readonly(func, path, excinfo):
    """
    Controlador de errores para rmtree en Windows.
    Si un archivo es de solo lectura, le cambia el permiso y reintenta.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        print(f"No se pudo cambiar permisos a {path}: {e}")


def es_borrable(directorio):
    """
    Verifica si el directorio está vacío o solo contiene
    archivos .ok de 0 bytes.
    """
    try:
        items = list(directorio.iterdir())
        if not items:
            return True

        for item in items:
            # Si hay una carpeta, este nivel no se borra todavía
            if item.is_dir():
                return False
            # Solo permitimos archivos .ok de 0 bytes
            if not (item.suffix.lower() == ".ok" and item.stat().st_size == 0):
                return False
        return True
    except (PermissionError, OSError):
        return False


def limpiar_ruta(ruta_base, dry_run=False):
    root = Path(ruta_base).resolve()

    if not root.is_dir():
        print(f"Error: {ruta_base} no es un directorio válido.")
        return

    # Usamos topdown=False para procesar de hijos a padres
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        current_dir = Path(dirpath)

        # 1. REQUISITO NUEVO: Ignorar carpetas ocultas (empiezan por .)
        if current_dir.name.startswith("."):
            continue

        # También ignoramos si alguno de los padres en la ruta es oculto
        # (por ejemplo: /ruta/.config/subcarpeta)
        if any(part.startswith(".") for part in current_dir.relative_to(root).parts):
            continue

        # 2. Calcular profundidad (0=root, 1=primer nivel, 2+=candidatos)
        try:
            profundidad = len(current_dir.relative_to(root).parts)
        except ValueError:
            continue

        # Solo actuar si no es el primer nivel bajo la ruta
        if profundidad > 1:
            if es_borrable(current_dir):
                if dry_run:
                    print(f"[DRY RUN] Se eliminaría: {current_dir}")
                else:
                    try:
                        shutil.rmtree(current_dir, onerror=handle_remove_readonly)
                        print(f"Eliminado: {current_dir}")
                    except Exception as e:
                        print(f"No se pudo eliminar {current_dir}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Limpiador de directorios (Protege carpetas ocultas)."
    )
    parser.add_argument("ruta", help="Ruta base para la limpieza.")
    parser.add_argument(
        "-z",
        "--dry-run",
        action="store_true",
        help="Modo prueba: no borra nada, solo lista.",
    )

    args = parser.parse_args()

    print(f"--- Iniciando limpieza (Respetando carpetas ocultas) ---")
    print(f"Ruta: {args.ruta}")
    if args.dry_run:
        print("MODO: Simulación (Dry Run)")
    print("-" * 50)

    limpiar_ruta(args.ruta, dry_run=args.dry_run)
    print("-" * 50)
    print("Operación completada.")


if __name__ == "__main__":
    main()
