#!/usr/bin/python3
# -*- coding: utf8 -*-

import requests
import os
import sys
import argparse
import re

# Configuración
API_KEY = "Q5i9yCmsFJ41wbXX0zwEECE6y8IrCm18NQeRTgDP7240b503"
SEARCH_URL = "https://api.theporndb.net/scenes"

def limpiar_basura(texto, es_estudio=False):
    if not texto: return ""
    # Convertimos separadores a espacios
    temp = re.sub(r'[\(\)\[\]\._\-]', ' ', texto)
    if es_estudio: return " ".join(temp.split()).strip()

    # Tags de limpieza agresiva
    tags = [
        r'\b\d{3,4}p\b', r'\b(480|720|1080|2160)\b', r'\b\d[kK]\b', 
        r'\bx26[45]\b', r'\bhevc\b', r'\bbrrip\b', r'\bwebrip\b', 
        r'\bq\d{2}\b', r'\bpart\d\b', r'_180_3D_LR', 
        r'\b180x180\b', r'\b3dh\b', r'\b3d\b', r'\blr\b', r'\b180\b', 
        r'\bsbs\b', r'\bvr\b', r'\bfull\b', r'\braw\b'
    ]
    for tag in tags:
        temp = re.sub(tag, '', temp, flags=re.IGNORECASE)
    
    return " ".join(temp.split()).strip()

def extraer_datos_locales(ruta_completa, sitio_forzado=None):
    path_abs = os.path.abspath(ruta_completa)
    nombre_archivo = os.path.basename(path_abs)
    
    # 1. ESTUDIO
    est_orig = sitio_forzado if sitio_forzado else os.path.basename(os.path.dirname(path_abs))
    est_busqueda = limpiar_basura(est_orig, es_estudio=True)
    
    # 2. EXTENSIONES
    match_ext_vid = re.search(r'\.(mp4|mkv|avi|wmv|mov|flv)$', nombre_archivo, flags=re.IGNORECASE)
    ext_video = match_ext_vid.group(0) if match_ext_vid else os.path.splitext(nombre_archivo)[1]
    raw_base_name = nombre_archivo[:nombre_archivo.rfind(ext_video)]
    
    match_tag = re.search(r'\.([a-z0-9]+)$', raw_base_name, flags=re.IGNORECASE)
    tag_tecnico_api = f" [{match_tag.group(1).upper()}]" if match_tag else ""

    # 3. FECHA (Mejorado para YYYYMMDD sin separadores)
    # Buscamos primero YYYYMMDD, luego formatos con separadores
    patron_f = r'\b(\d{4})(\d{2})(\d{2})\b|(\d{4})[\.\-_\s](\d{2})[\.\-_\s](\d{2})|(\d{2})[\.\-_\s](\d{2})[\.\-_\s](\d{4}|\d{2})'
    match_f = re.search(patron_f, raw_base_name)
    
    fecha_norm = None
    pos_fecha = (0, 0)
    if match_f:
        g = match_f.groups()
        pos_fecha = match_f.span()
        if g[0]: # YYYYMMDD
            fecha_norm = f"{g[0]}-{g[1]}-{g[2]}"
        elif g[3]: # YYYY-MM-DD
            fecha_norm = f"{g[3]}-{g[4]}-{g[5]}"
        else: # DD-MM-YYYY
            año = "20"+g[8] if len(g[8])==2 else g[8]
            fecha_norm = f"{año}-{g[7]}-{g[6]}"

    # 4. LIMPIEZA TÍTULO (Quitar estudio y fecha)
    # Quitamos el estudio del nombre
    est_clean = est_busqueda.replace(" ", "")
    tit_temp = re.sub(re.escape(est_clean), '', raw_base_name, flags=re.IGNORECASE)
    tit_temp = re.sub(re.escape(est_busqueda), '', tit_temp, flags=re.IGNORECASE)
    
    # Quitamos la fecha si la encontramos
    if fecha_norm:
        tit_temp = tit_temp[:pos_fecha[0]] + " " + tit_temp[pos_fecha[1]:]

    tit_busqueda = limpiar_basura(tit_temp)
    if len(tit_busqueda) < 3: tit_busqueda = limpiar_basura(raw_base_name)

    return {
        "est_busqueda": est_busqueda,
        "fecha": fecha_norm,
        "tit_busqueda": tit_busqueda,
        "raw_base_name": raw_base_name,
        "original_full_path": path_abs,
        "ext_video": ext_video,
        "tag_tecnico_api": tag_tecnico_api,
        "directorio": os.path.dirname(path_abs)
    }

