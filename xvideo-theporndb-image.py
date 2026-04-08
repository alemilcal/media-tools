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
    """Limpia etiquetas para la búsqueda sin tocar la extensión original."""
    if not texto: return ""
    # Eliminamos resoluciones, codecs y tags de calidad
    tags = [
        r'\b\d{3,4}p\b', r'\b(480|720|1080|2160)\b', r'\b\d[kK]\b', 
        r'\bx26[45]\b', r'\bhevc\b', r'\bbrrip\b', r'\bwebrip\b', 
        r'\bq\d{2}\b', r'\bpart\d\b'
    ]
    for tag in tags:
        texto = re.sub(tag, '', texto, flags=re.IGNORECASE)
    # Convertimos símbolos en espacios para la búsqueda
    texto = re.sub(r'[\(\)\[\]\._\-]', ' ', texto)
    return " ".join(texto.split()).strip()

def extraer_datos_locales(ruta_completa):
    path_abs = os.path.abspath(ruta_completa)
    estudio_carpeta = os.path.basename(os.path.dirname(path_abs))
    nombre_archivo = os.path.basename(path_abs)
    
    # 1. CAPTURA DE DOBLE EXTENSIÓN DINÁMICA
    # Busca un punto opcional seguido de letras/números (ej: .q23) 
    # y termina con una extensión de vídeo conocida.
    match_ext = re.search(r'(\.[a-z0-9]+)?\.(mp4|mkv|avi|wmv|mov|flv)$', nombre_archivo, flags=re.IGNORECASE)
    ext_completa = match_ext.group(0) if match_ext else os.path.splitext(nombre_archivo)[1]
    
    # El nombre base es todo lo que hay antes de esa extensión completa
    nombre_sin_ext = nombre_archivo[:nombre_archivo.rfind(ext_completa)]
    
    # 2. DETECCIÓN DE FECHA
    patron_fecha = r'(\d{4})[\.\-_\s]?(\d{2})[\.\-_\s]?(\d{2})|(\d{2})[\.\-_\s](\d{2})[\.\-_\s](\d{4}|\d{2})'
    match_f = re.search(patron_fecha, nombre_sin_ext)
    
    fecha_norm = None
    titulo_raw = nombre_sin_ext
    
    if match_f:
        g = match_f.groups()
        if g[0]: # Formato YYYY MM DD
            fecha_norm = f"{g[0]}-{g[1].zfill(2)}-{g[2].zfill(2)}"
        else: # Formato DD MM YYYY
            año = "20"+g[5] if len(g[5])==2 else g[5]
            fecha_norm = f"{año}-{g[4].zfill(2)}-{g[3].zfill(2)}"
        # Título: preferimos lo que hay después de la fecha
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
        resp.raise_for_status()
        return resp.json().get('data', [])
    except: return []

def buscar_recursivo(info):
    """Busca por niveles para no fallar."""
    # Nivel 1: Estudio + Título + Fecha
    p = {"site": info['estudio_busqueda'], "q": info['titulo_busqueda']}
    if info['fecha']: p["date"] = info['fecha']
    res = realizar_peticion(p)
    if res: return res

    # Nivel 2: Sin fecha
    res = realizar_peticion({"site": info['estudio_busqueda'], "q": info['titulo_busqueda']})
    if res: return res

    # Nivel 3: Solo título (Global)
    return realizar_peticion({"q": info['titulo_busqueda']})

def ejecutar(archivo_input, interactivo=False, renombrar=False):
    info = extraer_datos_locales(archivo_input)
    print(f"\n[*] ARCHIVO: {info['original_base_name']}{info['extension_completa']}")
    print(f"[*] BUSCANDO: Site='{info['estudio_busqueda']}' | Title='{info['titulo_busqueda']}'")

    resultados = buscar_recursivo(info)
    
    if not resultados:
        print("[!] No se encontró ninguna escena en la API.")
        return

    # Selección Interactiva
    if interactivo:
        print(f"\n[?] Opciones encontradas ({len(resultados)}):")
        print(f"{'#':<3} | {'FECHA':<10} | {'SITIO':<15} | {'ACTRIZ':<18} | {'TÍTULO'}")
        print("-" * 90)
        for i, r in enumerate(resultados[:15]):
            p = r.get('performers', [])
            act = p[0]['name'] if p else "N/A"
            sit = r.get('site', {}).get('name', 'N/A')
            print(f"{i+1:<3} | {r['date']:<10} | {sit[:15]:<15} | {act[:18]:<18} | {r['title']}")
        
        sel = int(input("\nSelecciona número (0 para cancelar): ") or 0)
        if sel == 0: return
        escena = resultados[sel-1]
    else:
        escena = resultados[0]

    # Datos oficiales de la API para el nombre
    est_api = escena.get('site', {}).get('name', info['estudio_busqueda'])
    fec_api = escena.get('date', '0000-00-00').replace('-', '.')
    tit_api = escena.get('title', 'N/A')
    perf = escena.get('performers', [])
    actriz = f" - {perf[0]['name']}" if perf else ""

    # Construir nombre base limpio
    nombre_limpio = re.sub(r'[\\/:*?"<>|]', '', f"{est_api} {fec_api} {tit_api}{actriz}")
    prefijo = nombre_limpio if renombrar else info['original_base_name']

    # 1. Posters (mantienen la doble extensión técnica si se renombra)
    img_url = escena.get('image')
    if img_url:
        print(f"[*] Descargando imágenes para ID {escena['id']}...", end=' ', flush=True)
        img_data = requests.get(img_url).content
        ext_img = os.path.splitext(img_url.split('?')[0])[1] or ".jpg"
        
        # Si renombramos, el poster también llevará el .q23 o similar en su nombre
        sufijo_tecnico = info['extension_completa'].rsplit('.', 1)[0] if renombrar else ""
        
        for suf in ["", "-fanart"]:
            nom_img = f"{prefijo}{suf}{ext_img}"
            with open(os.path.join(info['directorio'], nom_img), 'wb') as f:
                f.write(img_data)
        print("OK.")

    # 2. Renombrar Vídeo
    if renombrar:
        nueva_ruta = os.path.join(info['directorio'], f"{nombre_limpio}{info['extension_completa']}")
        if info['original_full_path'] != nueva_ruta:
            print(f"[*] Renombrando vídeo a: {nombre_limpio}{info['extension_completa']}")
            os.rename(info['original_full_path'], nueva_ruta)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-n", "--rename", action="store_true")
    args = parser.parse_args()
    ejecutar(args.archivo, args.interactive, args.rename)