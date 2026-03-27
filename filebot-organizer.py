import subprocess
import argparse
import sys
import os
from pathlib import Path

def run_filebot(cmd):
    """Ejecuta FileBot y muestra la salida directamente."""
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Organizador Pro FileBot")
    parser.add_argument("input", help="Carpeta de entrada")
    parser.add_argument("-c", "--cartoon", action="store_true", help="Destino: Anime/Cartoon")
    parser.add_argument("-t", "--title", help="Título o ID de TMDB (Ej: 62171)")
    parser.add_argument("-s", "--season", help="Temporada (0 para Especiales)")
    parser.add_argument("-n", "--test", action="store_true", help="Solo test")

    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Error: No existe {input_path}")
        sys.exit(1)

    # Configuración de rutas según SO
    if os.name == 'nt':
        base_out = "E:/transcode/input-cartoon/shows" if args.cartoon else "E:/transcode/input-film/shows"
        filebot_exe = "C:/bin/filebot/filebot.exe"
    else:
        base_out = "/mnt/e/transcode/input-cartoon/shows" if args.cartoon else "/mnt/e/transcode/input-film/shows"
        filebot_exe = "filebot"

    # Formato de salida profesional
    fmt = "{n}/Season {s.pad(2) ?: '00'}/{n} {s00e00} {t}"
    
    # CONSTRUCCIÓN DEL COMANDO PROFESIONAL
    # --lang es: Fundamental para que "Especial" coincida con "Especial"
    # -non-strict: Permite que FileBot ignore el "ruido" de los corchetes
    cmd_base = [
        filebot_exe, "-rename", str(input_path),
        "--output", base_out,
        "--format", fmt,
        "--db", "TheMovieDB::TV",
        "--lang", "es", 
        "-non-strict"
    ]

    # Forzar la búsqueda por ID o título
    search_query = args.title if args.title else input_path.name
    cmd_base.extend(["--q", search_query])
    
    # Filtro de temporada: Si es 0, aceptamos cualquier especial
    if args.season:
        if args.season == "0":
            cmd_base.extend(["--filter", "s == 0 || special || !regular"])
        else:
            cmd_base.extend(["--filter", f"s == {args.season}"])

    # --- PASO 1: TEST ---
    print(f"\n>>> [TEST] Analizando archivos...")
    test_cmd = cmd_base + ["--action", "test"]
    res = run_filebot(test_cmd)
    
    if args.test or res not in [0, 3]:
        sys.exit(res)

    # --- PASO 2: CONFIRMACIÓN ---
    print("\n" + "="*60)
    confirmar = input("¿Confirmas el renombrado y copia? (s/n): ").lower()
    
    if confirmar == 's':
        print("\n>>> Copiando...")
        copy_cmd = cmd_base + ["--action", "copy"]
        run_filebot(copy_cmd)
        print("\n¡Hecho!")

if __name__ == "__main__":
    main()