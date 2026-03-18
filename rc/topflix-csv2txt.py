#!/usr/bin/python3
# -*- coding: utf8 -*-

import csv
import sys
from pathlib import Path


def convertir_csv_a_txt(archivo_csv, archivo_txt):
    ruta_csv = Path(archivo_csv)
    ruta_txt = Path(archivo_txt)

    if not ruta_csv.exists():
        print(f"[ERROR] No se encuentra el archivo: {archivo_csv}")
        return

    encontrados = 0
    try:
        with open(ruta_csv, mode="r", encoding="utf-8-sig") as f_csv:
            # Detectar el separador automáticamente
            sample = f_csv.read(2048)
            f_csv.seek(0)
            dialect = csv.Sniffer().sniff(sample)

            lector = csv.reader(f_csv, dialect)

            # --- SALTAR CABECERA ---
            next(lector, None)

            with open(ruta_txt, mode="w", encoding="utf-8") as f_txt:
                for fila in lector:
                    try:
                        if len(fila) >= 4:
                            titulo = fila[2].strip()
                            año = fila[3].strip()

                            # VALIDACIÓN EXTRA: Solo escribir si el año contiene números
                            # Esto filtra cabeceras si el CSV tuviera varias o formato extraño
                            if titulo and año and any(char.isdigit() for char in año):
                                f_txt.write(f"{titulo} ({año})\n")
                                encontrados += 1
                    except IndexError:
                        continue

        print(f"--- Proceso completado ---")
        print(f"Archivo generado: {archivo_txt}")
        print(f"Total de líneas útiles escritas: {encontrados}")

    except Exception as e:
        print(f"[ERROR] Ocurrió un fallo al procesar el CSV: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 csv_a_txt.py entrada.csv salida.txt")
    else:
        convertir_csv_a_txt(sys.argv[1], sys.argv[2])
