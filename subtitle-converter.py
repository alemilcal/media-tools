#!/usr/bin/python3
# -*- coding: utf8 -*-


import html
import math
import re
import sys

import numpy as np

# Regex corregidos
RE_TAGS = re.compile(r"\{[^{}]*\}")
RE_ITALIC = re.compile(r"\\i1(?!\d)")


def textClean(text):

    if not text:
        return ""

    r = text
    r = RE_TAGS.sub("", r).strip()
    r = html.unescape(r)

    mojibake_dict = {
        "\u00c3\u2030": "É",
        "\u00c3\u0089": "É",
        "\u00c3\u0081": "Á",
        "\u00c3\u2020": "Á",
        "\u00c3\u008d": "Í",
        "\u00c3\u00ad": "í",
        "\u00c3\u0093": "Ó",
        "\u00c3\u201c": "Ó",
        "\u00c3\u009a": "Ú",
        "\u00c3\u009a": "Ú",
        "\u00c3\u00a1": "á",
        "\u00c3\u00a9": "é",
        "\u00c3\u00ad": "í",
        "\u00c3\u00b3": "ó",
        "\u00c3\u00ba": "ú",
        "\u00c3\u00b1": "ñ",
        "\u00c3\u0091": "Ñ",
        "\u00c2\u00bf": "¿",
        "\u00c2\u00a1": "¡",
        "Ã‰": "É",
        "Ã¡": "á",
        "Ã©": "é",
        "Ã­": "í",
        "Ã³": "ó",
        "Ãº": "ú",
        "Ã±": "ñ",
    }
    for bad, good in mojibake_dict.items():
        r = r.replace(bad, good)  # 5. REPLACEMENTS ORIGINALES
    # Normalizamos comillas tipográficas (abiertas/cerradas) a comillas estándar
    # Usamos los códigos Unicode para asegurar que detecte las comillas "curvas"
    # \u201c y \u201d son las comillas dobles curvas (abrir y cerrar)
    # \u2018 y \u2019 son las comillas simples curvas
    r = r.replace("\ufeff", "")
    r = r.replace("\u201c", '"').replace("\u201d", '"')
    r = r.replace("\u2018", "'").replace("\u2019", "'")
    # También existen estas comillas bajas que se usan a veces:
    r = r.replace("\u201e", '"')
    # Triple punto (elipsis)
    r = r.replace("\u2026", '...')

    # Continuar con el resto...
    r = re.compile(
        r"[\u3040-\u309F\u30A0-\u30FF\u4300-\u9faf\u3000-\u30ff\uff00-\uffff]"
    ).sub("", r)
    r = r.replace("\\n", " ").replace("\\N", " ")
    # Eliminar el espacio entre el número y el símbolo de porcentaje (ej: "10 %" -> "10%")
    r = re.sub(r"(\d+(?:[.,]\d+)?)\s*%", r"\1%", r)

    # 7. ESPACIOS EXTRAS (opcional pero recomendado)
    r = re.sub(r"\s+", " ", r).strip()

    return r


def balancear_texto(texto, limite_max=40):
    # Limpiamos espacios y saltos previos para tener el texto "crudo"
    texto = " ".join(texto.split())
    total_chars = len(texto)

    if total_chars <= limite_max:
        return texto

    # 1. Calculamos cuántas líneas necesitamos
    num_lineas = math.ceil(total_chars / limite_max)
    palabras = texto.split(" ")
    resultado = []

    # 2. Vamos cortando línea a línea buscando simetría (balanceo)
    for i in range(num_lineas - 1):
        if not palabras:
            break

        # Objetivo de caracteres para la línea actual basado en el texto restante
        texto_restante = " ".join(palabras)
        objetivo = len(texto_restante) / (num_lineas - i)

        mejor_corte = 1
        min_dist = float("inf")
        acumulado = 0

        # Probamos posibles puntos de corte evaluando cuál se acerca más al objetivo
        # Dejamos al menos una palabra por cada línea que falte por procesar
        for j in range(len(palabras) - (num_lineas - i - 1)):
            longitud_prueba = acumulado + len(palabras[j])
            dist = abs(longitud_prueba - objetivo)

            if dist <= min_dist:
                min_dist = dist
                mejor_corte = j + 1
            else:
                # Si la distancia empieza a aumentar, hemos pasado el punto óptimo
                break

            # Sumamos longitud de palabra más el espacio para la siguiente iteración
            acumulado = longitud_prueba + 1

        resultado.append(" ".join(palabras[:mejor_corte]))
        palabras = palabras[mejor_corte:]

    # 3. Añadimos las palabras restantes a la última línea
    if palabras:
        resultado.append(" ".join(palabras))

    return "\n".join(resultado)


def time_to_cs(t_str):
    r"""Convierte tiempo ASS a centésimas, respetando el formato original."""
    t_str = t_str.strip().replace(",", ".")
    parts = t_str.split(":")
    h, m = int(parts[0]), int(parts[1])
    s_parts = parts[2].split(".")
    s = int(s_parts[0])
    # Si viene .7 lo convierte en 70, si es .73 se queda en 73
    cs_str = s_parts[1] if len(s_parts) > 1 else "00"
    while len(cs_str) < 2:
        cs_str += "0"
    cs = int(cs_str[:2])
    return (h * 360000) + (m * 6000) + (s * 100) + cs


