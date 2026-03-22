#!/usr/bin/python3
# -*- coding: utf8 -*-

import os, argparse, subprocess, sys, json, glob

VERSION = 'v2.1.0-turbo'
VXT = ('.mkv', '.mp4', '.m4v', '.mov', '.mpg', '.mpeg', '.avi', '.vob', '.mts', '.m2ts', '.wmv', '.flv')

# Configuración de binarios
if os.name == 'posix':
    MEDIAINFO_BIN = 'mediainfo'
    MKVPROPEDIT_BIN = 'mkvpropedit'
else:
    BIN_PATH = 'C:/script/bin/'
    MEDIAINFO_BIN = f'{BIN_PATH}MediaInfo.exe'
    MKVPROPEDIT_BIN = f'{BIN_PATH}mkvpropedit.exe'

parser = argparse.ArgumentParser(description=f'Video analyzer ({VERSION})')
parser.add_argument('input', nargs='*', help='Input file(s) or wildcards like *.mkv')
parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')
args = parser.parse_args()

def get_all_media_data(file_list):
    """Ejecuta MediaInfo UNA SOLA VEZ para todos los archivos (Máxima velocidad)"""
    if not file_list: return []
    try:
        # Pasamos la lista completa de archivos a mediainfo de una tacada
        cmd = [MEDIAINFO_BIN, '--Output=JSON'] + file_list
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        data = json.loads(result)
        
        # MediaInfo devuelve un objeto si es uno, o una lista si son varios
        media_info = data.get('media', [])
        return media_info if isinstance(media_info, list) else [media_info]
    except Exception as e:
        if args.verbose: print(f"Error en análisis masivo: {e}")
        return []

def format_lang(track):
    """Extrae el código de 3 letras (ISO 639-2) y lo capitaliza"""
    # Intentamos obtener el código de 3 letras directamente de MediaInfo
    lang = track.get('Language_ISO639_2') or track.get('Language') or 'und'
    # Forzamos mapeos comunes si vienen en 2 letras
    mapping = {'ja': 'Jpn', 'en': 'Eng', 'es': 'Spa'}
    lang = lang[:3].lower()
    return mapping.get(lang[:2], lang.capitalize())

def analyze_batch(media_objects):
    header = "{:68}   {:3} {:3} {:3}   {:12}   {:12}   {:12}   {}".format("File", "Au1", "Au2", "Au3", "Sub1", "Sub2", "Sub3", "WL")
    print(header)
    print("-" * 132)

    for media in media_objects:
        tracks = media.get('track', [])
        general = tracks[0] if tracks else {}
        filepath = general.get('CompleteName', 'Unknown')
        filename = os.path.basename(filepath)
        
        display_name = (filename[:65] + '...') if len(filename) > 68 else filename.ljust(68)

        audio_langs = []
        sub_info = []

        for t in tracks:
            t_type = t.get('@type')
            if t_type == 'Audio':
                audio_langs.append(format_lang(t))
            elif t_type == 'Text':
                lang = format_lang(t)
                is_forced = t.get('Forced') == 'Yes' or any(x in t.get('Title', '').lower() for x in ['forz', 'forc'])
                title = t.get('Title', '')[:6]
                sub_info.append((lang, is_forced, title))

        # Lógica de avisos (WL)
        audio_spa = any(a == 'Spa' for a in audio_langs[:3])
        sub_spa_forced = any(s[0] == 'Spa' and s[1] for s in sub_info[:3])

        w_val = 0
        if not audio_spa: w_val += 2
        if not sub_spa_forced: w_val += 1
        w_string = f"W{w_val}" if w_val > 0 else "  "

        audios = (audio_langs + ['   ']*3)[:3]
        subs = []
        for i in range(3):
            if i < len(sub_info):
                s = sub_info[i]
                subs.append(f"{s[0]:<3} {'F' if s[1] else ' '} {s[2]:<6}")
            else:
                subs.append("            ")

        print(f"{display_name} | {' '.join(audios)} | {' | '.join(subs)} | {w_string}")

def main():
    files_to_process = []
    
    # 1. Recolección de archivos (ahora con glob para Windows)
    targets = args.input if args.input else ['.']
    for item in targets:
        if os.path.isdir(item):
            for root, _, files in os.walk(item):
                for f in files:
                    if f.lower().endswith(VXT):
                        files_to_process.append(os.path.abspath(os.path.join(root, f)))
        else:
            for f in glob.glob(item):
                if f.lower().endswith(VXT):
                    files_to_process.append(os.path.abspath(f))

    if not files_to_process:
        print("No se encontraron archivos de video.")
        return

    # 2. Análisis en un solo bloque (Batch processing)
    # Dividimos en grupos de 50 para no exceder el límite de caracteres de la terminal
    batch_size = 50
    for i in range(0, len(files_to_process), batch_size):
        chunk = files_to_process[i:i + batch_size]
        media_data = get_all_media_data(chunk)
        analyze_batch(media_data)

if __name__ == '__main__':
    main()