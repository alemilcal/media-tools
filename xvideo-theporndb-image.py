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

def limpiar_nombre_busqueda(texto):
    """Elimina etiquetas técnicas y limpia símbolos."""
    tags = [r'\b\d{3,4}p\b', r'\b\d[kK]\b', r'\bx26[45]\b', r'\bhevc\b', r'\bbrrip\b', r'\bwebrip\b']
    for tag in tags:
        texto = re.sub(tag, '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'[\(\)\[\]\._\-]', ' ', texto)
    return " ".join(texto.split()).strip()

def extraer_datos_locales(ruta_completa):
    path_abs = os.path.abspath(ruta_completa)
    estudio = os.path.basename(os.path.dirname(path_abs))
    nombre_archivo = os.path.basename(path_abs)
    nombre_sin_ext, ext_video = os.path.splitext(nombre_archivo)
    
    patron_fecha = r'(\d{4}|\d{2})[\._\-\s](\d{2})[\._\-\s](\d{2}|\d{4})'
    match = re.search(patron_fecha, nombre_sin_ext)
    fecha_norm = None
    titulo_raw = nombre_sin_ext

    if match:
        g1, g2, g3 = match.groups()
        if len(g1) == 4: fecha_norm = f"{g1}-{g2.zfill(2)}-{g3.zfill(2)}"
        else:
            año = "20"+g3 if len(g3)==2 else g3
            fecha_norm = f"{año}-{g2.zfill(2)}-{g1.zfill(2)}"
        titulo_raw = nombre_sin_ext[match.end():] or nombre_sin_ext

    return {
        "estudio": limpiar_nombre_busqueda(estudio),
        "fecha": fecha_norm,
        "titulo_busqueda": limpiar_nombre_busqueda(titulo_raw),
        "original_full_path": path_abs,
        "original_base_name": nombre_sin_ext,
        "extension_video": ext_video,
        "directorio": os.path.dirname(path_abs)
    }

def buscar_y_procesar(archivo_input, interactivo=False, renombrar=False):
    info = extraer_datos_locales(archivo_input)
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    
    print(f"\n[*] PROCESANDO: {info['original_base_name']}")
    params = {"site": info['estudio'], "q": info['titulo_busqueda']}
    if info['fecha']: params["date"] = info['fecha']

    try:
        # Búsqueda en cascada
        res = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10).json().get('data', [])
        if not res and info['fecha']:
            params.pop("date")
            res = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10).json().get('data', [])
        if not res:
            res = requests.get(SEARCH_URL, headers=headers, params={"q": info['titulo_busqueda']}, timeout=10).json().get('data', [])

        if not res:
            print("[!] No se encontró nada en la API.")
            return

        # Selección de resultado (Ahora siempre pregunta si -i está activo)
        if interactivo:
            print(f"\n[?] Resultados encontrados ({len(res)}):")
            for i, r in enumerate(res[:10]): # Mostramos hasta 10 opciones
                sitio = r.get('site', {}).get('name', 'N/A')
                print(f"  {i+1}. [{r['id']}] {r['title']} ({r['date']}) - {sitio}")
            
            try:
                sel = int(input("\nSelecciona el número (0 para cancelar): ") or 0)
                if sel == 0: return
                escena = res[sel-1]
            except (ValueError, IndexError):
                print("[!] Selección no válida.")
                return
        else:
            escena = res[0]

        # Datos oficiales
        estudio_api = escena.get('site', {}).get('name', info['estudio'])
        fecha_api = escena.get('date', '0000-00-00').replace('-', '.')
        titulo_api = escena.get('title', info['titulo_busqueda'])
        actrices = escena.get('performers', [])
        actriz_str = f" - {actrices[0]['name']}" if actrices else ""

        nombre_estandar = re.sub(r'[\\/:*?"<>|]', '', f"{estudio_api} {fecha_api} {titulo_api}{actriz_str}")
        prefijo_nombre = nombre_estandar if renombrar else info['original_base_name']

        # 1. Póster y Fanart
        img_url = escena.get('image')
        if img_url:
            print("[*] Descargando imágenes...", end=' ', flush=True)
            img_data = requests.get(img_url).content
            _, ext_img = os.path.splitext(img_url.split('?')[0])
            ext_img = ext_img if ext_img else ".jpg"
            
            for sufijo in ["", "-fanart"]:
                ruta = os.path.join(info['directorio'], f"{prefijo_nombre}{sufijo}{ext_img}")
                with open(ruta, 'wb') as f:
                    f.write(img_data)
            print("Póster y Fanart OK.")

        # 2. Renombrar
        if renombrar:
            nueva_ruta_video = os.path.join(info['directorio'], f"{nombre_estandar}{info['extension_video']}")
            if info['original_full_path'] != nueva_ruta_video:
                print(f"[*] Renombrando vídeo a: {nombre_estandar}{info['extension_video']}")
                os.rename(info['original_full_path'], nueva_ruta_video)

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-n", "--rename", action="store_true")
    args = parser.parse_args()
    
    buscar_y_procesar(args.archivo, args.interactive, args.rename)
