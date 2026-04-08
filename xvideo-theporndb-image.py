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
    """Limpia etiquetas para la búsqueda en la API sin alterar la extensión original."""
    if not texto: return ""
    tags = [
        r'\b\d{3,4}p\b', r'\b(480|720|1080|2160)\b', r'\b\d[kK]\b', 
        r'\bx26[45]\b', r'\bhevc\b', r'\bbrrip\b', r'\bwebrip\b', 
        r'\bq\d{2}\b', r'\bpart\d\b'
    ]
    for tag in tags:
        texto = re.sub(tag, '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'[\(\)\[\]\._\-]', ' ', texto)
    return " ".join(texto.split()).strip()

def extraer_datos_locales(ruta_completa):
    path_abs = os.path.abspath(ruta_completa)
    estudio_carpeta = os.path.basename(os.path.dirname(path_abs))
    nombre_archivo = os.path.basename(path_abs)
    
    # 1. Capturar extensión completa (incluyendo dobles extensiones como .q20.mp4)
    # Busca patrones como .q20.mp4, .1080p.mkv o simplemente .mp4
    match_ext = re.search(r'(\.[a-z0-9]+)?\.(mp4|mkv|avi|wmv|mov|flv)$', nombre_archivo, flags=re.IGNORECASE)
    ext_completa = match_ext.group(0) if match_ext else os.path.splitext(nombre_archivo)[1]
    
    nombre_sin_ext = nombre_archivo[:nombre_archivo.rfind(ext_completa)]
    
    # 2. Regex de fecha
    patron_fecha = r'(\d{4})[\.\-_\s]?(\d{2})[\.\-_\s]?(\d{2})|(\d{2})[\.\-_\s](\d{2})[\.\-_\s](\d{4}|\d{2})'
    match_f = re.search(patron_fecha, nombre_sin_ext)
    
    fecha_norm = None
    titulo_raw = nombre_sin_ext
    
    if match_f:
        g = match_f.groups()
        if g[0]: fecha_norm = f"{g[0]}-{g[1].zfill(2)}-{g[2].zfill(2)}"
        else:
            año = "20"+g[5] if len(g[5])==2 else g[5]
            fecha_norm = f"{año}-{g[4].zfill(2)}-{g[3].zfill(2)}"
        titulo_raw = nombre_sin_ext[match_f.end():].strip() or nombre_sin_ext[:match_f.start()].strip()

    return {
        "estudio_local": estudio_carpeta,
        "estudio_busqueda": limpiar_basura(estudio_carpeta),
        "fecha": fecha_norm,
        "titulo_busqueda": limpiar_basura(titulo_raw),
        "original_full_path": path_abs,
        "original_base_name": nombre_sin_ext,
        "extension_completa": ext_completa,
        "directorio": os.path.dirname(path_abs)
    }

def realizar_peticion(params):
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(SEARCH_URL, headers=headers, params=params, timeout=12)
        return resp.json().get('data', [])
    except: return []

def buscar_recursivo(info, query_manual=None):
    if query_manual: return realizar_peticion({"q": query_manual})
    
    # Intento 1: Estudio + Título + Fecha
    p = {"site": info['estudio_busqueda'], "q": info['titulo_busqueda']}
    if info['fecha']: p["date"] = info['fecha']
    res = realizar_peticion(p)
    if res: return res

    # Intento 2: Sin fecha
    res = realizar_peticion({"site": info['estudio_busqueda'], "q": info['titulo_busqueda']})
    if res: return res

    # Intento 3: Global
    return realizar_peticion({"q": info['titulo_busqueda']})

def ejecutar(archivo_input, interactivo=False, renombrar=False):
    info = extraer_datos_locales(archivo_input)
    print(f"[*] PROCESANDO: {info['original_base_name']}{info['extension_completa']}")
    
    resultados = buscar_recursivo(info)
    
    while not resultados and interactivo:
        nuevo = input("[?] No hay resultados. Búsqueda manual: ").strip()
        if not nuevo: break
        resultados = buscar_recursivo(info, query_manual=nuevo)

    if not resultados: return

    # Selección
    if interactivo:
        print(f"\n[?] Opciones:")
        print(f"{'#':<3} | {'FECHA':<10} | {'SITIO':<15} | {'ACTRIZ':<15} | {'TÍTULO'}")
        for i, r in enumerate(resultados[:10]):
            p = r.get('performers', [])
            a = p[0]['name'] if p else "N/A"
            s = r.get('site', {}).get('name', 'N/A')
            print(f"{i+1:<3} | {r['date']:<10} | {s[:15]:<15} | {a[:15]:<15} | {r['title']}")
        sel = int(input("\nSelecciona (0 para cancelar): ") or 0)
        if sel == 0: return
        escena = resultados[sel-1]
    else:
        escena = resultados[0]

    # Datos API
    est_api = escena.get('site', {}).get('name', info['estudio_busqueda'])
    fec_api = escena.get('date', '0000-00-00').replace('-', '.')
    tit_api = escena.get('title', 'N/A')
    perf = escena.get('performers', [])
    actriz = f" - {perf[0]['name']}" if perf else ""

    nombre_base = re.sub(r'[\\/:*?"<>|]', '', f"{est_api} {fec_api} {tit_api}{actriz}")
    
    # Nombre final conserva la extensión técnica original (.q20.mp4)
    prefijo = nombre_base if renombrar else info['original_base_name']
    
    # 1. Posters
    img_url = escena.get('image')
    if img_url:
        img_data = requests.get(img_url).content
        ext_img = os.path.splitext(img_url.split('?')[0])[1] or ".jpg"
        for sufijo in ["", "-fanart"]:
            # El poster también conserva la "doble extensión" si renombras
            # Ejemplo: Estudio...q20.jpg
            ext_tecnica = info['extension_completa'].rsplit('.', 1)[0] if renombrar else ""
            nom_img = f"{prefijo}{sufijo}{ext_img}"
            with open(os.path.join(info['directorio'], nom_img), 'wb') as f:
                f.write(img_data)
        print("[+] Imágenes guardadas.")

    # 2. Renombrar
    if renombrar:
        nueva_ruta = os.path.join(info['directorio'], f"{nombre_base}{info['extension_completa']}")
        if info['original_full_path'] != nueva_ruta:
            os.rename(info['original_full_path'], nueva_ruta)
            print(f"[+] Renombrado a: {nombre_base}{info['extension_completa']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-n", "--rename", action="store_true")
    args = parser.parse_args()
    ejecutar(args.archivo, args.interactive, args.rename)