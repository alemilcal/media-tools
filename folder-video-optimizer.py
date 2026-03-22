#!/usr/bin/python3
# -*- coding: utf8 -*-


import argparse
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_OPTIMIZER_PY = os.path.join(BASE_DIR, "video-optimizer.py")


def main():

    global args

    descripcion = "Folder Video Optimizer"
    parser = argparse.ArgumentParser(description=descripcion)
    parser.add_argument("-c", action="store_true", help="cartoon mode")
    parser.add_argument("input", nargs=1, help="input folder")
    parser.add_argument("output", nargs=1, help="output folder")
    args = parser.parse_args()
    print(f"{descripcion}...")
    if len(sys.argv) < 3:
        print(f"Uso: {sys.argv[0]} <directorio_entrada> <directorio_salida>")
    else:
        procesar_directorios(args.input[0], args.output[0], args.c)

import re
import unicodedata
import os

def normalizar_ruta(ruta):
    # 1. Separar la unidad (en Windows) del resto de la ruta
    # Esto protege el "C:" o "E:" para que no se normalice
    drive, resto = os.path.splitdrive(ruta)
    
    # 2. Dividir la ruta en sus partes (carpetas y archivo)
    # Usamos re.split para pillar tanto / como \
    partes = re.split(r'[\\/]', resto)
    partes_limpias = []

    for part in partes:
        if not part: # Saltamos entradas vacías por barras dobles
            partes_limpias.append("")
            continue

        # A. Eliminar paréntesis, corchetes y llaves con su contenido
        p = re.sub(r'\([^)]*\)|\[[^\]]*\]|\{[^}]*\}', '', part)

        # B. Quitar acentos y eñes
        p = unicodedata.normalize('NFD', p)
        p = p.encode('ascii', 'ignore').decode('ascii')

        # C. Minúsculas y cambios básicos
        p = p.lower().replace(' ', '_')

        # D. Solo permitir a-z, 0-9, _, -, .
        p = re.sub(r'[^a-z0-9._-]', '', p)

        # E. LIMPIEZA CRÍTICA: Quitar guiones/puntos sobrantes
        p = p.strip('_- ')      # Quita _ o - al inicio y al final
        p = re.sub(r'_+', '_', p) # Colapsa múltiples ___ en uno
        p = re.sub(r'-+', '-', p) # Colapsa múltiples --- en uno
        
        partes_limpias.append(p)

    # 3. Reconstruir la ruta usando el separador del sistema actual
    ruta_final = drive + os.sep + os.path.join(*partes_limpias)
    
    # 4. Toque final: normpath arregla barras duplicadas o puntos raros
    return os.path.normpath(ruta_final)

def procesar_directorios(origen_raw, destino_raw, cartoon):

    origen = os.path.abspath(origen_raw)
    destino = os.path.abspath(destino_raw)

    # Verificamos si el directorio de origen existe
    if not os.path.exists(origen):
        print(f"Error: El directorio de origen '{origen}' no existe.")
        return

    # Comprobamos si la ruta de origen termina en barra para decidir el destino base
    # Si no termina en barra, añadimos el nombre de la carpeta de origen al destino
    if origen_raw.endswith(os.sep) or (os.altsep and origen_raw.endswith(os.altsep)):
        base_destino = destino
    else:
        base_destino = os.path.join(destino, os.path.basename(origen))

    # Recorremos el árbol de directorios de origen
    for root, dirs, files in os.walk(origen):
        dirs.sort()
        # 1. Calculamos la ruta relativa respecto al origen para replicarla en el destino
        rel_path = os.path.relpath(root, origen)
        target_dir = os.path.normpath(os.path.join(base_destino, rel_path))

        # 2. Creamos la carpeta en el destino si no existe
        # if not os.path.exists(target_dir):
        #     os.makedirs(target_dir)
        #     print(f"Carpeta creada: {target_dir}")

        # 3. Procesamos los archivos
        for nombre_archivo in sorted(files):
            if nombre_archivo.lower().endswith(
                ".mkv"
            ) or nombre_archivo.lower().endswith(".mp4"):                
                nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
                nombre_sin_ext_normalizado = normalizar_ruta(nombre_sin_ext)
                if os.path.exists(
                    os.path.join(root, nombre_sin_ext + ".ok")
                ) or os.path.exists(os.path.join(root, nombre_sin_ext + ".err")):
                    continue
                if os.path.exists(
                    os.path.join(root, nombre_sin_ext_normalizado + ".ok")
                ) or os.path.exists(os.path.join(root, nombre_sin_ext_normalizado + ".err")):
                    continue
                ruta_entrada = os.path.join(root, nombre_archivo)

                nombre_base = os.path.splitext(nombre_archivo)[0]
                subextension = ".q20"
                if cartoon:
                    subextension += ".crt"
                ruta_salida = normalizar_ruta(os.path.join(
                    target_dir, nombre_base + subextension + ".mp4"
                ))

                # Definimos la ruta completa del log para no tener dudas
                ruta_log = normalizar_ruta(os.path.join(target_dir, nombre_base + subextension + ".log"))

                print(f"Optimizando: {ruta_entrada} -> {ruta_salida}")

                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    print(f"Carpeta creada: {target_dir}")

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
                    print(f"Error: No se encontró el optimizador o Python3. Revisa la ruta: {VIDEO_OPTIMIZER_PY}")


if __name__ == "__main__":
    main()
