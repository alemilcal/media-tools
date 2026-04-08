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
    """Elimina etiquetas técnicas, calidades y corchetes para la búsqueda."""
    if not texto: return ""
    
    # 1. Eliminar TODO lo que esté dentro de corchetes [] o paréntesis ()
    # Esto quita [VRSpy], [Oculus], [4K], etc.
    texto = re.sub(r'[\[\(\].*?[\]\)]', '', texto)
    
    # 2. Etiquetas de calidad y técnica comunes
    tags = [
        r'\b\d{3,4}p\b', r'\b(480|720|1080|2160)\b', r'\b\d[kK]\b', 
        r'\bx26[45]\b', r'\bhevc\b', r'\bbrrip\b', r'\bwebrip\b', 
        r'\bq\d{2}\b', r'\bpart\d\b'
    ]
    for tag in tags:
        texto = re.sub(tag, '', texto, flags=re.IGNORECASE)
    
    # 3. Limpiar símbolos y dejar solo palabras
    texto = re.sub(r'[\._\-]', ' ', texto)
    return " ".join(texto.split()).strip()

def extraer_datos_locales(ruta_completa):
    path_abs = os.path.abspath(ruta_completa)
    estudio_carpeta = os.path.basename(os.path.dirname(path_abs))
    nombre_archivo = os.path.basename(path_abs)
    
    # Captura de extensión y etiqueta técnica final (ej: .q20.mp4)
    match_ext = re.search(r'\.([a-z0-9]+)\.(mp4|mkv|avi|wmv|mov|flv)$', nombre_archivo, flags=re.IGNORECASE)
    if match_ext:
        tag_tecnico = f" [{match_ext.group(1).upper()}]"
        ext_video = f".{match_ext.group(2)}"
        nombre_sin_ext = nombre_archivo[:match_ext.start()]
    else:
        tag_tecnico = ""
        nombre_sin_ext, ext_video = os.path.splitext(nombre_archivo)
    
    # Detección de fecha
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
        "estudio_local": estudio_carpeta,
        "estudio_busqueda": limpiar_basura(estudio_carpeta),
        "fecha": fecha_norm,
        "titulo_sucio": nombre_sin_ext,
        "original_full_path": path_abs,
        "ext_video": ext_video,
        "tag_tecnico": tag_tecnico,
        "directorio": os.path.dirname(path_abs)
    }

def realizar_peticion(params):
    headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(SEARCH_URL, headers=headers, params=params, timeout=12)
        return resp.json().get('data', [])
    except: return []

def buscar_inteligente(info):
    """Prueba varias combinaciones de búsqueda para archivos difíciles."""
    estudio = info['estudio_busqueda']
    # Limpiamos el título de corchetes y tags
    titulo_limpio = limpiar_basura(info['titulo_sucio'])
    
    # 1. Búsqueda exacta (Sitio + Título + Fecha)
    print(f"[*] Intentando búsqueda estricta: '{titulo_limpio}' en '{estudio}'...")
    p = {"site": estudio, "q": titulo_limpio}
    if info['fecha']: p["date"] = info['fecha']
    res = realizar_peticion(p)
    if res: return res

    # 2. Si hay un guion " - ", intentar solo con la parte derecha (título real)
    if " - " in titulo_limpio:
        partes = titulo_limpio.split(" - ")
        solo_titulo = partes[-1].strip()
        print(f"[*] Intentando solo con título: '{solo_titulo}'...")
        res = realizar_peticion({"site": estudio, "q": solo_titulo})
        if res: return res

    # 3. Búsqueda global sin estudio (por si el nombre de carpeta no es exacto)
    print(f"[*] Intentando búsqueda global por título...")
    res = realizar_peticion({"q": titulo_limpio})
    if res: return res

    return []

def ejecutar(archivo_input, interactivo=False, renombrar=False):
    info = extraer_datos_locales(archivo_input)
    print(f"\n[*] ANALIZANDO: {archivo_input}")

    resultados = buscar_inteligente(info)
    
    if not resultados:
        print("[!] No se encontró nada. Prueba con el modo interactivo (-i) para búsqueda manual.")
        if interactivo:
            manual = input("[?] Introduce búsqueda manual: ")
            if manual: resultados = realizar_peticion({"q": manual})
        if not resultados: return

    # Selección
    if interactivo:
        print(f"\n[?] Opciones encontradas:")
        for i, r in enumerate(resultados[:10]):
            p = r.get('performers', [])
            act = p[0]['name'] if p else "N/A"
            print(f"  {i+1}. [{r['id']}] {r['date']} | {act} | {r['title']}")
        sel = int(input("\nSelecciona número (0 para cancelar): ") or 1)
        if sel == 0: return
        escena = resultados[sel-1]
    else:
        escena = resultados[0]

    # Datos finales
    est_api = escena.get('site', {}).get('name', info['estudio_busqueda'])
    fecha_api = escena.get('date', '0000-00-00')
    tit_api = escena.get('title', 'N/A')
    perf = escena.get('performers', [])
    actriz = f" - {perf[0]['name']}" if perf else ""

    # Formato: Estudio YYYY-MM-DD Titulo - Actriz [TAG]
    nombre_base_f = re.sub(r'[\\/:*?"<>|]', '', f"{est_api} {fecha_api} {tit_api}{actriz}{info['tag_tecnico']}")
    prefijo = nombre_base_f if renombrar else os.path.splitext(os.path.basename(archivo_input))[0]

    # Imágenes
    img_url = escena.get('image')
    if img_url:
        print(f"[*] Descargando imágenes ID {escena['id']}...", end=' ', flush=True)
        img_data = requests.get(img_url).content
        ext_img = os.path.splitext(img_url.split('?')[0])[1] or ".jpg"
        for suf in ["", "-fanart"]:
            nom_img = f"{prefijo}{suf}{ext_img}"
            with open(os.path.join(info['directorio'], nom_img), 'wb') as f:
                f.write(img_data)
        print("OK.")

    # Renombrar
    if renombrar:
        nueva_ruta = os.path.join(info['directorio'], f"{nombre_base_f}{info['ext_video']}")
        if info['original_full_path'] != nueva_ruta:
            print(f"[*] Renombrando a: {nombre_base_f}{info['ext_video']}")
            os.rename(info['original_full_path'], nueva_ruta)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-n", "--rename", action="store_true")
    args = parser.parse_args()
    ejecutar(args.archivo, args.interactive, args.rename)