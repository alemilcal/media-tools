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
    drive, resto = os.path.splitdrive(ruta)
    partes = re.split(r'[\\/]', resto)
    partes_limpias = []

    for i, part in enumerate(partes):
        if not part:
            partes_limpias.append("")
            continue

        # 1. Separar nombre de la extensión (manejando múltiples extensiones)
        # Buscamos el primer punto que no sea un punto al inicio (archivo oculto)
        if "." in part and not part.startswith("."):
            nombre_base = part[:part.find(".")]
            extensiones = part[part.find("."):] # Incluye todos los .q20.crt.mp4
        else:
            nombre_base = part
            extensiones = ""

        # 2. Limpieza del nombre base
        # A. Quitar paréntesis, corchetes y llaves
        n = re.sub(r'\([^)]*\)|\[[^\]]*\]|\{[^}]*\}', '', nombre_base)
        
        # B. Normalizar tildes y eñes
        n = unicodedata.normalize('NFD', n)
        n = n.encode('ascii', 'ignore').decode('ascii').lower()

        # C. EL CAMBIO CLAVE: Colapsar CUALQUIER secuencia de símbolos 
        # (espacios, guiones, guiones bajos) en un único guion bajo
        n = re.sub(r'[\s\-_]+', '_', n)

        # D. Solo permitir letras y números (por si quedaron caracteres raros)
        n = re.sub(r'[^a-z0-9_]', '', n)

        # E. Quitar guiones bajos de los extremos (evita el "_" antes del punto)
        n = n.strip('_')

        # 3. Reensamblar la parte
        partes_limpias.append(n + extensiones)

    # Reconstruir ruta
    ruta_final = drive + os.sep + os.path.join(*partes_limpias)
    return os.path.normpath(ruta_final)

import os
import sys
import subprocess
import re
import unicodedata

def normalizar_ruta(ruta):
    """
    Normaliza una ruta completa: maneja unidad, carpetas y nombre de archivo.
    """
    drive, resto = os.path.splitdrive(ruta)
    partes = re.split(r'[\\/]', resto)
    partes_limpias = []

    for i, part in enumerate(partes):
        if not part:
            if i == 0: partes_limpias.append("") # Manejo de rutas absolutas en Linux
            continue

        # Separamos el nombre de la extensión en el primer punto
        if "." in part and not part.startswith("."):
            nombre_base = part[:part.find(".")]
            extensiones = part[part.find("."):]
        else:
            nombre_base = part
            extensiones = ""

        # Limpieza: paréntesis/corchetes, acentos, minúsculas
        n = re.sub(r'\([^)]*\)|\[[^\]]*\]|\{[^}]*\}', '', nombre_base)
        n = unicodedata.normalize('NFD', n).encode('ascii', 'ignore').decode('ascii').lower()
        
        # Colapsar cualquier combinación de espacios/guiones/underscores en uno solo
        n = re.sub(r'[\s\-_]+', '_', n)
        
        # Quitar underscores de los extremos (evita el "_" antes del punto)
        n = n.strip('_')
        
        partes_limpias.append(n + extensiones)

    ruta_final = drive + os.sep + os.path.join(*partes_limpias)
    return os.path.normpath(ruta_final)

import os
import sys
import subprocess
import re
import unicodedata

def limpiar_texto(texto):
    """Normaliza solo el texto de un nombre de archivo o carpeta."""
    if not texto: return ""
    # 1. Quitar paréntesis, corchetes y llaves
    n = re.sub(r'\([^)]*\)|\[[^\]]*\]|\{[^}]*\}', '', texto)
    # 2. Quitar acentos y eñes
    n = unicodedata.normalize('NFD', n).encode('ascii', 'ignore').decode('ascii').lower()
    # 3. Colapsar espacios/guiones en un solo _ y limpiar bordes
    n = re.sub(r'[\s\-_]+', '_', n).strip('_')
    # 4. Solo permitir a-z, 0-9 y _
    n = re.sub(r'[^a-z0-9_]', '', n)
    return n

