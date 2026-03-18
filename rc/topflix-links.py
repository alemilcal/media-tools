#!/usr/bin/python3
# -*- coding: utf8 -*-

import os
import re
import unicodedata
from pathlib import Path

# --- CONFIGURACIÓN ---
TOPFLIX_BASE = Path.home() / "topflix"

BIBLIOTECAS = {
    "cine.txt": (
        [
            "/mnt/5plex/MOVIES/movies",
            "/mnt/5plex/MOVIES/spanish-movies",
            "/mnt/5plex/MOVIES/input/movies",
            "/mnt/5plex/MOVIES/input/spanish-movies",
        ],
        "cine",
    ),
    "tv.txt": (
        [
            "/mnt/6media/TVSHOW/shows",
            "/mnt/6media/TVSHOW/spanish-shows",
            "/mnt/6media/TVSHOW/input/shows",
            "/mnt/6media/TVSHOW/input/spanish-shows",
        ],
        "tv",
    ),
    "anime.txt": (
        ["/mnt/6media/TVSHOW/shows", "/mnt/6media/TVSHOW/input/shows"],
        "anime",
    ),
    "ecchi.txt": (
        ["/mnt/6media/TVSHOW/shows", "/mnt/6media/TVSHOW/input/shows"],
        "ecchi",
    ),
}


def normalizar(texto):
    if not texto:
        return ""
    texto = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"[^a-zA-Z0-9]", "", texto).lower()


def quitar_año(texto):
    return re.sub(r"[\s\(\[\.]+\d{4}[\)\]\s\.]*$", "", texto).strip()


def preparar_biblioteca():
    if not TOPFLIX_BASE.exists():
        print(f"[ERROR] No existe {TOPFLIX_BASE}")
        return

    rutas_para_borrar = []
    print("--- Iniciando Proceso Topflix (Optimizado) ---")

    for txt_file, (src_dirs, dst_subdir) in BIBLIOTECAS.items():
        txt_path = TOPFLIX_BASE / txt_file
        target_dir = TOPFLIX_BASE / dst_subdir
        if not txt_path.exists():
            continue

        print(f"\n> Analizando {txt_file}...")

        # 1. CARGAR BUSQUEDAS DEL TXT (Indexamos lo que queremos)
        busquedas_validas = {}  # {normalizado: linea_original}
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Guardamos tanto el nombre con año como sin año para comparar
                busquedas_validas[normalizar(line)] = line
                busquedas_validas[normalizar(quitar_año(line))] = line

        # 2. BUSCAR SOLO LO NECESARIO EN LOS DISCOS
        enlaces_a_crear = {}  # {nombre_real: ruta_completa}
        encontrados_txt = set()  # Para saber qué del TXT se ha hallado

        for ruta_str in src_dirs:
            if not os.path.exists(ruta_str):
                continue

            print(f"  [...] Revisando: {ruta_str}")
            with os.scandir(ruta_str) as it:
                for entry in it:
                    if entry.is_dir():
                        nombre_disco = entry.name
                        norm_disco_full = normalizar(nombre_disco)
                        norm_disco_sin_año = normalizar(quitar_año(nombre_disco))

                        # ¿Esta carpeta del disco coincide con algo de mi TXT?
                        match = busquedas_validas.get(
                            norm_disco_full
                        ) or busquedas_validas.get(norm_disco_sin_año)

                        if match:
                            if nombre_disco not in enlaces_a_crear:
                                enlaces_a_crear[nombre_disco] = ruta_str
                                encontrados_txt.add(match)

        # 3. CREAR ENLACES
        target_dir.mkdir(parents=True, exist_ok=True)
        for nombre_real, ruta_padre in enlaces_a_crear.items():
            src_path = Path(ruta_padre) / nombre_real
            ln_path = target_dir / nombre_real
            if not ln_path.exists():
                os.symlink(src_path, ln_path)
                print(f"  [+] NUEVO: {nombre_real}")

        # 4. AVISAR DE LO QUE NO SE ENCONTRÓ
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line in encontrados_txt:
                    continue
                print(f"  [?] NO ENCONTRADO: {line}")

        # 5. PASADA FINAL: AUDITORÍA EN CARPETA DE ENLACES
        for item in target_dir.iterdir():
            if item.is_symlink() and item.name not in enlaces_a_crear:
                rutas_para_borrar.append(str(item.absolute()))
                print(f"  [!] SOBRA EN DESTINO: {item.name} (No está en el TXT)")

    # --- RESULTADO FINAL ---
    print("\n" + "=" * 40)
    if rutas_para_borrar:
        print(f"SE HAN DETECTADO {len(rutas_para_borrar)} ENLACES SOBRANTES.")
        print("Para borrarlos, ejecuta el siguiente comando:\n")
        # Generamos el comando con shlex.quote para manejar espacios de forma segura
        comando = "rm -v " + " ".join(shlex.quote(r) for r in rutas_para_borrar)
        print(comando)
    else:
        print("No se han detectado enlaces sobrantes. Todo limpio.")
    print("=" * 40)


if __name__ == "__main__":
    preparar_biblioteca()
    print("\n--- Finalizado ---")
