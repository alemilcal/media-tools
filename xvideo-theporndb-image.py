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
    """Elimina etiquetas técnicas y limpia el nombre."""
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

def normalizar_para_comparar(texto):
    return re.sub(r'[^a-zA-Z0-9]', '', texto).lower()

def extraer_datos_locales(ruta_completa):
    path_abs = os.path.abspath(ruta_completa)
    estudio_carpeta = os.path.basename(os.path.dirname(path_abs))
    nombre_archivo = os.path.basename(path_abs)
    nombre_sin_ext = re.sub(r'\.(mp4|mkv|avi|wmv|mov|flv)$', '', nombre_archivo, flags=re.IGNORECASE)
    
    patron_fecha = r'(\d{4})[\.\-_\s]?(\d{2})[\.\-_\s]?(\d{2})|(\d{2})[\.\-_\s](\d{2})[\.\-_\s](\d{4}|\d{2})'
    match = re.search(patron_fecha, nombre_sin_ext)
    
    fecha_norm = None
    titulo_raw = nombre_sin_ext
    
    if match:
        grupos = match.groups()
        if grupos[0]: # Formato YYYY MM DD
            fecha_norm = f"{grupos[0]}-{grupos[1].zfill(2)}-{grupos[2].zfill(2)}"
        else: # Formato DD MM YYYY
            año = "20"+grupos[5] if len(grupos[5])==2 else grupos[5]
            fecha_norm = f"{año}-{grupos[4].zfill(2)}-{grupos[3].zfill(2)}"
        titulo_raw = nombre_sin_ext[match.end():].strip() or nombre_sin_ext[:match.start()].strip()

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

def realizar_peticion(params):
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(SEARCH_URL, headers=headers, params=params, timeout=12)
        return resp.json().get('data', [])
    except:
        return []

def buscar_recursivo(info, query_manual=None):
    """Estrategia de búsqueda por niveles de agresividad."""
    # Si el usuario introduce una búsqueda manual
    if query_manual:
        print(f"[*] Buscando manualmente: '{query_manual}'...")
        return realizar_peticion({"q": query_manual})

    # Nivel 1: Estudio + Título + Fecha
    print("[*] Nivel 1: Búsqueda estricta...", end=' ', flush=True)
    p = {"site": info['estudio_busqueda'], "q": info['titulo_busqueda']}
    if info['fecha']: p["date"] = info['fecha']
    res = realizar_peticion(p)
    if res: return res

    # Nivel 2: Estudio + Título (sin fecha)
    print("\n[*] Nivel 2: Sin fecha...", end=' ', flush=True)
    res = realizar_peticion({"site": info['estudio_busqueda'], "q": info['titulo_busqueda']})
    if res: return res

    # Nivel 3: Solo Título (Fuzzy global)
    print("\n[*] Nivel 3: Global por título...", end=' ', flush=True)
    res = realizar_peticion({"q": info['titulo_busqueda']})
    if res: return res

    # Nivel 4: Fragmentar título (primeras 3 palabras)
    palabras = info['titulo_busqueda'].split()
    if len(palabras) > 2:
        fragmento = " ".join(palabras[:3])
        print(f"\n[*] Nivel 4: Fragmento '{fragmento}'...", end=' ', flush=True)
        res = realizar_peticion({"q": fragmento})
        if res: return res

    return []

def ejecutar(archivo_input, interactivo=False, renombrar=False):
    info = extraer_datos_locales(archivo_input)
    print(f"\n[*] ANALIZANDO: {info['original_base_name']}")
    
    resultados = buscar_recursivo(info)
    
    # BUCLE DE RESCATE (Solo si es interactivo y no hay resultados)
    while not resultados and interactivo:
        print("\n[!] No se encontró nada automáticamente.")
        nuevo_termino = input("[?] Introduce término de búsqueda manual (o Enter para salir): ").strip()
        if not nuevo_termino: break
        resultados = buscar_recursivo(info, query_manual=nuevo_termino)

    if not resultados:
        print("\n[!] Fin de búsqueda sin resultados.")
        return

    # Filtrar por estudio si no es búsqueda manual y no estamos en modo relax total
    local_std_norm = normalizar_para_comparar(info['estudio_busqueda'])
    validos = []
    for r in resultados:
        api_std_norm = normalizar_para_comparar(r.get('site', {}).get('name', ''))
        # Aceptamos si el estudio coincide O si el usuario está eligiendo manualmente
        if local_std_norm in api_std_norm or api_std_norm in local_std_norm or interactivo:
            validos.append(r)

    if not validos:
        print("[!] Los resultados encontrados no coinciden con el estudio local.")
        return

    # Selección
    if interactivo:
        print(f"\n[?] Opciones ({len(validos)}):")
        print(f"{'#':<3} | {'FECHA':<10} | {'SITIO':<15} | {'ACTRIZ':<15} | {'TÍTULO'}")
        print("-" * 90)
        for i, r in enumerate(validos[:15]):
            perfs = r.get('performers', [])
            actriz = perfs[0]['name'] if perfs else "N/A"
            sitio = r.get('site', {}).get('name', 'N/A')
            print(f"{i+1:<3} | {r['date']:<10} | {sitio[:15]:<15} | {actriz[:15]:<15} | {r['title']}")
        
        sel = int(input("\nSelecciona número (0 para cancelar): ") or 0)
        if sel == 0: return
        escena = validos[sel-1]
    else:
        escena = validos[0]

    # Procesamiento final (Pósters y Renombrado)
    estudio_api = escena.get('site', {}).get('name', info['estudio_busqueda'])
    fecha_api = escena.get('date', '0000-00-00').replace('-', '.')
    titulo_api = escena.get('title', 'N/A')
    perfs_api = escena.get('performers', [])
    actriz_api = f" - {perfs_api[0]['name']}" if perfs_api else ""

    nombre_f = re.sub(r'[\\/:*?"<>|]', '', f"{estudio_api} {fecha_api} {titulo_api}{actriz_api}")
    prefijo = nombre_f if renombrar else info['original_base_name']

    img_url = escena.get('image')
    if img_url:
        print(f"\n[+] ID: {escena['id']} | Descargando pósters...", end=' ', flush=True)
        img_data = requests.get(img_url).content
        ext_img = os.path.splitext(img_url.split('?')[0])[1] or ".jpg"
        for sufijo in ["", "-fanart"]:
            with open(os.path.join(info['directorio'], f"{prefijo}{sufijo}{ext_img}"), 'wb') as f:
                f.write(img_data)
        print("OK.")

    if renombrar:
        nueva_ruta = os.path.join(info['directorio'], f"{nombre_f}{info['extension_video']}")
        if info['original_full_path'] != nueva_ruta:
            print(f"[*] Renombrando a: {nombre_f}{info['extension_video']}")
            os.rename(info['original_full_path'], nueva_ruta)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-n", "--rename", action="store_true")
    args = parser.parse_args()
    ejecutar(args.archivo, args.interactive, args.rename)