def cs_to_srt_time(cs):
    r"""Formato SRT estándar HH:MM:SS,mmm"""
    h = cs // 360000
    m = (cs % 360000) // 6000
    s = (cs % 6000) // 100
    ms = (cs % 100) * 10
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def process_text_logic(raw_text, style, style_italic):
    # 1. Limpieza básica de etiquetas para medir longitud real
    clean_text = RE_TAGS.sub("", raw_text).strip()

    # 2. FILTRO: Si está posicionado (\pos o \an) y es muy corto (letras/carteles) -> ELIMINAR
    # if (
    #     ("\\pos" in raw_text or "\\an" in raw_text or "\\p1" in raw_text)
    #     and len(clean_text) <= 3
    # ) or (
    #     clean_text
    #     and all(
    #         (len(w) == 1 and w.isalpha()) or re.fullmatch(r"-?\d+(\.\d+)?", w)
    #         for w in clean_text.split()
    #     )
    # ):
    #     return None
    # 2. FILTRO: Si es un dibujo (\p1), cartel posicionado (\pos) o basura de karaoke
    # Eliminamos si es un comando de dibujo (\p1) o si el texto es posicionado y muy corto
    if "\\p1" in raw_text:
        return None

    if (("\\pos" in raw_text or "\\an" in raw_text) and len(clean_text) <= 3):
        return None

    # Filtro de "basura": si la mayoría de las palabras son letras sueltas o números (dibujos residuales)
    palabras = clean_text.split()
    if palabras:
        es_basura = all(
            len(w) <= 2 or w.isdigit() or re.fullmatch(r"-?\d+(\.\d+)?", w)
            for w in palabras
        )
        if es_basura:
            return None

    # 3. FORMATO: Si tiene \pos, envolver en corchetes
    if "\\pos" in raw_text and len(clean_text) > 0:
        clean_text = f"[{clean_text.upper()}]"

    # 4. CURSIVAS: Por etiqueta o por estilo
    if RE_ITALIC.search(raw_text) or style.lower() in style_italic:
        clean_text = f"<i>{clean_text}</i>"

    # 5. REPLACEMENTS
    text = textClean(clean_text)

    # --- LIMPIEZA DE ESPACIOS PREVIA AL BALANCEO ---
    text = " ".join(text.split())
    # AÑADE ESTAS DOS LÍNEAS AQUÍ PARA QUITAR ESPACIOS EN LOS CORCHETES
    text = text.replace("[ ", "[").replace(" ]", "]")
    # --- LLAMADA A LA FUNCIÓN DE BALANCEO (AQUÍ) ---
    text = balancear_texto(text, 40)

    # 6. MANEJO DE GUIONES (Después del balanceo para que manden)
    text = text.replace(" - ", "\n-").replace(" -", "\n-")

    # Limpieza final: quitamos espacios sobrantes en cada línea individual
    # para no romper los saltos de línea (\n) que acabamos de crear
    text = "\n".join([line.strip() for line in text.split("\n")])

    if text.startswith("- "):
        text = text[0] + text[2:]

    return text if len(text) > 0 else None