def procesar_directorios(origen_raw, destino_raw, cartoon):
    origen = os.path.abspath(origen_raw)
    destino = os.path.abspath(destino_raw)

    if not os.path.exists(origen):
        print(f"Error: El origen '{origen}' no existe.")
        return

    # Determinamos la base del destino
    if origen_raw.endswith(os.sep) or (os.altsep and origen_raw.endswith(os.altsep)):
        base_destino = destino
    else:
        base_destino = os.path.join(destino, limpiar_texto(os.path.basename(origen)))

    for root, dirs, files in os.walk(origen):
        dirs.sort()
        
        # 1. Calculamos la carpeta destino normalizando cada nivel
        rel_path = os.path.relpath(root, origen)
        segmentos_rel = [limpiar_texto(s) for s in rel_path.split(os.sep) if s != "."]
        target_dir = os.path.join(base_destino, *segmentos_rel)

        for nombre_archivo in sorted(files):
            if nombre_archivo.lower().endswith((".mkv", ".mp4")):
                nombre_sin_ext, ext_original = os.path.splitext(nombre_archivo)
                
                # Filtro de archivos ya procesados
                if any(os.path.exists(os.path.join(root, nombre_sin_ext + e)) for e in [".ok", ".err"]):
                    continue

                # 2. Preparamos nombres de salida
                subext = ".q20" + (".crt" if cartoon else "")
                nombre_limpio = limpiar_texto(nombre_sin_ext)
                
                ruta_entrada = os.path.join(root, nombre_archivo)
                # IMPORTANTE: Aquí unimos sin que limpiar_texto añada barras extra
                ruta_salida = os.path.join(target_dir, f"{nombre_limpio}{subext}.mp4")
                ruta_log = os.path.join(target_dir, f"{nombre_limpio}{subext}.log")

                # 3. Crear carpeta solo si hay trabajo que hacer
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir, exist_ok=True)
                    print(f"Carpeta creada: {target_dir}")

                # Elimina el os.path.basename para ver la ruta completa
                print(f"Optimizando: {ruta_entrada} -> {ruta_salida}")
                try:
                    with open(ruta_log, "w", encoding="utf-8") as f_log:
                        lista_comando = [sys.executable, VIDEO_OPTIMIZER_PY]
                        if cartoon: lista_comando.append("-c")
                        lista_comando.extend([ruta_entrada, ruta_salida])

                        subprocess.run(
                            lista_comando,
                            check=True,
                            stdout=f_log,
                            stderr=subprocess.STDOUT,
                            cwd=target_dir
                        )
                except Exception as e:
                    print(f"Error procesando {nombre_archivo}: {e}")

# def procesar_directorios(origen_raw, destino_raw, cartoon):

#     origen = os.path.abspath(origen_raw)
#     destino = os.path.abspath(destino_raw)

#     # Verificamos si el directorio de origen existe
#     if not os.path.exists(origen):
#         print(f"Error: El directorio de origen '{origen}' no existe.")
#         return

#     # Comprobamos si la ruta de origen termina en barra para decidir el destino base
#     # Si no termina en barra, añadimos el nombre de la carpeta de origen al destino
#     if origen_raw.endswith(os.sep) or (os.altsep and origen_raw.endswith(os.altsep)):
#         base_destino = destino
#     else:
#         base_destino = os.path.join(destino, os.path.basename(origen))

#     # Recorremos el árbol de directorios de origen
#     for root, dirs, files in os.walk(origen):
#         dirs.sort()
#         # 1. Calculamos la ruta relativa respecto al origen para replicarla en el destino
#         rel_path = os.path.relpath(root, origen)
#         target_dir = normalizar_ruta(os.path.normpath(os.path.join(base_destino, rel_path)))

#         # 2. Procesamos los archivos
#         for nombre_archivo in sorted(files):
#             if nombre_archivo.lower().endswith(
#                 ".mkv"
#             ) or nombre_archivo.lower().endswith(".mp4"):                
#                 nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
#                 nombre_sin_ext_normalizado = normalizar_ruta(nombre_sin_ext)
#                 if os.path.exists(
#                     os.path.join(root, nombre_sin_ext + ".ok")
#                 ) or os.path.exists(os.path.join(root, nombre_sin_ext + ".err")):
#                     continue
#                 if os.path.exists(
#                     os.path.join(root, nombre_sin_ext_normalizado + ".ok")
#                 ) or os.path.exists(os.path.join(root, nombre_sin_ext_normalizado + ".err")):
#                     continue
#                 ruta_entrada = os.path.join(root, nombre_archivo)

#                 nombre_base = os.path.splitext(nombre_archivo)[0]
#                 subextension = ".q20"
#                 if cartoon:
#                     subextension += ".crt"
#                 ruta_salida = normalizar_ruta(os.path.join(
#                     target_dir, nombre_base + subextension + ".mp4"
#                 ))

#                 # Definimos la ruta completa del log para no tener dudas
#                 ruta_log = normalizar_ruta(os.path.join(target_dir, nombre_base + subextension + ".log"))

#                 print(f"Optimizando: {ruta_entrada} -> {ruta_salida}")

#                 if not os.path.exists(target_dir):
#                     os.makedirs(target_dir)
#                     print(f"Carpeta creada: {target_dir}")

#                 try:
#                     with open(ruta_log, "w", encoding="utf-8") as f_log:
#                         lista_comando = [
#                             sys.executable,
#                             VIDEO_OPTIMIZER_PY,
#                         ]
#                         if cartoon:
#                             lista_comando.append("-c")
#                         lista_comando.append(ruta_entrada)
#                         lista_comando.append(ruta_salida)
#                         comando_para_leer = subprocess.list2cmdline(lista_comando)
#                         print(f"\nDEBUG - Comando ejecutado:\n{comando_para_leer}\n")
#                         subprocess.run(
#                             lista_comando,
#                             check=True,
#                             stdout=f_log,
#                             stderr=subprocess.STDOUT,
#                             cwd=target_dir,
#                         )
#                 except subprocess.CalledProcessError as e:
#                     print(f"Error en {nombre_archivo}. Revisa el log: {ruta_log}")
#                 except FileNotFoundError:
#                     print(f"Error: No se encontró el optimizador o Python3. Revisa la ruta: {VIDEO_OPTIMIZER_PY}")


if __name__ == "__main__":
    main()
