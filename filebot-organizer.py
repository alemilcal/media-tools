import subprocess
import argparse
import sys
import os

def run_filebot():
    parser = argparse.ArgumentParser(description="Organizador de series con FileBot")
    parser.add_argument("input", help="Carpeta de entrada")
    parser.add_argument("-c", "--cartoon", action="store_true", help="Usar destino de dibujos/anime")
    parser.add_argument("-n", "--test", action="store_true", help="Modo test (dry run)")
    parser.add_argument("-t", "--title", help="Forzar título de búsqueda")
    parser.add_argument("-s", "--season", help="Forzar número de temporada")

    args = parser.parse_args()

    # --- CONFIGURACIÓN DE RUTAS ---
    # Ajusta estas rutas según tu sistema (puedes usar rutas de Linux si lo usas allí)
    if os.name == 'nt':  # Windows
        base_output = "E:/transcode/input-cartoon/shows" if args.cartoon else "E:/transcode/input-film/shows"
        filebot_exe = "C:/bin/filebot/filebot.exe"
    else:  # Linux/Mac
        base_output = "/mnt/e/transcode/input-cartoon/shows" if args.cartoon else "/mnt/e/transcode/input-film/shows"
        filebot_exe = "filebot"

    # --- CONSTRUCCIÓN DEL FORMATO ---
    # Usamos la expresión que ya sabemos que funciona para Season 00/01
    fmt = "{n}/Season {any{s.pad(2)}{episode.season.pad(2)}{'00'}}/{n} {s00e00} {t}"

    # --- CONSTRUCCIÓN DEL COMANDO ---
    cmd = [
        filebot_exe, "-rename", args.input,
        "--output", base_output,
        "--format", fmt,
        "--db", "TheMovieDB::TV",
        "-non-strict",
        "--action", "test" if args.test else "copy"
    ]

    # Agregar parámetros opcionales si existen
    if args.title:
        cmd.extend(["--q", args.title])
    
    if args.season:
        cmd.extend(["--filter", f"s == {args.season}"])

    # --- EJECUCIÓN ---
    print(f"--- Ejecutando FileBot ---")
    print(f"Entrada: {args.input}")
    print(f"Destino: {base_output}")
    print(f"Acción: {'TEST' if args.test else 'COPY'}")
    if args.title: print(f"Título forzado: {args.title}")
    if args.season: print(f"Temporada forzada: {args.season}")
    print("-" * 30)

    try:
        # shell=False evita que los paréntesis y espacios rompan el comando
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print(f"Error: No se encontró FileBot en {filebot_exe}")
    except subprocess.CalledProcessError as e:
        print(f"Error en la ejecución de FileBot: {e}")

if __name__ == "__main__":
    run_filebot()