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
    # Convertimos separadores a espacios para detectar tags como palabras sueltas
    temp = re.sub(r'[\(\)\[\]\._\-]', ' ', texto)
    if es_estudio: return " ".join(temp.split()).strip()

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
    estudio_raw = sitio_forzado if sitio_forzado else os.path.basename(os.path.dirname(path_abs))
    estudio_busqueda = limpiar_basura(estudio_raw, es_estudio=True)
    
    # 2. EXTENSIÓN DE VIDEO Y NOMBRE BASE ORIGINAL
    match_ext_vid = re.search(r'\.(mp4|mkv|avi|wmv|mov|flv)$', nombre_archivo, flags=re.IGNORECASE)
    ext_video = match_ext_vid.group(0) if match_ext_vid else os.path.splitext(nombre_archivo)[1]
    
    # raw_base_name es el nombre del archivo SIN la extensión (.mp4)
    raw_base_name = nombre_archivo[:nombre_archivo.rfind(ext_video)]
    
    # Identificamos etiqueta tipo .q20 para el renombrado
    match_tag = re.search(r'\.([a-z0-9]+)$', raw_base_name, flags=re.IGNORECASE)
    tag_tecnico_api = f" [{match_tag.group(1).upper()}]" if match_tag else ""

    # 3. LIMPIEZA PARA BÚSQUEDA
    # Quitar el estudio del nombre para la query
    est_clean = estudio_busqueda.replace(" ", "")
    tit_temp = re.sub(re.escape(est_clean), '', raw_base_name, flags=re.IGNORECASE)
    tit_temp = re.sub(re.escape(estudio_busqueda), '', tit_temp, flags=re.IGNORECASE)
    tit_busqueda = limpiar_basura(tit_temp)
    
    if len(tit_busqueda) < 3: tit_busqueda = limpiar_basura(raw_base_name)

    # 4. FECHA
    patron_f = r'(\d{4})[\.\-_\s]?(\d{2})[\.\-_\s]?(\d{2})|(\d{2})[\.\-_\s](\d{2})[\.\-_\s](\d{4}|\d{2})'
    match_f = re.search(patron_f, raw_base_name)
    fecha_norm = None
    if match_f:
        g = match_f.groups()
        if g[0]: fecha_norm = f"{g[0]}-{g[1].zfill(2)}-{g[2].zfill(2)}"
        else:
            año = "20"+g[5] if len(g[5])==2 else g[5]
            fecha_norm = f"{año}-{g[4].zfill(2)}-{g[3].zfill(2)}"

    return {
        "estudio_busqueda": estudio_busqueda,
        "fecha": fecha_norm,
        "titulo_busqueda": tit_busqueda,
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
    print(f"[*] BÚSQUEDA: Site='{info['estudio_busqueda']}' | Query='{info['titulo_busqueda']}'")

    # Búsqueda
    params = {"site": info['estudio_busqueda'], "q": info['titulo_busqueda']}
    if info['fecha']: params["date"] = info['fecha']
    res = realizar_peticion(params)
    if not res: res = realizar_peticion({"q": info['titulo_busqueda']})

    if not res:
        print("[!] No se han encontrado resultados.")
        return

    # Selección
    if interactivo:
        print(f"\n[?] Opciones:")
        for i, r in enumerate(res[:10]):
            p_ = r.get('performers', [])
            act = p_[0]['name'] if p_ else "N/A"
            print(f"  {i+1}. [{r['id']}] {r['date']} | {r.get('site',{}).get('name')} | {act} | {r['title']}")
        sel_raw = input("\nSelecciona (Enter para el 1): ").strip()
        escena = res[int(sel_raw)-1 if sel_raw else 0]
    else:
        escena = res[0]

    # Determinación del nombre base para los archivos de salida
    if renombrar:
        est_api = escena.get('site', {}).get('name', info['estudio_busqueda'])
        tit_api = escena.get('title', 'N/A')
        perf = escena.get('performers', [])
        actriz = f" - {perf[0]['name']}" if perf else ""
        tag_vr = "_180_3D_LR" if es_vr else ""
        # Formato: Estudio YYYY-MM-DD Titulo - Actriz [TAG]_180_3D_LR
        nombre_base_final = re.sub(r'[\\/:*?"<>|]', '', f"{est_api} {escena['date']} {tit_api}{actriz}{info['tag_tecnico_api']}{tag_vr}")
    else:
        # Si NO renombras, las imágenes se llaman igual que el video original
        nombre_base_final = info['raw_base_name']

    # Imágenes
    img_url = escena.get('image')
    if img_url:
        print(f"[*] Descargando imágenes...", end=' ', flush=True)
        img_res = requests.get(img_url, timeout=15)
        ctype = img_res.headers.get('Content-Type', '').lower()
        ext_img = '.png' if 'png' in ctype else '.jpg'
        
        for suf in ["", "-fanart"]:
            nom_img = f"{nombre_base_final}{suf}{ext_img}"
            with open(os.path.join(info['directorio'], nom_img), 'wb') as f:
                f.write(img_res.content)
        print("OK.")

    # Renombrar vídeo (Solo si se activó explícitamente -n)
    if renombrar:
        nueva_ruta = os.path.join(info['directorio'], f"{nombre_base_final}{info['ext_video']}")
        if info['original_full_path'] != nueva_ruta:
            os.rename(info['original_full_path'], nueva_ruta)
            print(f"[OK] Vídeo renombrado a: {nombre_base_final}{info['ext_video']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-n", "--rename", action="store_true")
    parser.add_argument("-v", "--vr", action="store_true")
    parser.add_argument("-s", "--site", help="Forzar estudio")
    args = parser.parse_args()
    ejecutar(args.archivo, args.interactive, args.rename, args.vr, args.site)