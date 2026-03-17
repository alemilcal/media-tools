#!/usr/bin/python3
# -*- coding: utf8 -*-


import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_OPTIMIZER_PY = os.path.join(BASE_DIR, "video-optimizer.py")


def procesar_directorios(origen_raw, destino_raw, cartoon):

    origen = os.path.abspath(origen_raw)
    destino = os.path.abspath(destino_raw)

    # Verificamos si el directorio de origen existe
    if not os.path.exists(origen):
        print(f"Error: El directorio de origen '{origen}' no existe.")
        return

    # Recorremos el árbol de directorios de origen
    for root, dirs, files in os.walk(origen):
        dirs.sort()
        # 1. Calculamos la ruta relativa respecto al origen para replicarla en el destino
        rel_path = os.path.relpath(root, origen)
        target_dir = os.path.normpath(os.path.join(destino, rel_path))

        # 2. Creamos la carpeta en el destino si no existe
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"Carpeta creada: {target_dir}")

        # 3. Procesamos los archivos
        for nombre_archivo in sorted(files):
            if nombre_archivo.lower().endswith(
                ".mkv"
            ) or nombre_archivo.lower().endswith(".mp4"):
                nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
                if os.path.exists(
                    os.path.join(root, nombre_sin_ext + ".ok")
                ) or os.path.exists(os.path.join(root, nombre_sin_ext + ".err")):
                    continue
                ruta_entrada = os.path.join(root, nombre_archivo)

                nombre_base = os.path.splitext(nombre_archivo)[0]
                subextension = ".q20"
                if cartoon:
                    subextension += ".crt"
                ruta_salida = os.path.join(
                    target_dir, nombre_base + subextension + ".mkv"
                )

                # Definimos la ruta completa del log para no tener dudas
                ruta_log = os.path.join(target_dir, nombre_base + subextension + ".log")

                print(f"Optimizando: {ruta_entrada} -> {ruta_salida}")

                try:
                    with open(ruta_log, "w", encoding="utf-8") as f_log:
                        lista_comando = [
                            sys.executable,
                            VIDEO_OPTIMIZER_PY,
                        ]
                        if cartoon:
                            lista_comando.append("-c")
                        lista_comando.append(ruta_entrada)
                        lista_comando.append(ruta_salida)
                        comando_para_leer = subprocess.list2cmdline(lista_comando)
                        print(f"\nDEBUG - Comando ejecutado:\n{comando_para_leer}\n")
                        subprocess.run(
                            lista_comando,
                            check=True,
                            stdout=f_log,
                            stderr=subprocess.STDOUT,
                            cwd=target_dir,
                        )
                except subprocess.CalledProcessError as e:
                    print(f"Error en {nombre_archivo}. Revisa el log: {ruta_log}")
                except FileNotFoundError:
                    print("Error: No se encontró el optimizador o Python3.")


if __name__ == "__main__":
    # Validamos que se pasen los dos parámetros
    if len(sys.argv) < 3:
        print(
            "Uso: python folder-video-optimizer.py <directorio_origen> <directorio_destino> [-c]"
        )
        print("-c: modo cartoon")
    else:
        dir_1 = sys.argv[1]
        dir_2 = sys.argv[2]
        cartoon = False
        if len(sys.argv) >= 4:
            cartoon = sys.argv[3] == "-c"
        procesar_directorios(dir_1, dir_2, cartoon)
