#!/usr/bin/python3
# -*- coding: utf8 -*-

import os, argparse, subprocess, json, glob, sys

VERSION = 'v3.1.1-fix'
VXT = ('.mkv', '.mp4', '.m4v', '.mov', '.avi', '.wmv')

# Configuración de binarios
if os.name == 'posix':
    MKVMERGE_BIN = 'mkvmerge'
    MKVPROPEDIT_BIN = 'mkvpropedit'
else:
    BIN_PATH = 'C:/script/bin/'
    MKVMERGE_BIN = f'{BIN_PATH}mkvmerge.exe'
    MKVPROPEDIT_BIN = f'{BIN_PATH}mkvpropedit.exe'

parser = argparse.ArgumentParser(description=f'Video analyzer & editor ({VERSION})')
parser.add_argument('-a', nargs=2, metavar=('TRACK', 'LANG'), help='Cambiar idioma audio (ej: 1 jpn)')
parser.add_argument('-s', nargs=2, metavar=('TRACK', 'LANG'), help='Cambiar idioma sub (ej: 1 spa)')
parser.add_argument('-f', nargs=2, metavar=('TRACK', 'VAL'), help='Set forzado 0/1 (ej: 1 1)')
parser.add_argument('-v', '--verbose', action='store_true', help='Modo detallado')
parser.add_argument('input', nargs='*', help='Archivos o comodines')
args = parser.parse_args()

def fix_lang(lang):
    m = {'und': 'und', 'spa': 'Spa', 'jpn': 'Jpn', 'eng': 'Eng', 'fre': 'Fre', 'ger': 'Ger', 'jp': 'Jpn', 'ja': 'Jpn'}
    l = lang.lower()[:3]
    return m.get(l, l.capitalize())

def analyze_file(filepath):
    if not os.path.exists(filepath):
        print(f"Error: No existe el archivo {filepath}")
        return

    try:
        # Usamos mkvmerge para obtener el JSON
        res = subprocess.check_output([MKVMERGE_BIN, '-J', filepath], stderr=subprocess.DEVNULL)
        data = json.loads(res)
    except Exception as e:
        print(f"Error analizando {os.path.basename(filepath)}. ¿Está instalado mkvmerge?")
        return

    filename = os.path.basename(filepath)
    display_name = (filename[:65] + '...') if len(filename) > 68 else filename.ljust(68)

    audios, subs = [], []
    for t in data.get('tracks', []):
        props = t.get('properties', {})
        lang = fix_lang(props.get('language', 'und'))
        if t['type'] == 'audio':
            audios.append(lang)
        elif t['type'] == 'subtitles':
            forced = props.get('forced_track') == True or 'forz' in props.get('track_name', '').lower()
            subs.append({'l': lang, 'f': forced, 't': props.get('track_name', '')[:6]})

    # Lógica WL (Warning Level)
    w = (0 if any(a == 'Spa' for a in audios[:3]) else 2) + (0 if any(s['l'] == 'Spa' and s['f'] for s in subs[:3]) else 1)
    w_str = f"W{w}" if w > 0 else "  "

    a_cols = (audios + ['   ']*3)[:3]
    s_cols = []
    for i in range(3):
        if i < len(subs):
            s = subs[i]
            s_cols.append(f"{s['l']:<3} {'F' if s['f'] else ' '} {s['t']:<6}")
        else: s_cols.append("            ")

    print(f"{display_name} | {' '.join(a_cols)} | {' | '.join(s_cols)} | {w_str}")

def apply_edits(filepath):
    if not filepath.lower().endswith('.mkv'): return
    cmd = [MKVPROPEDIT_BIN, filepath]
    if args.a: cmd += ['--edit', f'track:a{args.a[0]}', '--set', f'language={args.a[1]}']
    if args.s: cmd += ['--edit', f'track:s{args.s[0]}', '--set', f'language={args.s[1]}']
    if args.f: cmd += ['--edit', f'track:s{args.f[0]}', '--set', f'flag-forced={args.f[1]}']
    if not args.verbose: cmd.append('-q')
    subprocess.run(cmd)

def main():
    targets = args.input if args.input else ['.']
    files = []