def realizar_peticion(params):
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(SEARCH_URL, headers=headers, params=params, timeout=12)
        return r.json().get('data', [])
    except: return []

def ejecutar(archivo_input, interactivo=False, renombrar=False, es_vr=False, sitio_forzado=None):
    info = extraer_datos_locales(archivo_input, sitio_forzado)
    print(f"\n[*] ARCHIVO: {info['raw_base_name']}{info['ext_video']}")

    # --- MOTOR DE BÚSQUEDA ---
    print(f"[*] Buscando: Site='{info['est_busqueda']}' | Query='{info['tit_busqueda']}'...", end=' ', flush=True)
    p = {"site": info['est_busqueda'], "q": info['tit_busqueda']}
    if info['fecha']: p["date"] = info['fecha']
    res = realizar_peticion(p)

    if not res:
        print("\n[*] Reintentando sin fecha...", end=' ', flush=True)
        res = realizar_peticion({"site": info['est_busqueda'], "q": info['tit_busqueda']})

    if not res:
        print("\n[*] Reintentando búsqueda global...", end=' ', flush=True)
        res = realizar_peticion({"q": info['tit_busqueda']})

    # RESCATE MANUAL
    while not res and interactivo:
        print("\n" + "!"*30 + " NO HAY RESULTADOS " + "!"*30)
        manual = input("[?] Búsqueda manual (o Enter para salir): ").strip()
        if not manual: break
        res = realizar_peticion({"q": manual})

    if not res: return

    # Selección
    if interactivo:
        print(f"\n[?] Opciones ({len(res)}):")
        print(f"{'#':<3} | {'FECHA':<10} | {'SITIO':<15} | {'ACTRIZ':<18} | {'TÍTULO'}")
        for i, r in enumerate(res[:15]):
            p_ = r.get('performers', [])
            act = p_[0]['name'] if p_ else "N/A"
            sit = r.get('site',{}).get('name','N/A')
            print(f"{i+1:<3} | {r['date']:<10} | {sit[:15]:<15} | {act[:18]:<18} | {r['title']}")
        sel_raw = input("\nSelección (Enter para el 1): ").strip()
        escena = res[int(sel_raw)-1 if sel_raw and sel_raw.isdigit() else 0]
    else:
        escena = res[0]

    # Formateo final
    est_api = escena.get('site', {}).get('name', info['est_busqueda'])
    tit_api = escena.get('title', 'N/A')
    perf = escena.get('performers', [])
    actriz = f" - {perf[0]['name']}" if perf else ""
    tag_vr = "_180_3D_LR" if es_vr else ""

    if renombrar:
        nombre_base_final = re.sub(r'[\\/:*?"<>|]', '', f"{est_api} {escena['date']} {tit_api}{actriz}{info['tag_tecnico_api']}{tag_vr}")
    else:
        nombre_base_final = info['raw_base_name']

    # Imágenes
    img_url = escena.get('image')
    if img_url:
        print(f"[*] Descargando pósters...", end=' ', flush=True)
        img_res = requests.get(img_url, timeout=15)
        ext_img = '.png' if 'png' in img_res.headers.get('Content-Type', '').lower() else '.jpg'
        for suf in ["", "-fanart"]:
            nom_img = f"{nombre_base_final}{suf}{ext_img}"
            with open(os.path.join(info['directorio'], nom_img), 'wb') as f:
                f.write(img_res.content)
        print("OK.")

    if renombrar:
        nueva_ruta = os.path.join(info['directorio'], f"{nombre_base_final}{info['ext_video']}")
        if info['original_full_path'] != nueva_ruta:
            os.rename(info['original_full_path'], nueva_ruta)
            print(f"[OK] Renombrado.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-n", "--rename", action="store_true")
    parser.add_argument("-v", "--vr", action="store_true")
    parser.add_argument("-s", "--site", help="Forzar estudio")
    args = parser.parse_args()
    ejecutar(args.archivo, args.interactive, args.rename, args.vr, args.site)