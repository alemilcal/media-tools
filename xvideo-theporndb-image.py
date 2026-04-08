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

def limpiar_basura(texto):
    if not texto: return ""
    tags = [
        r'\b\d{3,4}p\b', r'\b(480|720|1080|2160)\b', r'\b\d[kK]\b', 
        r'\bx26[45]\b', r'\bhevc\b', r'\bbrrip\b', r'\bwebrip\b', 
        r'\bq\d{2}\b', r'\bpart\d\b', r'_180_3D_LR' # Añadido el tag VR a la limpieza
    ]
    for tag in tags:
        texto = re.sub(tag, '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'[\(\)\[\]\._\-]', ' ', texto)
    return " ".join(texto.split()).strip()

def extraer_datos_locales(ruta_completa):
    path_abs = os.path.abspath(ruta_completa)
    estudio_carpeta = os.path.basename(os.path.dirname(path_abs))
    nombre_archivo = os.path.basename(path_abs)
    
    # Captura de extensión y etiqueta técnica [Q20]
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
    
    # Eliminar cadena VR del nombre base si ya existía para que no se duplique
    nombre_sin_ext = re.sub(r'_180_3D_LR', '', nombre_sin_ext, flags=re.IGNORECASE)

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
        "estudio_busqueda": limpiar_basura(estudio_carpeta),
        "fecha": fecha_norm,
        "titulo_busqueda": limpiar_basura(nombre_sin_ext),
        "original_full_path": path_abs,
        "original_base_name": nombre_sin_ext.strip(),
        "ext_video": ext_video,
        "tag_tecnico_api": tag_tecnico_api,
        "sufijo_original": sufijo_original,
        "directorio": os.path.dirname(path_abs)
    }

def ejecutar(archivo_input, interactivo=False, renombrar=False, es_vr=False):
    info = extraer_datos_locales(archivo_input)
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    
    # Búsqueda
    p = {"site": info['estudio_busqueda'], "q": info['titulo_busqueda']}
    if info['fecha']: p["date"] = info['fecha']
    
    print(f"[*] PROCESANDO: {info['original_base_name']}")
    try:
        res = requests.get(SEARCH_URL, headers=headers, params=p, timeout=12).json().get('data', [])
        if not res: res = requests.get(SEARCH_URL, headers=headers, params={"q": info['titulo_busqueda']}).json().get('data', [])
        
        if not res:
            print("[!] No se encontró nada.")
            return

        if interactivo:
            print("\n[?] Opciones:")
            for i, r in enumerate(res[:10]):
                p_ = r.get('performers', [])
                act = p_[0]['name'] if p_ else "N/A"
                print(f"  {i+1}. [{r['id']}] {r['date']} | {r.get('site',{}).get('name')} | {act} | {r['title']}")
            sel = int(input("\nSelecciona número: ") or 1)
            escena = res[sel-1]
        else:
            escena = res[0]

        # Datos para nombre
        est_api = escena.get('site', {}).get('name', info['estudio_busqueda'])
        fec_api = escena.get('date', '0000-00-00')
        tit_api = escena.get('title', 'N/A')
        perf = escena.get('performers', [])
        actriz = f" - {perf[0]['name']}" if perf else ""
        
        # Etiqueta VR
        tag_vr = "_180_3D_LR" if es_vr else ""

        if renombrar:
            nombre_base_f = re.sub(r'[\\/:*?"<>|]', '', f"{est_api} {fec_api} {tit_api}{actriz}{info['tag_tecnico_api']}{tag_vr}")
            sufijo_img = ""
        else:
            nombre_base_f = f"{info['original_base_name']}{tag_vr}"
            sufijo_img = info['sufijo_original']

        # Imágenes
        img_url = escena.get('image')
        if img_url:
            print(f"[*] Descargando pósters...", end=' ', flush=True)
            img_res = requests.get(img_url, timeout=15)
            ctype = img_res.headers.get('Content-Type', '').lower()
            ext_img = '.png' if 'png' in ctype else '.jpg'
            
            for suf in ["", "-fanart"]:
                nom_img = f"{nombre_base_f}{suf}{sufijo_img}{ext_img}"
                with open(os.path.join(info['directorio'], nom_img), 'wb') as f:
                    f.write(img_res.content)
            print("OK.")

        # Renombrar Vídeo
        if renombrar:
            nueva_ruta = os.path.join(info['directorio'], f"{nombre_base_f}{info['ext_video']}")
            os.rename(info['original_full_path'], nueva_ruta)
            print(f"[OK] Vídeo renombrado a: {nombre_base_f}{info['ext_video']}")

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-n", "--rename", action="store_true")
    parser.add_argument("-v", "--vr", action="store_true", help="Añade sufijo _180_3D_LR para VR")
    args = parser.parse_args()
    ejecutar(args.archivo, args.interactive, args.rename, args.vr)