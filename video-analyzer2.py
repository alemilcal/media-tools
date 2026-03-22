#!/usr/bin/python3
# -*- coding: utf8 -*-

import os, argparse, subprocess, json, glob, sys

VERSION = 'v3.0.0-mkvmerge'
VXT = ('.mkv', '.mp4', '.m4v', '.mov', '.avi', '.wmv')

# Configuración de binarios (MKVToolNix)
if os.name == 'posix':
    MKVMERGE_BIN = 'mkvmerge'
    MKVPROPEDIT_BIN = 'mkvpropedit'
else:
    BIN_PATH = 'C:/script/bin/'
    MKVMERGE_BIN = f'{BIN_PATH}mkvmerge.exe'
    MKVPROPEDIT_BIN = f'{BIN_PATH}mkvpropedit.exe'

parser = argparse.ArgumentParser(description=f'Video analyzer ({VERSION})')
parser.add_argument('input', nargs='*', help='Archivos o comodines (ej: *.mkv)')
args = parser.parse_args()

def get_track_info(filepath):
    """Usa mkvmerge -J para obtener metadatos instantáneamente"""
    try:
        cmd = [MKVMERGE_BIN, '-J', filepath]
        result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return json.loads(result)
    except:
        return None

def fix_lang(lang):
    """Normaliza idiomas a 3 letras capitalizadas"""
    m = {'und': 'und', 'spa': 'Spa', 'jpn': 'Jpn', 'eng': 'Eng', 'fre': 'Fre', 'ger': 'Ger'}
    l = lang.lower()[:3]
    return m.get(l, l.capitalize())

def analyze_file(filepath):
    data = get_track_info(filepath)
    if not data or 'tracks' not in data: return

    filename = os.path.basename(filepath)
    display_name = (filename[:65] + '...') if len(filename) > 68 else filename.ljust(68)

    audios = []
    subs = []

    for t in data['tracks']:
        t_type = t.get('type')
        props = t.get('properties', {})
        lang = fix_lang(props.get('language', 'und'))
        
        if t_type == 'audio':
            audios.append(lang)
        elif t_type == 'subtitles':
            # Detectar forzado por flag o por nombre del track
            forced = props.get('forced_track') == True or any(x in props.get('track_name', '').lower() for x in ['forz', 'forc'])
            title = props.get('track_name', '')[:6]
            subs.append({'lang': lang, 'forced': forced, 'title': title})

    # Lógica de advertencias (WL)
    has_spa_audio = any(a == 'Spa' for a in audios[:3])
    has_spa_sub_forced = any(s['lang'] == 'Spa' and s['forced'] for s in subs[:3])

    w_val = 0
    if not has_spa_audio: w_val += 2
    if not has_spa_sub_forced: w_val += 1
    w_str = f"W{w_val}" if w_val > 0 else "  "

    # Preparar columnas
    a_cols = (audios + ['   ']*3)[:3]
    s_formatted = []
    for i in range(3):
        if i < len(subs):
            s = subs[i]
            s_formatted.append(f"{s['lang']:<3} {'F' if s['forced'] else ' '} {s['title']:<6}")
        else:
            s_formatted.append("            ")

    print(f"{display_name} | {' '.join(a_cols)} | {' | '.join(s_formatted)} | {w_str}")

def main():
    # Encabezado
    print("{:68}   {:3} {:3} {:3}   {:12}   {:12}   {:12}   {}".format("File", "Au1", "Au2", "Au3", "Sub1", "Sub2", "Sub3", "WL"))
    print("-" * 132)

    # Resolución de archivos (Soporte para Windows *.mkv)
    targets = args.input if args.input else ['.']
    files_to_process = []
    
    for t in targets:
        # glob.glob expande los comodines que Windows no sabe manejar por sí solo
        path_list = glob.glob(t) if '*' in t else ([t] if os.path.isfile(t) else [])
        if not path_list and os.path.isdir(t):
            for root, _, files in os.walk(t):
                for f in files:
                    if f.lower().endswith(VXT):
                        files_to_process.append(os.path.join(root, f))
        else:
            files_to_process.extend([f for f in path_list if f.lower().endswith(VXT)])

    for f in sorted(files_to_process):
        analyze_file(f)

if __name__ == '__main__':
    main()