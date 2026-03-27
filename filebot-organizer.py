import subprocess
import argparse
import sys
import os
from pathlib import Path

def run_filebot(cmd):
    """Ejecuta FileBot y muestra la salida en tiempo real."""
    # Usamos shell=False y lista para máxima seguridad con rutas
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Organizador Pro con FileBot")
    parser.add_argument("input", help="Carpeta de entrada")
    parser.add_argument("-c", "--cartoon", action="store_true", help="Destino: Cartoon/Anime")
    parser.add_argument("-t", "--title", help="Forzar título o ID de TMDB")
    parser.add_argument("-s", "--season", help="Forzar número de temporada")
    parser.add_argument("-n", "--test", action="store_true", help="Solo modo test")

    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Error: No existe {input_path}")
        sys.exit(1)

    # Configuración de ejecutables y rutas
    if os.name == 'nt':
        base_out = "E:/transcode/input-cartoon/shows" if args.cartoon else "E:/transcode/input-film/shows"
        filebot_exe = "C:/bin/filebot/filebot.exe"
    else:
        base_out = "/mnt/e/transcode/input-cartoon/shows" if args.cartoon else "/mnt/e/transcode/input-film/shows"
        filebot_exe = "filebot"

    # Formato de salida (Season 00, etc.)
    fmt = "{n}/Season {any{s.pad(2)}{'00'}}/{n} {s00e00} {t}"
    
    cmd_base = [
        filebot_exe, "-rename", str(input_path),
        "--output", base_out,
        "--format", fmt,
        "--db", "TheMovieDB::TV",
        "-non-strict"
    ]

    # Si pasamos un título o ID
    if args.title:
        cmd_base.extend(["--q", args.title])
    
    # Filtro de temporada
    if args.season:
        if args.season == "0":
            # Filtro ultra-flexible para especiales
            cmd_base.extend(["--filter", "s == 0 || special || !regular"])
        else:
            cmd_base.extend(["--filter", f"s == {args.season}"])

    # --- PASO 1: TEST ---
    print(f"\n>>> [TEST] Analizando carpeta: {input_path.name}")
    print("-" * 60)
    test_cmd = cmd_base + ["--action", "test"]
    res = run_filebot(test_cmd)
    
    # 0 = Éxito, 3 = Éxito parcial (algunos archivos no matchearon)
    if res not in [0, 3]:
        print(f"\n[!] FileBot no encontró resultados. Prueba usando el ID de TMDB con -t")
        sys.exit(res)

    if args.test:
        sys.exit(0)

    # --- PASO 2: CONFIRMACIÓN ---
    print("\n" + "="*60)
    confirmar = input("¿Confirmas la operación? (s/n): ").lower()
    
    if confirmar == 's':
        print("\n>>> Ejecutando COPIA real...")
        copy_cmd = cmd_base + ["--action", "copy"]
        run_filebot(copy_cmd)
        print("\n¡Hecho!")
    else:
        print("\nOperación cancelada.")

if __name__ == "__main__":
    main()