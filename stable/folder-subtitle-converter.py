#!/usr/bin/python3
# -*- coding: utf8 -*-


import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUBTITLE_CONVERTER_PY = os.path.join(BASE_DIR, "subtitle-converter.py")


def procesar_subtitulos(ruta_raiz):
    # Validamos que la ruta existe
    if not os.path.exists(ruta_raiz):
        print(f"Error: La ruta '{ruta_raiz}' no existe.")
        return

    # 1. Obtenemos la carpeta donde está ESTE script que se está ejecutando
    directorio_script = Path(__file__).parent.absolute()

    # Validamos que el convertidor realmente esté ahí antes de seguir
    if not os.path.exists(SUBTITLE_CONVERTER_PY):
        print(f"[!] Error Crítico: No se encuentra '{SUBTITLE_CONVERTER_PY}'")
        return

    # Recorremos recursivamente
    for root, dirs, files in os.walk(ruta_raiz):
        for nombre_archivo in files:
            nombre_lower = nombre_archivo.lower()
            ext_detectada = None

            # Verificamos los tres casos de extensiones permitidas
            if nombre_lower.endswith(".ass"):
                ext_detectada = ".ass"
            elif nombre_lower.endswith(".ass.bak"):
                ext_detectada = ".ass.bak"
            elif nombre_lower.endswith(".srt.bak"):
                ext_detectada = ".srt.bak"

            if ext_detectada:
                # 1. Definimos las rutas completas
                ruta_entrada = os.path.join(root, nombre_archivo)
                # Obtenemos el nombre base quitando la extensión detectada para asegurar salida .srt
                nombre_base = nombre_archivo[: -len(ext_detectada)]
                ruta_srt = os.path.join(root, nombre_base + ".srt")

                print(f"\n--- Procesando: {nombre_archivo} ---")

                try:
                    # 2. Ejecutamos el optimizador con salida en tiempo real
                    proceso = subprocess.Popen(
                        [sys.executable, SUBTITLE_CONVERTER_PY, ruta_entrada, ruta_srt],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                    )

                    # Validamos que stdout no sea None para evitar errores de iteración
                    if proceso.stdout:
                        for linea in proceso.stdout:
                            sys.stdout.write(linea)
                            sys.stdout.flush()

                    proceso.wait()

                    # 3. Si tuvo éxito, verificamos si hay que renombrar
                    if proceso.returncode == 0:
                        print(f"[OK] Generado: {os.path.basename(ruta_srt)}")

                        # Solo si el original era .ass, lo renombramos a .ass.bak
                        if ext_detectada == ".ass":
                            ruta_bak = ruta_entrada + ".bak"
                            # Si ya existe un .bak, lo eliminamos para permitir el renombrado
                            if os.path.exists(ruta_bak):
                                os.remove(ruta_bak)
                            os.rename(ruta_entrada, ruta_bak)
                            print(
                                f"[OK] Original renombrado a: {os.path.basename(ruta_bak)}"
                            )
                    else:
                        print(
                            f"[ERROR] El optimizador falló con código {proceso.returncode}"
                        )

                except Exception as e:
                    print(f"[!] Error inesperado con {nombre_archivo}: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Uso: python3 {sys.argv[0]} <directorio>")
    else:
        procesar_subtitulos(sys.argv[1])
