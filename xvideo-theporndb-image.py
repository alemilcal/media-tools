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

def extraer_campos(nombre_archivo):
    """
    Usa Regex para separar: Studio, Fecha (YYYY-MM-DD) y Titulo.
    Soporta separadores de espacio o guion bajo.
    """
    nombre_sin_ext, _ = os.path.splitext(os.path.basename(nombre_archivo))
    
    # Patrón: (Cualquier cosa) + (Espacio o _) + (4 dígitos-2-2) + (Espacio o _) + (Resto)
    pattern = r'^(.+?)[\s_](\d{4}-\d{2}-\d{2})[\s_](.+)$'
    match = re.match(pattern, nombre_sin_ext)
    
    if match:
        return {
            "studio": match.group(1).strip(),
            "fecha": match.group(2).strip(),
            "titulo": match.group(3).strip(),
            "original": nombre_sin_ext
        }
    return None

def descargar_poster(archivo_input):
    campos = extraer_campos(archivo_input)
    
    if not campos:
        print(f"[!] Error: El formato del nombre no es válido (Studio Fecha Titulo).", flush=True)
        print(f"    Recibido: '{archivo_input}'", flush=True)
        return

    print(f"[*] Datos extraídos:", flush=True)
    print(f"    - Estudio: {campos['studio']}")
    print(f"    - Fecha:   {campos['fecha']}")
    print(f"    - Título:  {campos['titulo']}", flush=True)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    # Parámetros de búsqueda avanzada
    params = {
        "site": campos['studio'],
        "date": campos['fecha'],
        "q": campos['titulo'],
        "limit": 1  # Solo queremos el mejor resultado
    }

    try:
        print(f"[*] Consultando búsqueda avanzada...", flush=True)
        response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=(5, 15))
        response.raise_for_status()
        
        json_data = response.json()
        
        # El endpoint /scenes devuelve una lista en el campo 'data'
        results = json_data.get('data', [])
        
        if not results:
            print(f"[!] No se encontraron resultados específicos con esos filtros.", flush=True)
            return

        # Tomamos el primer resultado
        scene = results[0]
        image_url = scene.get('image')

        if not image_url:
            print(f"[-] Escena encontrada pero no tiene URL de imagen.", flush=True)
            return

        print(f"[+] Resultado encontrado: {scene.get('title')} ({scene.get('site', {}).get('name')})", flush=True)
        print(f"[*] Descargando imagen...", flush=True)

        img_res = requests.get(image_url, timeout=(5, 20))
        img_res.raise_for_status()

        # Determinar extensión
        _, img_ext = os.path.splitext(image_url.split('?')[0])
        img_ext = img_ext if img_ext else ".jpg"
        
        # Guardar con el nombre original del archivo
        nombre_salida = f"{campos['original']}{img_ext}"

        with open(nombre_salida, 'wb') as f:
            f.write(img_res.content)
        
        print(f"[OK] ¡Éxito! Archivo guardado como: {nombre_salida}", flush=True)

    except Exception as e:
        print(f"[!] Error durante la ejecución: {e}", flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descarga optimizada de posters")
    parser.add_argument("archivo", help="Nombre del archivo (Studio Fecha Titulo)")
    
    args = parser.parse_args()
    descargar_poster(args.archivo)