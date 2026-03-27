import subprocess
import argparse
import sys
import os
from pathlib import Path

def run_filebot(cmd):
    """Ejecuta FileBot y captura la salida."""
    return subprocess.run(cmd, check=False).returncode

def main():
    parser = argparse.ArgumentParser(description="Organizador Pro con FileBot")
    parser.add_argument("input", help="Carpeta de entrada")
    parser.add_argument("-c", "--cartoon", action="store_true", help="Destino: Cartoon/Anime")
    parser.add_argument("-t", "--title", help="Forzar título de búsqueda")
    parser.add_argument("-s", "--season", help="Forzar número de temporada")
    parser.add_argument("-n", "--test", action="store_true", help="Solo modo test")

    args = parser.parse_args()

    # --- CONFIGURACIÓN DE RUTAS ---
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Error: No existe {input_path}")
        sys.exit(1)

    # Rutas según sistema operativo
    if os.name == 'nt':
        base_out = "E:/transcode/input-cartoon/shows" if args.cartoon else "E:/transcode/input-film/shows"
        filebot_exe = "C:/bin/filebot/filebot.exe"
    else:
        base_out = "/mnt/e/transcode/input-cartoon/shows" if args.cartoon else "/mnt/e/transcode/input-film/shows"
        filebot_exe = "filebot"

    # --- LÓGICA DE FORMATO Y FILTRO ---
    # Usamos s == 0 en el filtro por ser lo más compatible con especiales
    fmt = "{n}/Season {any{s.pad(2)}{'00'}}/{n} {s00e00} {t}"
    
    cmd_base = [
        filebot_exe, "-rename", str(input_path),
        "--output", base_out,
        "--format", fmt,
        "--db", "TheMovieDB::TV",
        "-non-strict"
    ]

    if args.title:
        cmd_base.extend(["--q", args.title])
    
    if args.season:
        # Filtro simplificado para evitar que descarte los especiales
        cmd_base.extend(["--filter", f"s == {args.season}"])

    # --- PASO 1: TEST OBLIGATORIO ---
    print(f"\n>>> Lanzando PREVISUALIZACIÓN para: {input_path.name}")
    test_cmd = cmd_base + ["--action", "test"]
    
    res = run_filebot(test_cmd)
    
    if res != 0:
        print(f"\n[!] FileBot falló o no encontró coincidencias (Error {res}).")
        sys.exit(res)

    if args.test:
        print("\nModo test finalizado.")
        sys.exit(0)

    # --- PASO 2: CONFIRMACIÓN DEL USUARIO ---
    print("\n" + "="*50)
    confirmar = input("¿Los nombres de arriba son correctos? ¿COPIAR archivos? (s/n): ").lower()
    
    if confirmar == 's':
        print("\n>>> Procediendo a la COPIA real...")
        copy_cmd = cmd_base + ["--action", "copy"]
        run_filebot(copy_cmd)
        print("\n¡Hecho!")
    else:
        print("\nOperación cancelada.")

if __name__ == "__main__":
    main()