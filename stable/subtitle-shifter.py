#!/usr/bin/python3
# -*- coding: utf8 -*-

import argparse
import os
import re


def shift_timestamp(timestamp, offset_ms, is_ass=False):
    """
    Desplaza un timestamp con precisión de milisegundos.
    """
    if is_ass:
        # Formato ASS: H:MM:SS.cc (centesimas)
        h, m, s_cc = timestamp.split(":")
        s, cc = s_cc.split(".")
        total_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(cc) * 10
    else:
        # Formato SRT: HH:MM:SS,mmm (milisegundos)
        h, m, s_mmm = timestamp.split(":")
        s, mmm = s_mmm.split(",")
        total_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(mmm)

    # Aplicar el desplazamiento
    total_ms += offset_ms
    if total_ms < 0:
        total_ms = 0

    # Desglosar el nuevo tiempo
    res_h = total_ms // 3600000
    total_ms %= 3600000
    res_m = total_ms // 60000
    total_ms %= 60000
    res_s = total_ms // 1000
    res_ms = total_ms % 1000

    if is_ass:
        # El formato ASS requiere centésimas (2 dígitos)
        res_cc = res_ms // 10
        return f"{res_h}:{res_m:02d}:{res_s:02d}.{res_cc:02d}"
    else:
        # El formato SRT requiere milisegundos (3 dígitos)
        return f"{res_h:02d}:{res_m:02d}:{res_s:02d},{res_ms:03d}"


def process_subtitles(input_path, offset_ms):
    ext = os.path.splitext(input_path)[1].lower()
    output_path = f"shifted_{os.path.basename(input_path)}"

    # Expresiones regulares para capturar los tiempos
    srt_pattern = r"(\d{2}:\d{2}:\d{2},\d{3})"
    ass_pattern = r"(\d{1,2}:\d{2}:\d{2}\.\d{2})"

    is_ass = ext == ".ass"
    pattern = ass_pattern if is_ass else srt_pattern

    try:
        # Usamos errors='ignore' para evitar problemas con encodings extraños
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Reemplazo de todas las coincidencias usando la función de desplazamiento
        new_content = re.sub(
            pattern, lambda m: shift_timestamp(m.group(1), offset_ms, is_ass), content
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✅ Archivo generado: {output_path}")
        print(f"🕒 Desplazamiento aplicado: {offset_ms} ms")

    except Exception as e:
        print(f"❌ Error procesando el archivo: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Desplazamiento de tiempos en subtítulos (SRT/ASS)."
    )
    parser.add_argument("archivo", help="Ruta del archivo original")
    parser.add_argument(
        "offset",
        type=int,
        help="Desplazamiento en milisegundos (ej: 1000 para +1s, -500 para -0.5s)",
    )

    args = parser.parse_args()

    if os.path.exists(args.archivo):
        process_subtitles(args.archivo, args.offset)
    else:
        print("❌ Error: No se encuentra el archivo especificado.")
