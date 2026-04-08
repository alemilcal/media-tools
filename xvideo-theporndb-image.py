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
    """Elimina etiquetas técnicas, calidades y extensiones dobles."""
    if not texto: return ""
    # Eliminar etiquetas técnicas y calidades comunes
    tags = [
        r'\b\d{3,4}p\b', r'\b\d[kK]\b', r'\bx26[45]\b', r'\bhevc\b', 
        r'\bbrrip\b', r'\bwebrip\b', r'\bq\d{2}\b', r'\bpart\d\b'
    ]
    for tag in tags:
        texto = re.sub(tag, '', texto, flags=re.IGNORECASE)
    
    # Reemplazar símbolos por espacios
    texto = re.sub(r'[\(\)\[\]\._\-]', ' ', texto)
    return " ".join(texto.split()).strip()

def extraer_datos_locales(ruta_completa):
    path_abs = os.path.abspath(ruta_completa)
    estudio_carpeta = os.path.basename(os.path.dirname(path_abs))
    nombre_archivo = os.path.basename(path_abs)
    
    # 1. Gestionar extensión (quitar .mp4, .mkv, etc. y posibles puntos previos como .q20)
    # Buscamos la última coincidencia de una extensión conocida
    nombre_sin_ext = re.sub(r'\.(mp4|mkv|avi|wmv|mov|flv)$', '', nombre_archivo, flags=re.IGNORECASE)
    # Si queda algo como "titulo.q20", limpiar_basura se encargará después
    
    # 2. Regex de fecha mejorado
    # Grupo 1: YYYY-MM-DD o YYYY.MM.DD o YYYY_MM_DD o YYYYMMDD
    # Grupo 2: DD-MM-YYYY o variantes
    patrones = [
        r'(\d{4})[\.\-_\s]?(\d{2})[\.\-_\s]?(\d{2})', # YYYYMMDD o YYYY.MM.DD
        r'(\d{2})[\.\-_\s](\d{2})[\.\-_\s](\d{4}|\d{2})' # DD.MM.YYYY
    ]
    
    fecha_norm = None
    titulo_raw = nombre_sin_ext
    
    for p in patrones:
        match = re.search(p, nombre_sin_ext)
        if match:
            g1, g2, g3 = match.groups()
            if len(g1) == 4: # Caso YYYY MM DD
                fecha_norm = f"{g1}-{g2.zfill(2)}-{g3.zfill(2)}"
            else: # Caso DD MM YYYY
                año = "20"+g3 if len(g3)==2 else g3
                fecha_norm = f"{año}-{g2.zfill(2)}-{g1.zfill(2)}"
            
            # El título es lo que queda DESPUÉS de la fecha
            titulo_raw = nombre_sin_ext[match.end():].strip()
            # Si después de la fecha no hay nada relevante, usamos el nombre completo
            if not limpiar_basura(titulo_raw):
                titulo_raw = nombre_sin_ext[:match.start()].strip()
            break

    return {
        "estudio_local": estudio_carpeta,
        "estudio_busqueda": limpiar_basura(estudio_carpeta),
        "fecha": fecha_norm,
        "titulo_busqueda": limpiar_basura(titulo_raw),
        "original_full_path": path_abs,
        "original_base_name": nombre_sin_ext,
        "extension_video": os.path.splitext(nombre_archivo)[1],
        "directorio": os.path.dirname(path_abs)
    }

def normalizar_para_comparar(texto):
    return re.sub(r'[^a-zA-Z0-9]', '', texto).lower()

def buscar_y_procesar(archivo_input, interactivo=False, renombrar=False):
    info = extraer_datos_locales(archivo_input)
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    
    print(f"\n[*] ANALIZANDO: {info['original_base_name']}")
    print(f"    - Estudio: {info['estudio_local']}")
    print(f"    - Fecha:   {info['fecha'] if info['fecha'] else 'No detectada'}")
    print(f"    - Título:  {info['titulo_busqueda']}")

    params = {"site": info['estudio_busqueda'], "q": info['titulo_busqueda']}
    if info['fecha']: params["date"] = info['fecha']

    try:
        res_raw = requests.get(SEARCH_URL, headers=headers, params=params, timeout=12).json().get('data', [])
        
        # Filtro estricto de estudio
        local_std_norm = normalizar_para_comparar(info['estudio_busqueda'])
        resultados_validos = []
        for r in res_raw:
            api_std_norm = normalizar_para_comparar(r.get('site', {}).get('name', ''))
            if local_std_norm in api_std_norm or api_std_norm in local_std_norm:
                resultados_validos.append(r)

        if not resultados_validos:
            print("[!] No se han encontrado escenas que coincidan con el estudio local.")
            return

        # Modo Interactivo
        if interactivo:
            print(f"\n[?] Opciones encontradas ({len(resultados_validos)}):")
            print(f"{'#':<3} | {'FECHA':<10} | {'ACTRIZ':<20} | {'TÍTULO'}")
            print("-" * 85)
            for i, r in enumerate(resultados_validos[:10]):
                perfs = r.get('performers', [])
                actriz = perfs[0]['name'] if perfs else "N/A"
                print(f"{i+1:<3} | {r['date']:<10} | {actriz[:20]:<20} | {r['title']}")
            
            sel = int(input("\nSelecciona número (0 para cancelar): ") or 0)
            if sel == 0: return
            escena = resultados_validos[sel-1]
        else:
            escena = resultados_validos[0]

        # Datos finales
        estudio_api = escena.get('site', {}).get('name', info['estudio_busqueda'])
        fecha_api = escena.get('date', '0000-00-00').replace('-', '.')
        titulo_api = escena.get('title', 'N/A')
        perfs_api = escena.get('performers', [])
        actriz_api = f" - {perfs_api[0]['name']}" if perfs_api else ""

        nombre_limpio = re.sub(r'[\\/:*?"<>|]', '', f"{estudio_api} {fecha_api} {titulo_api}{actriz_api}")
        prefijo = nombre_limpio if renombrar else info['original_base_name']

        # Descarga Imágenes
        img_url = escena.get('image')
        if img_url:
            print(f"\n[+] ID: {escena['id']} | Descargando pósters...", end=' ', flush=True)
            img_data = requests.get(img_url).content
            _, ext_img = os.path.splitext(img_url.split('?')[0])
            ext_img = ext_img if ext_img else ".jpg"
            
            for sufijo in ["", "-fanart"]:
                with open(os.path.join(info['directorio'], f"{prefijo}{sufijo}{ext_img}"), 'wb') as f:
                    f.write(img_data)
            print("OK.")

        # Renombrar Vídeo
        if renombrar:
            nueva_ruta = os.path.join(info['directorio'], f"{nombre_limpio}{info['extension_video']}")
            if info['original_full_path'] != nueva_ruta:
                print(f"[*] Renombrando vídeo a: {nombre_limpio}{info['extension_video']}")
                os.rename(info['original_full_path'], nueva_ruta)

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-n", "--rename", action="store_true")
    args = parser.parse_args()
    buscar_y_procesar(args.archivo, args.interactive, args.rename)