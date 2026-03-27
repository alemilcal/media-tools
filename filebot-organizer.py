import subprocess
import argparse
import sys
import os
from pathlib import Path

def run_filebot(cmd):
    """Ejecuta FileBot y muestra la salida en tiempo real."""
    # Eliminamos capturas complejas para que veas todo lo que dice FileBot
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

    # Configuración de rutas según SO
    if os.name == 'nt':
        base_out = "E:/transcode/input-cartoon/shows" if args.cartoon else "E:/transcode/input-film/shows"
        filebot_exe = "C:/bin/filebot/filebot.exe"
    else:
        base_out = "/mnt/e/transcode/input-cartoon/shows" if args.cartoon else "/mnt/e/transcode/input-film/shows"
        filebot_exe = "filebot"

    # Formato de salida: Forzamos Season 00 para los especiales
    fmt = "{n}/Season {any{s.pad(2)}{'00'}}/{n} {s00e00} {t}"
    
    cmd_base = [
        filebot_exe, "-rename", str(input_path),
        "--output", base_out,
        "--format", fmt,
        "--db", "TheMovieDB::TV",
        "-non-strict"
    ]

    # Usar ID o Título
    if args.title:
        cmd_base.extend(["--q", args.title])
    
    # Lógica de filtro blindada
    if args.season:
        if args.season == "0":
            # Filtro "Atrapalotodo" para especiales: 
            # Si el episodio es especial O la temporada es 0 O la temporada no es > 0
            cmd_base.extend(["--filter", "special || any{s}{0} == 0"])
        else:
            cmd_base.extend(["--filter", f"s == {args.season}"])

    # --- PASO 1: TEST ---
    print(f"\n>>> [TEST] Analizando carpeta: {input_path.name}")
    print("-" * 60)
    test_cmd = cmd_base + ["--action", "test"]
    res = run_filebot(test_cmd)
    
    # 0 = Éxito, 3 = Parcial, 100+ = No encontrado
    if res not in [0, 3]:
        print(f"\n[!] FileBot no encontró resultados.")
        sys.exit(res)

    if args.test:
        sys.exit(0)

    # --- PASO 2: CONFIRMACIÓN ---
    print("\n" + "="*50)
    confirmar = input("¿Confirmas la operación? (s/n): ").lower()
    
    if confirmar == 's':
        print("\n>>> Copiando archivos reales...")
        copy_cmd = cmd_base + ["--action", "copy"]
        run_filebot(copy_cmd)
        print("\n¡Hecho!")
    else:
        print("\nOperación cancelada.")

if __name__ == "__main__":
    main()