def convert_ass_to_srt(input_file, output_file):
    style_italic = set()
    dialogue_data = []

    try:
        with open(input_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        with open(input_file, "r", encoding="latin-1") as f:
            lines = f.readlines()

    italic_idx = -1
    for line in lines:
        line = line.strip()
        if line.lower().startswith("format:"):
            fields = [f.strip().lower() for f in line.split(",")]
            if "italic" in fields:
                italic_idx = fields.index("italic")

        elif line.lower().startswith("style:") and italic_idx != -1:
            parts = line.split(",")
            if parts[italic_idx] != "0":
                style_name = parts[0].split(":")[-1].strip().lower()
                style_italic.add(style_name)

        elif line.lower().startswith("dialogue:"):
            parts = line.split(",", 9)
            if len(parts) < 10:
                continue

            start_cs = time_to_cs(parts[1])
            end_cs = time_to_cs(parts[2])
            if start_cs >= end_cs:
                continue

            processed_text = process_text_logic(parts[9], parts[3], style_italic)

            if processed_text:
                dialogue_data.append(
                    (start_cs, end_cs, parts[3].strip(), processed_text)
                )

    if not dialogue_data:
        return

    # Procesamiento NumPy
    dt = np.dtype([("start", "i8"), ("end", "i8"), ("style", "U30"), ("text", "U512")])
    subs = np.array(dialogue_data, dtype=dt)

    # UNIFICACIÓN (Criterio 1: No contiguos)
    textos_unicos = np.unique(subs["text"])
    res_unificado = []
    for txt in textos_unicos:
        grupo = np.sort(subs[subs["text"] == txt], order="start")
        curr = grupo[0].copy()
        for i in range(1, len(grupo)):
            nxt = grupo[i]
            if (nxt["start"] - curr["end"]) < 10:
                curr["end"] = max(curr["end"], nxt["end"])
            else:
                res_unificado.append(curr)
                curr = nxt.copy()
        res_unificado.append(curr)

    subs = np.array(res_unificado, dtype=dt)
    subs.sort(order="start")

    # # --- NUEVO BLOQUE DE UNIFICACIÓN POR INICIO IDÉNTICO ---
    # res_mismo_inicio = []
    # if len(subs) > 0:
    #     curr = subs[0].copy()
    #     for i in range(1, len(subs)):
    #         nxt = subs[i]
    #         # Si empiezan exactamente en la misma centésima
    #         if nxt["start"] == curr["start"]:
    #             # Unimos los textos con un salto de línea
    #             if nxt["text"] != curr["text"]:
    #                 curr["text"] = f"{curr['text']}\n{nxt['text']}"
    #             # Nos quedamos con el final del que dure más
    #             curr["end"] = max(curr["end"], nxt["end"])
    #         else:
    #             res_mismo_inicio.append(curr)
    #             curr = nxt.copy()
    #     res_mismo_inicio.append(curr)
    #     subs = np.array(res_mismo_inicio, dtype=dt)
    # # --- FIN DEL BLOQUE ---
    # --- NUEVO BLOQUE DE UNIFICACIÓN POR INICIO IDÉNTICO ---
    res_mismo_inicio = []
    if len(subs) > 0:
        curr = subs[0].copy()
        for i in range(1, len(subs)):
            nxt = subs[i]
            if nxt["start"] == curr["start"]:
                if nxt["text"] != curr["text"]:
                    # Detectamos si alguno de los dos era posicionado
                    usa_brackets = curr["text"].startswith("[") or nxt["text"].startswith("[")
                    
                    # Limpiamos los textos de corchetes existentes
                    t1 = curr["text"].strip("[]")
                    t2 = nxt["text"].strip("[]")
                    
                    unificado = f"{t1}\n{t2}"
                    
                    if usa_brackets:
                        # Todo el bloque unificado en MAYÚSCULAS y con un solo juego de corchetes
                        curr["text"] = f"[{unificado.upper()}]"
                    else:
                        curr["text"] = unificado
                        
                curr["end"] = max(curr["end"], nxt["end"])
            else:
                res_mismo_inicio.append(curr)
                curr = nxt.copy()
        res_mismo_inicio.append(curr)
        subs = np.array(res_mismo_inicio, dtype=dt)

    # CLIPPING (Criterio: No solapamiento)
    for i in range(len(subs) - 1):
        #if subs[i]["end"] > subs[i + 1]["start"]:
        #    subs[i]["end"] = subs[i + 1]["start"]
        if subs[i]["end"] >= subs[i + 1]["start"]:
            subs[i]["end"] = min(subs[i]["end"], subs[i + 1]["start"] - 1)
        min_duration = 3 * len(subs[i]["text"])
        if subs[i]["end"] - subs[i]["start"] < min_duration:
            subs[i]["end"] = subs[i]["start"] + min_duration

    # Enforce minimum for the last subtitle
    if len(subs) > 0:
        i = len(subs) - 1
        min_duration = math.ceil(0.3 * len(subs[i]["text"]))
        if subs[i]["end"] - subs[i]["start"] < min_duration:
            subs[i]["end"] = subs[i]["start"] + min_duration

    # DURACIÓN MÍNIMA (Criterio 2: 1cs)
    subs = subs[(subs["end"] - subs["start"]) >= 1]

    # ESCRITURA SRT
    with open(output_file, "w", encoding="utf-8") as f:
        for i, sub in enumerate(subs, 1):
            f.write(
                f"{i}\n{cs_to_srt_time(sub['start'])} --> {cs_to_srt_time(sub['end'])}\n{sub['text']}\n\n"
            )


def convert_srt_to_srt(input_file, output_file):
    style_italic = set()
    dialogue_data = []

    try:
        with open(input_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        with open(input_file, "r", encoding="latin-1") as f:
            lines = f.readlines()

    with open(output_file, "w", encoding="utf-8") as f:
        for line in lines:
            # clean_text = re.sub(r"{[^{]*}", r"", line)
            # clean_text = line
            clean_text = textClean(line)
            f.write(f"{clean_text}\n")


if __name__ == "__main__":
    print(f"Subtitle Converter...")
    if len(sys.argv) < 3:
        print(f"Uso: {sys.argv[0]} <archivo_entrada.ass/srt> <archivo_salida.srt>")
    else:
        print(f'Procesando archivo: "{sys.argv[1]}" --> "{sys.argv[2]}"')
        if sys.argv[1].lower().endswith(".ass") or sys.argv[1].lower().endswith(
            ".ass.bak"
        ):
            print("Convirtiendo ASS a SRT...")
            convert_ass_to_srt(sys.argv[1], sys.argv[2])
        elif sys.argv[1].lower().endswith(".srt") or sys.argv[1].lower().endswith(
            ".srt.bak"
        ):
            print("Convirtiendo SRT a SRT... (limpiando realmente)")
            convert_srt_to_srt(sys.argv[1], sys.argv[2])
        else:
            print("Archivo de entrada no ASS ni STR")
