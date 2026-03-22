#!/usr/bin/python3
# -*- coding: utf8 -*-

import os, argparse, subprocess, json, glob, sys, shutil

VERSION = 'v3.1.2-robust'
# Extensiones con punto para mayor precisión
VXT = ('.mkv', '.mp4', '.m4v', '.mov', '.avi', '.wmv', '.flv')

# Configuración de binarios
if os.name == 'posix':
    MKVMERGE_BIN = 'mkvmerge'
    MKVPROPEDIT_BIN = 'mkvpropedit'
else:
    BIN_PATH = 'C:/script/bin/'
    MKVMERGE_BIN = os.path.join(BIN_PATH, 'mkvmerge.exe')
    MKVPROPEDIT_BIN = os.path.join(BIN_PATH, 'mkvpropedit.exe')

def check_requirements():
    """Verifica que las herramientas necesarias estén instaladas"""
    for bin_name in [MKVMERGE_BIN, MKVPROPEDIT_BIN]:
        if shutil.which(bin_name) is None:
            print(f"ERROR: No se encuentra '{bin_name}'.")
            print("Por favor, instala MKVToolNix y asegúrate de que esté en el PATH.")
            sys.exit(1)

def fix_lang(lang):
    """Normaliza códigos de idioma a 3 letras capitalizadas"""
    # Mapeos específicos
    m = {'und': 'Und', 'spa': 'Spa', 'jpn': 'Jpn', 'eng': 'Eng', 'fre': 'Fre', 'ger': 'Ger', 'jp': 'Jpn', 'ja': 'Jpn'}
    l = lang.lower()[:3]
    return m.get(l, l.capitalize())

def apply_edits(filepath, args):
    """Aplica cambios de metadatos usando mkvpropedit"""
    if not filepath.lower().endswith('.mkv'): return
    
    cmd = [MKVPROPEDIT_BIN, filepath]
    if args.a: cmd += ['--edit', f'track:a{args.a[0]}', '--set', f'language={args.a[1]}']
    if args.s: cmd += ['--edit', f'track:s{args.s[0]}', '--set', f'language={args.s[1]}']
    if args.f: cmd += ['--edit', f'track:s{args.f[0]}', '--set', f'flag-forced={args.f[1]}']
    
    if not args.verbose: cmd.append('-q')
    subprocess.run(cmd)

def analyze_file(filepath):
    """Analiza y vuelca la info por pantalla"""
    try:
        res = subprocess.check_output([MKVMERGE_BIN, '-J', filepath], stderr=subprocess.DEVNULL)
        data = json.loads(res)
    except:
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
            title = props.get('track_name', '')[:6]
            subs.append({'l': lang, 'f': forced, 't': title})

    # Lógica WL (Warning Level)
    has_spa_audio = any(a == 'Spa' for a in audios[:3])
    has_spa_sub_f = any(s['l'] == 'Spa' and s['f'] for s in subs[:3])
    
    w_val = (0 if has_spa_audio else 2) + (0 if has_spa_sub_f else 1)
    w_str = f"W{w_val}" if w_val > 0 else "  "

    # Formatear columnas
    a_cols = (audios + ['   ']*3)[:3]
    s_cols = []
    for i in range(3):
        if i < len(subs):
            s = subs[i]
            s_cols.append(f"{s['l']:<3} {'F' if s['f'] else ' '} {s['t']:<6}")
        else:
            s_cols.append("            ")

    print(f"{display_name} | {' '.join(a_cols)} | {' | '.join(s_cols)} | {w_str}")

def main():
    parser = argparse.ArgumentParser(description=f'Video analyzer & editor ({VERSION})')
    parser.add_argument('-a', nargs=2, metavar=('TRACK', 'LANG'), help='Cambiar idioma audio (ej: 1 jpn)')
    parser.add_argument('-s', nargs=2, metavar=('TRACK', 'LANG'), help='Cambiar idioma sub (ej: 1 spa)')
    parser.add_argument('-f', nargs=2, metavar=('TRACK', 'VAL'), help='Set forzado 0/1 (ej: 1 1)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Modo detallado')
    parser.add_argument('input', nargs='*', help='Archivos o carpetas')
    args = parser.parse_args()

    check_requirements()

    # Imprimir encabezado inmediatamente
    print("{:68}   {:3} {:3} {:3}   {:12}   {:12}   {:12}   {}".format("File", "Au1", "Au2", "Au3", "Sub1", "Sub2", "Sub3", "WL"))
    print("-" * 132)

    # Recolectar archivos de forma robusta
    targets = args.input if args.input else ['.']
    files_to_process = []

    for t in targets:
        if os.path.isfile(t):
            files_to_process.append(t)
        elif os.path.isdir(t):
            for root, _, files in os.walk(t):
                for f in files:
                    if f.lower().endswith(VXT):
                        files_to_process.append(os.path.join(root, f))
        else:
            # Para wildcards como *.mkv (especialmente útil en Windows)
            found = glob.glob(t)
            for f in found:
                if os.path.isfile(f) and f.lower().endswith(VXT):
                    files_to_process.append(f)

    if not files_to_process:
        print(f"AVISO: No se han encontrado archivos de video en: {targets}")
        return

    for f in sorted(files_to_process):
        if args.a or args.s or args.f:
            apply_edits(f, args)
        analyze_file(f)

if __name__ == '__main__':
    main()