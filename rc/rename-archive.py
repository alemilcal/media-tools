#!/usr/bin/python3
# -*- coding: utf8 -*-

import argparse
import fnmatch
import os
import re
import string
import subprocess

# import qqlib
import sys
import time

if os.name == "posix":
    NICE_BIN = "nice"
else:
    NICE_BIN = ""

# Options:

parser = argparse.ArgumentParser(description="Files normalizing renamer.")
# parser.add_argument('-a',action='store_true',help='process all files and directories (e.g. remove dot files/dirs)')
parser.add_argument("-b", action="store_true", help="remove bracketed strings")
parser.add_argument("-c", action="store_true", help="remove uppercase")
parser.add_argument(
    "-w",
    action="store_true",
    help="wonderful renaming (smart capitalization and spacing)",
)
parser.add_argument(
    "-dy", action="store_true", help="rename file to last modification date"
)
parser.add_argument("-dz", action="store_true", help="rename file to last change date")
parser.add_argument("-m", action="store_true", help="generate movie info files")
parser.add_argument("-md5", action="store_true", help="rename file to md5sum")
parser.add_argument("-j", action="store_true", help="rename jpegs based on EXIF data")
parser.add_argument("-n", nargs=1, help="numerate files with a prefix")
parser.add_argument(
    "-o", action="store_true", help="only output new name (do not actually rename)"
)
parser.add_argument("-r", action="store_true", help="recursive rename")
parser.add_argument("-s", action="store_true", help="remove spaces")
parser.add_argument("-t", action="store_true", help="generate tv show info files")
parser.add_argument("-x", nargs=2, help="replace string (regex)")
parser.add_argument("-y", action="store_true", help="overwrite files without prompt")
parser.add_argument("-z", action="store_true", help="dry run")
parser.add_argument("path", nargs="+", help="initial path")
args = parser.parse_args()


def execute_command(c):
    if NICE_BIN != "":
        c = NICE_BIN + " -n 19 " + c
    print("> Executing: ", c)
    if not args.z:
        os.system(c)


def replace_string(s, a, b):
    r = s.replace(a, b)
    return r


def remove_spaces(s):
    r = s
    r = replace_string(r, " ", "-")
    r = replace_string(r, "_-_", "-")
    r = replace_string(r, "__", "-")
    r = replace_string(r, "--", "-")
    r = replace_string(r, "--", "-")
    r = replace_string(r, "--", "-")
    if r[0] == "_":
        r = r[1:]
    if r[0] == "-":
        r = r[1:]
    return r


def is_file_numerated(p):
    global args
    b = os.path.basename(p)
    t = "%02u" % (int(args.n[0]))
    r = b[:2] == t + "x" or b[:2] == t + "X"
    return r


def is_numerable_file(p):
    b = os.path.basename(p)
    x = os.path.splitext(p)
    e = x[1]
    r = os.path.isfile(p) and b[0] != "." and e != ".nfo"
    return r


def remove_brackets_only(b, c1, c2):
    r = replace_string(b, c1, "")
    r = replace_string(r, c2, "")
    return r


def remove_brackets_full(b, c1, c2):
    x = b
    b = ""
    r = False
    for c in x:
        if not r and c == c1:
            r = True
        if r and c == c2:
            r = False
        if not r and c != c1 and c != c2:
            b += c
    return b


