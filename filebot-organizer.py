import subprocess
import argparse
import sys
import os
from pathlib import Path

def run_filebot(cmd):
    """Ejecuta FileBot y devuelve el código de salida."""
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
        print(f"Error: No existe la ruta {input_path}")
        sys.exit(1)

    if os.name == 'nt': # Windows
        base_out = "E:/transcode/input-cartoon/shows" if args.cartoon else "E:/transcode/input-film/shows"
        filebot_exe = "C:/bin/filebot/filebot.exe"
    else: # Linux
        base_out = "/mnt/e/transcode/input-cartoon/shows" if args.cartoon else "/mnt/e/transcode/input-film/shows"
        filebot_exe = "filebot"

    # --- LÓGICA DE FORMATO Y FILTRO ---
    # Usamos una expresión que cubra todos los casos de Season 0
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
        # Si pides temporada 0, filtramos por lo que NO es regular (especiales)
        # Si pides otra temporada, usamos el número normal
        if args.season == "0":
            cmd_base.extend(["--filter", "!regular || s == 0"])
        else:
            cmd_base.extend(["--filter", f"s == {args.season}"])

    # --- PASO 1: PREVISUALIZACIÓN ---
    print(f"\n>>> [TEST] Analizando: {input_path.name}")
    print("-" * 60)
    
    test_cmd = cmd_base + ["--action", "test"]
    res = run_filebot(test_cmd)
    
    if res != 0:
        print(f"\n[!] FileBot no encontró nada. Prueba cambiando el título con -t")
        sys.exit(res)

    if args.test:
        sys.exit(0)

    # --- PASO 2: CONFIRMACIÓN ---
    print("-" * 60)
    confirmar = input("¿Confirmas la operación? (s/n): ").lower()
    
    if confirmar == 's':
        print("\n>>> Copiando archivos reales...")
        copy_cmd = cmd_base + ["--action", "copy"]
        run_filebot(copy_cmd)
        print("\n¡Completado con éxito!")
    else:
        print("\nOperación cancelada.")

if __name__ == "__main__":
    main()