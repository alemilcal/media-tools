#!/usr/bin/python3
# -*- coding: utf8 -*-

import argparse, os, sys

MEDIAINFO_BIN = "mediainfo" if os.name == "posix" else "MediaInfo.exe"

parser = argparse.ArgumentParser(description = 'Video Information')
parser.add_argument('input', nargs=1, help = 'input file')
args = parser.parse_args()

os.system(f'{MEDIAINFO_BIN} "%s" | less'%(args.input[0]))
