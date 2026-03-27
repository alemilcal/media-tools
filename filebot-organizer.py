import subprocess
import argparse
import sys
import os
from pathlib import Path

def run_filebot(cmd):
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Organizador Pro con Lógica de Foro")
    parser.add_argument("input", help="Carpeta de entrada")
    parser.add_argument("-c", "--cartoon", action="store_true", help="Destino Anime")
    parser.add_argument("-t", "--title", help="ID de TMDB o Título")
    parser.add_argument("-s", "--season", help="Forzar temporada (opcional)")

    args = parser.parse_args()
    input_path = Path(args.input).resolve()

    # Configuración de rutas
    base_out = "E:/transcode/input-cartoon/shows" if args.cartoon else "E:/transcode/input-film/shows"
    filebot_exe = "C:/bin/filebot/filebot.exe" if os.name == 'nt' else "filebot"

    # --- FORMATO BASADO EN TU HALLAZGO ---
    # Si es especial -> Season 00 y S00EXX. Si no -> Season XX y SXXEXX.
    fmt = "{n}/{episode.special ? 'Season 00' : 'Season '+s.pad(2)}/{n} {episode.special ? 'S00E'+special.pad(2) : s00e00} {t}"
    
    cmd = [
        filebot_exe, "-rename", str(input_path),
        "--output", base_out,
        "--format", fmt,
        "--db", "TheMovieDB::TV",
        "--lang", "es",
        "-non-strict"
    ]

    if args.title: cmd.extend(["--q", args.title])
    # Importante: Si usamos este formato, el filtro -s debe ser más permisivo
    if args.season: cmd.extend(["--filter", f"s == {args.season}"])

    print(f"\n>>> [TEST] Analizando con formato de foro: {input_path.name}")
    run_filebot(cmd + ["--action", "test"])

    print("\n" + "="*60)
    if input("¿Confirmas la copia? (s/n): ").lower() == 's':
        run_filebot(cmd + ["--action", "copy"])

if __name__ == "__main__":
    main()