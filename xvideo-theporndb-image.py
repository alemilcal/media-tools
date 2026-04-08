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
    
    # 1. Normalizar: convertimos TODOS los separadores a espacios primero
    # Esto permite que los tags técnicos se detecten correctamente como palabras
    texto = re.sub(r'[\(\)\[\]\._\-]', ' ', texto)
    
    if es_estudio:
        return " ".join(texto.split()).strip()

    # 2. Diccionario agresivo de tags técnicos (VR y Ripeos)
    tags = [
        r'\b\d{3,4}p\b', r'\b(480|720|1080|2160)\b', r'\b\d[kK]\b', 
        r'\bx26[45]\b', r'\bhevc\b', r'\bbrrip\b', r'\bwebrip\b', 
        r'\bq\d{2}\b', r'\bpart\d\b', 
        r'\b180x180\b', r'\b3dh\b', r'\b3d\b', r'\blr\b', r'\b180\b', 
        r'\bsbs\b', r'\bvr\b', r'\bfull\b', r'\braw\b'
    ]
    
    for tag in tags:
        texto = re.sub(tag, '', texto, flags=re.IGNORECASE)
    
    return " ".join(texto.split()).strip()

def extraer_datos_locales(ruta_completa, sitio_forzado=None):
    path_abs = os.path.abspath(ruta_completa)
    nombre_archivo = os.path.basename(path_abs)
    
    # 1. ESTUDIO
    estudio_raw = sitio_forzado if sitio_forzado else os.path.basename(os.path.dirname(path_abs))
    estudio_busqueda = limpiar_basura(estudio_raw, es_estudio=True)
    
    # 2. EXTENSIÓN Y TAG [Q20]
    match_ext = re.search(r'\.([a-z0-9]+)\.(mp4|mkv|avi|wmv|mov|flv)$', nombre_archivo, flags=re.IGNORECASE)
    if match_ext:
        tag_tecnico_api = f" [{match_ext.group(1).upper()}]"
        sufijo_original = f".{match_ext.group(1)}"
        ext_video = f".{match_ext.group(2)}"
        nombre_sin_ext = nombre_archivo[:match_ext.start()]
    else:
        tag_tecnico_api = ""
        sufijo_original = ""
        nombre_sin_ext, ext_video = os.path.splitext(nombre_archivo)

    # 3. LIMPIEZA DE TÍTULO (Quitar nombre del estudio y tags técnicos)
    # Primero quitamos el nombre del estudio si aparece pegado o con espacios
    estudio_sin_espacios = estudio_busqueda.replace(" ", "")
    titulo_temp = re.sub(re.escape(estudio_sin_espacios), '', nombre_sin_ext, flags=re.IGNORECASE)
    titulo_temp = re.sub(re.escape(estudio_busqueda), '', titulo_temp, flags=re.IGNORECASE)
    
    # Ahora limpiamos todos los tags técnicos (yoga-temptation-4k... -> yoga temptation)
    titulo_final = limpiar_basura(titulo_temp)
    
    # Fallback: si la limpieza es excesiva, usamos el nombre original limpio
    if len(titulo_final) < 3:
        titulo_final = limpiar_basura(nombre_sin_ext)

    # 4. FECHA
    patron_fecha = r'(\d{4})[\.\-_\s]?(\d{2})[\.\-_\s]?(\d{2})|(\d{2})[\.\-_\s](\d{2})[\.\-_\s](\d{4}|\d{2})'
    match_f = re.search(patron_fecha, nombre_sin_ext)
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
        "titulo_busqueda": titulo_final,
        "original_full_path": path_abs,
        "original_base_name": nombre_sin_ext.strip(),
        "ext_video": ext_video,
        "tag_tecnico_api": tag_tecnico_api,
        "sufijo_original": sufijo_original,
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
    print(f"\n[*] ARCHIVO: {info['original_base_name']}")
    print(f"[*] BUSCANDO: Site='{info['estudio_busqueda']}' | Query='{info['titulo_busqueda']}'")

    # 1. Búsqueda con Site + Título
    params = {"site": info['estudio_busqueda'], "q": info['titulo_busqueda']}
    if info['fecha']: params["date"] = info['fecha']
    resultados = realizar_peticion(params)
    
    # 2. Si falla, reintento global (solo Título)
    if not resultados:
        print("[*] Sin resultados con filtro de estudio. Probando búsqueda global...")
        resultados = realizar_peticion({"q": info['titulo_busqueda']})

    # 3. Rescate Manual (Si nada funciona y es interactivo)
    while not resultados and interactivo:
        print("\n" + "!"*20 + " NO HAY RESULTADOS AUTOMÁTICOS " + "!"*20)
        manual = input("[?] Escribe título o actriz (o Enter para salir): ").strip()
        if not manual: break
        resultados = realizar_peticion({"q": manual})

    if not resultados:
        print("[!] No se encontró nada.")
        return

    # Selección
    if interactivo:
        print(f"\n[?] Opciones:")
        print(f"{'#':<3} | {'FECHA':<10} | {'SITIO':<15} | {'ACTRIZ':<18} | {'TÍTULO'}")
        print("-" * 95)
        for i, r in enumerate(resultados[:15]):
            p_ = r.get('performers', [])
            act = p_[0]['name'] if p_ else "N/A"
            sit = r.get('site', {}).get('name', 'N/A')
            print(f"{i+1:<3} | {r['date']:<10} | {sit[:15]:<15} | {act[:18]:<18} | {r['title']}")
        
        sel_raw = input("\nSelecciona número (Enter para el 1): ").strip()
        escena = resultados[int(sel_raw)-1 if sel_raw else 0]
    else:
        escena = resultados[0]

    # Procesamiento de nombre final
    est_api = escena.get('site', {}).get('name', info['estudio_busqueda'])
    fec_api = escena.get('date', '0000-00-00')
    tit_api = escena.get('title', 'N/A')
    perf = escena.get('performers', [])
    actriz = f" - {perf[0]['name']}" if perf else ""
    tag_vr = "_180_3D_LR" if es_vr else ""

    if renombrar:
        nombre_base_f = re.sub(r'[\\/:*?"<>|]', '', f"{est_api} {fec_api} {tit_api}{actriz}{info['tag_tecnico_api']}{tag_vr}")
        sufijo_img = ""
    else:
        nombre_base_f = f"{info['original_base_name']}{tag_vr}"
        sufijo_img = info['sufijo_original']

    # Descarga imágenes
    img_url = escena.get('image')
    if img_url:
        print(f"[*] Descargando imágenes...", end=' ', flush=True)
        img_res = requests.get(img_url, timeout=15)
        ext_img = '.png' if 'png' in img_res.headers.get('Content-Type', '').lower() else '.jpg'
        for suf in ["", "-fanart"]:
            nom_img = f"{nombre_base_f}{suf}{sufijo_img}{ext_img}"
            with open(os.path.join(info['directorio'], nom_img), 'wb') as f:
                f.write(img_res.content)
        print("OK.")

    if renombrar:
        nueva_ruta = os.path.join(info['directorio'], f"{nombre_base_f}{info['ext_video']}")
        os.rename(info['original_full_path'], nueva_ruta)
        print(f"[OK] Renombrado a: {nombre_base_f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-n", "--rename", action="store_true")
    parser.add_argument("-v", "--vr", action="store_true")
    parser.add_argument("-s", "--site", help="Forzar estudio")
    args = parser.parse_args()
    ejecutar(args.archivo, args.interactive, args.rename, args.vr, args.site)