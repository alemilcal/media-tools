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

def limpiar_texto(texto):
    """Limpia etiquetas técnicas y normaliza para comparar o buscar."""
    if not texto: return ""
    tags = [r'\b\d{3,4}p\b', r'\b\d[kK]\b', r'\bx26[45]\b', r'\bhevc\b', r'\bbrrip\b', r'\bwebrip\b']
    for tag in tags:
        texto = re.sub(tag, '', texto, flags=re.IGNORECASE)
    # Solo dejamos letras y números para una comparación más robusta
    texto = re.sub(r'[\(\)\[\]\._\-]', ' ', texto)
    return " ".join(texto.split()).strip()

def normalizar_para_comparar(texto):
    """Elimina todo excepto letras y números para comparar estudios estrictamente."""
    return re.sub(r'[^a-zA-Z0-9]', '', texto).lower()

def extraer_datos_locales(ruta_completa):
    path_abs = os.path.abspath(ruta_completa)
    # El estudio es el nombre de la carpeta
    estudio_carpeta = os.path.basename(os.path.dirname(path_abs))
    
    nombre_archivo = os.path.basename(path_abs)
    nombre_sin_ext, ext_video = os.path.splitext(nombre_archivo)
    
    # Buscar fecha
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
        "estudio_local": estudio_carpeta,
        "estudio_busqueda": limpiar_texto(estudio_carpeta),
        "fecha": fecha_norm,
        "titulo_busqueda": limpiar_texto(titulo_raw),
        "original_full_path": path_abs,
        "original_base_name": nombre_sin_ext,
        "extension_video": ext_video,
        "directorio": os.path.dirname(path_abs)
    }

def buscar_y_procesar(archivo_input, interactivo=False, renombrar=False):
    info = extraer_datos_locales(archivo_input)
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    
    print(f"\n[*] ARCHIVO: {info['original_base_name']}")
    print(f"[*] ESTUDIO LOCAL: {info['estudio_local']}")
    
    params = {"site": info['estudio_busqueda'], "q": info['titulo_busqueda']}
    if info['fecha']: params["date"] = info['fecha']

    try:
        # Petición a la API
        res_raw = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10).json().get('data', [])
        
        # Filtrado Estricto de Estudio
        # Solo nos quedamos con resultados donde el estudio coincida con la carpeta
        estudio_local_norm = normalizar_para_comparar(info['estudio_busqueda'])
        resultados_validos = []

        for escena in res_raw:
            estudio_api = escena.get('site', {}).get('name', '')
            estudio_api_norm = normalizar_para_comparar(estudio_api)
            
            # Verificamos si uno contiene al otro (ej: "SexArt" coincide con "SexArt Studio")
            if estudio_local_norm in estudio_api_norm or estudio_api_norm in estudio_local_norm:
                resultados_validos.append(escena)

        if not resultados_validos:
            print(f"[!] ERROR: No se encontraron escenas que coincidan con el estudio '{info['estudio_local']}'.")
            return

        # Selección de resultado
        if interactivo:
            print(f"\n[?] Resultados validados para el estudio '{info['estudio_local']}' ({len(resultados_validos)}):")
            for i, r in enumerate(resultados_validos[:10]):
                print(f"  {i+1}. [{r['id']}] {r['title']} ({r['date']})")
            
            try:
                sel = int(input("\nSelecciona (0 para cancelar): ") or 0)
                if sel == 0: return
                escena = resultados_validos[sel-1]
            except: return
        else:
            escena = resultados_validos[0]

        # Datos para el renombrado
        estudio_api_final = escena.get('site', {}).get('name', info['estudio_busqueda'])
        fecha_api = escena.get('date', '0000-00-00').replace('-', '.')
        titulo_api = escena.get('title', 'N/A')
        actrices = escena.get('performers', [])
        actriz_str = f" - {actrices[0]['name']}" if actrices else ""

        nombre_final_base = re.sub(r'[\\/:*?"<>|]', '', f"{estudio_api_final} {fecha_api} {titulo_api}{actriz_str}")
        prefijo = nombre_final_base if renombrar else info['original_base_name']

        # Descarga de Póster y Fanart
        img_url = escena.get('image')
        if img_url:
            print(f"[+] Escena ID: {escena['id']} | Descargando imágenes...", end=' ', flush=True)
            img_data = requests.get(img_url).content
            _, ext_img = os.path.splitext(img_url.split('?')[0])
            ext_img = ext_img if ext_img else ".jpg"
            
            for sufijo in ["", "-fanart"]:
                ruta = os.path.join(info['directorio'], f"{prefijo}{sufijo}{ext_img}")
                with open(ruta, 'wb') as f:
                    f.write(img_data)
            print("OK.")

        # Renombrar vídeo
        if renombrar:
            nueva_ruta = os.path.join(info['directorio'], f"{nombre_final_base}{info['extension_video']}")
            if info['original_full_path'] != nueva_ruta:
                print(f"[*] Renombrando a: {nombre_final_base}{info['extension_video']}")
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
