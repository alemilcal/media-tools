import subprocess
import argparse
import sys
import os
from pathlib import Path

def run_command(cmd):
    """Ejecuta el comando y devuelve el código de salida."""
    try:
        # Usamos lista para evitar problemas con espacios y paréntesis
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("\n[ERROR] No se encontró el ejecutable de FileBot. Revisa la ruta.")
        return 1

def main():
    parser = argparse.ArgumentParser(description="Organizador de series con FileBot")
    parser.add_argument("input", help="Carpeta o archivo de entrada")
    parser.add_argument("-c", "--cartoon", action="store_true", help="Usar destino de dibujos/anime")
    parser.add_argument("-n", "--test_only", action="store_true", help="Solo hacer test, no preguntar para copiar")
    parser.add_argument("-t", "--title", help="Forzar título de búsqueda (query)")
    parser.add_argument("-s", "--season", help="Forzar número de temporada")

    args = parser.parse_args()

    # --- CONFIGURACIÓN DE RUTAS ---
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"[ERROR] La ruta de entrada no existe: {input_path}")
        sys.exit(1)

    if os.name == 'nt': # Windows
        base_output = "E:/transcode/input-cartoon/shows" if args.cartoon else "E:/transcode/input-film/shows"
        filebot_exe = "C:/bin/filebot/filebot.exe"
    else: # Linux
        base_output = "/mnt/e/transcode/input-cartoon/shows" if args.cartoon else "/mnt/e/transcode/input-film/shows"
        filebot_exe = "filebot"

    # --- CONFIGURACIÓN DE FILEBOT ---
    fmt = "{n}/Season {any{s.pad(2)}{episode.season.pad(2)}{'00'}}/{n} {s00e00} {t}"
    
    # Construcción base del comando
    base_cmd = [
        filebot_exe, "-rename", str(input_path),
        "--output", base_output,
        "--format", fmt,
        "--db", "TheMovieDB::TV",
        "-non-strict"
    ]

    if args.title:
        base_cmd.extend(["--q", args.title])
    
    if args.season:
        # Filtro más robusto: si es 0, buscamos temporada 0 o episodios especiales
        if args.season == "0":
            base_cmd.extend(["--filter", "s == 0 || special"])
        else:
            base_cmd.extend(["--filter", f"s == {args.season}"])

    # --- PASO 1: TEST (PREVIEW) ---
    print(f"\n[1/2] EJECUTANDO PREVISUALIZACIÓN (TEST)...")
    print("-" * 50)
    test_cmd = base_cmd + ["--action", "test"]
    exit_code = run_command(test_cmd)

    if exit_code != 0:
        print(f"\n[!] FileBot no pudo identificar los archivos o hubo un error (Code {exit_code}).")
        sys.exit(exit_code)

    if args.test_only:
        print("\nModo test finalizado.")
        sys.exit(0)

    # --- PASO 2: CONFIRMACIÓN ---
    print("-" * 50)
    confirm = input("¿Los nombres son correctos? ¿Proceder con la COPIA? (s/n): ").lower()

    if confirm == 's':
        print(f"\n[2/2] COPIANDO ARCHIVOS...")
        copy_cmd = base_cmd + ["--action", "copy"]
        run_command(copy_cmd)
        print("\n¡Proceso completado!")
    else:
        print("\nOperación cancelada por el usuario.")

if __name__ == "__main__":
    main()