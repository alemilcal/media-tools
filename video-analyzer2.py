#!/usr/bin/python3
# -*- coding: utf8 -*-

import os, argparse, subprocess, sys, json, glob

VERSION = 'v2.0.0-optimized'
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
parser.add_argument('-a', nargs=2, help='Tag audio track (track_num lang)')
parser.add_argument('-s', nargs=2, help='Tag sub track (track_num lang)')
parser.add_argument('-f', nargs=2, help='Tag sub track as forced (track_num 0/1)')
parser.add_argument('input', nargs='*', help='Input file(s) or wildcards like *.mkv')
parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')
parser.add_argument('-z', '--dry-run', action='store_true', help='Dry run')
args = parser.parse_args()

def get_media_data(filepath):
    """Obtiene toda la info del archivo en una sola llamada JSON (Mucho más rápido)"""
    try:
        cmd = [MEDIAINFO_BIN, '--Output=JSON', filepath]
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return json.loads(result)
    except Exception as e:
        if args.verbose: print(f"Error analizando {filepath}: {e}")
        return None

def analyze_video_file(filepath):
    data = get_media_data(filepath)
    if not data or 'media' not in data: return

    tracks = data['media']['track']
    general = tracks[0]
    
    # Extraer info básica
    filename = os.path.basename(filepath)
    display_name = (filename[:65] + '...') if len(filename) > 68 else filename.ljust(68)

    audio_langs = []
    sub_info = [] # Lista de tuples (lang, forced, title)

    for t in tracks:
        t_type = t.get('@type')
        if t_type == 'Audio':
            audio_langs.append(t.get('Language', 'und')[:3].capitalize())
        elif t_type == 'Text':
            lang = t.get('Language', 'und')[:3].capitalize()
            # Detectar forzado por flag o por título
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

    # Formatear columnas de tracks (máximo 3)
    audios = (audio_langs + ['   ']*3)[:3]
    subs = []
    for i in range(3):
        if i < len(sub_info):
            s = sub_info[i]
            subs.append(f"{s[0]} {'F' if s[1] else ' '} {s[2]:<6}")
        else:
            subs.append("            ")

    print(f"{display_name} | {' '.join(audios)} | {' | '.join(subs)} | {w_string}")

def process_input():
    # El encabezado se mantiene fiel a tu original
    header = "{:68}   {:3} {:3} {:3}   {:12}   {:12}   {:12}   {}".format("File", "Au1", "Au2", "Au3", "Sub1", "Sub2", "Sub3", "WL")
    print(header)
    print("-" * 132)

    # Manejo de comodines para Windows y Linux
    files_to_process = []
    if not args.input:
        for root, _, files in os.walk('.'):
            for f in sorted(files):
                if f.lower().endswith(VXT):
                    files_to_process.append(os.path.join(root, f))
    else:
        for pattern in args.input:
            # glob.glob expande los *.mkv en Windows
            expanded = glob.glob(pattern)
            for f in expanded:
                if f.lower().endswith(VXT):
                    files_to_process.append(f)

    for f in files_to_process:
        analyze_video_file(f)
        # Lógica de edición (mkvpropedit)
        if (args.a or args.s or args.f) and f.lower().endswith('.mkv'):
            apply_edits(f)

def apply_edits(f):
    edit_cmds = []
    if args.a: edit_cmds += ['--edit', f'track:a{args.a[0]}', '--set', f'language={args.a[1]}']
    if args.s: edit_cmds += ['--edit', f'track:s{args.s[0]}', '--set', f'language={args.s[1]}']
    if args.f: edit_cmds += ['--edit', f'track:s{args.f[0]}', '--set', f'flag-forced={args.f[1]}']
    
    full_cmd = [MKVPROPEDIT_BIN, f] + edit_cmds
    if not args.verbose: full_cmd.append('-q')
    
    if args.verbose: print(f"> Executing: {' '.join(full_cmd)}")
    if not args.dry-run: subprocess.run(full_cmd)

if __name__ == '__main__':
    process_input()