def process_path(p, numfile):

    if os.path.isdir(p) and p != ".." and (args.r or p == "."):
        print("Processing path: ", p)
        d = os.listdir(p)
        d = sorted(d)
        n = 0
        for a in d:
            np = p + "/" + a
            if is_numerable_file(np):
                n += 1
            process_path(np, n)

    a = os.path.basename(p)
    b = a
    if args.x:
        x = fnmatch.translate(args.x[0])
        b = re.sub(args.x[0], args.x[1], b)
    if args.b:
        b = remove_brackets_full(b, "[", "]")
        b = remove_brackets_only(b, "(", ")")
    b = replace_string(b, "á", "a")
    b = replace_string(b, "é", "e")
    b = replace_string(b, "í", "i")
    b = replace_string(b, "ó", "o")
    b = replace_string(b, "ú", "u")
    b = replace_string(b, "ü", "u")
    b = replace_string(b, "ñ", "n")
    b = replace_string(b, "ç", "c")
    b = replace_string(b, "Á", "A")
    b = replace_string(b, "É", "E")
    b = replace_string(b, "Í", "I")
    b = replace_string(b, "Ó", "O")
    b = replace_string(b, "Ú", "U")
    b = replace_string(b, "Ü", "U")
    b = replace_string(b, "Ñ", "N")
    b = replace_string(b, "Ç", "C")
    if args.b:
        b = replace_string(b, "[", "-")
        b = replace_string(b, "]", "-")
    i = b.find(".")
    j = b.rfind(".")
    f = b[i:]
    e = b[j:]
    if os.path.isfile(p):
        e = e.lower()
        e = replace_string(e, ".jpeg", ".jpg")
        e = replace_string(e, ".m4v", ".mp4")
    i = j
    if b[i - 1] == " " or b[i - 1] == "_":
        i -= 1
    b = b[:i] + e
    w = string.ascii_letters + string.digits + " _.-"
    if not args.b:
        w += "()[]"
    x = b
    b = ""
    for c in x:
        if c in w:
            b += c
    if args.w:  # WONDERFUL RENAMING
        nombre = os.path.splitext(b)[0]
        extension = os.path.splitext(b)[1]
        nombre = nombre.title()
        nombre = replace_string(nombre, " - ", "___")
        nombre = replace_string(nombre, "-", " ")
        nombre = replace_string(nombre, "___", " - ")
        extension = extension.lower()
        b = nombre + extension
    if args.c:
        b = b.lower()
    # replace spaces:
    if args.s:
        b = remove_spaces(b)
    # remove "-."
    b = replace_string(b, "-.", ".")
    # numerate file:
    if args.n != None and is_numerable_file(p) and not is_file_numerated(p):
        b = "%02ux%03u_%s" % (int(args.n[0]), numfile, b)
    # rename md5:
    if args.md5:
        proc = subprocess.Popen(
            'md5sum -b "%s" | cut -d " " -f 1' % (p), shell=True, stdout=subprocess.PIPE
        )
        b = proc.stdout.read()
        b = b[:-1] + e
    # rename modification date:
    if args.dy:
        proc = subprocess.Popen(
            'stat -c %%y "%s" | cut -c 1-4,6-7,9-10,12-13,15-16,18-19,21-22' % (p),
            shell=True,
            stdout=subprocess.PIPE,
        )
        b = proc.stdout.read()
        b = b[:-1] + e
    if args.dz:
        proc = subprocess.Popen(
            'stat -c %%z "%s" | cut -c 1-4,6-7,9-10,12-13,15-16,18-19,21-22' % (p),
            shell=True,
            stdout=subprocess.PIPE,
        )
        b = proc.stdout.read()
        b = b[:-1] + e
    ###
    d = os.path.dirname(p)
    if d == "":
        pb = b
    else:
        pb = d + "/" + b
    # generate info files:
    if is_numerable_file(p):
        if args.t and not args.z:
            bn = os.path.splitext(b)
            title = bn[0]
            title = title[5:]
            title = replace_string(title, "_", " ")
            # title=title.title()
            date = os.path.getctime(p)
            date = time.gmtime(date)
            date = "%04u-%02u-%02u" % (date[0], date[1], date[2])
            x = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
            x += "<episodedetails>\n"
            x += "  <title>%s</title>\n" % (title)
            try:
                season_number = int(b[:1])
            except:
                season_number = 1
            try:
                numfile = int(b[2:4])
            except:
                null
            x += "  <season>%s</season>\n" % (season_number)
            x += "  <episode>%u</episode>\n" % (numfile)
            x += "  <aired>%s</aired>\n" % (date)
            x += "</episodedetails>\n"
            pbn = os.path.splitext(pb)
            f = open(pbn[0] + ".nfo", "w")
            f.write(x)
            f.close()
        if args.m and not args.z:
            bn = os.path.splitext(b)
            title = bn[0]
            title = replace_string(title, "_", " ")
            title = title.title()
            x = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
            x += "<movie>\n"
            x += "  <title>%s</title>\n" % (title)
            x += "</movie>\n"
            pbn = os.path.splitext(pb)
            f = open(pbn[0] + ".nfo", "w")
            f.write(x)
            f.close()
    ###
    if a != b:
        fck = pb
        idx = 0
        while (args.dy or args.dz) and os.path.exists(fck):
            fck = pb[:-4] + "%d" % (idx) + e
            idx = idx + 1
        pb = fck
        if args.y:
            c = 'mv "%s" "%s"' % (p, pb)
        else:
            c = 'mv -i "%s" "%s"' % (p, pb)
        if args.o:
            print(os.path.basename(pb))
        else:
            # qqlib.execute_command(c,args.z)
            execute_command(c)
    if args.j:  # jpeg EXIF mode
        c = 'jhead -exonly -nf%%Y-%%m-%%d\ %%H.%%M.%%S "%s";jhead -ft "%s"' % (pb, pb)
        # qqlib.execute_command(c,args.z)
        execute_command(c)


n = 0
for f in args.path:
    if is_numerable_file(f):
        n += 1
    process_path(f, n)
