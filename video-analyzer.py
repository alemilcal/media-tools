#!/usr/bin/python3
# -*- coding: utf8 -*-

# Imports:

import os, string, argparse, subprocess, sys, shutil, random, time

# Constants:

VERSION = 'v1.6.0'
VXT = ['mkv', 'mp4', 'm4v', 'mov', 'mpg', 'mpeg', 'avi', 'vob', 'mts', 'm2ts', 'wmv', 'flv']
SPANISH = 'Spanish'
ENGLISH = 'English'
JAPANESE = 'Japanese'
UNDETERMINED = 'Undetermined'

if os.name == 'posix':
  FFMPEG_BIN = 'ffmpeg'
  HANDBRAKECLI_BIN = 'HandBrakeCLI'
  MEDIAINFO_BIN = 'mediainfo'
  MKVPROPEDIT_BIN = 'mkvpropedit'
  NICE_BIN = 'nice'
  SED_BIN = 'sed'
  BIFTOOL_BIN = 'biftool'
else:
  BIN_PATH = 'C:/script/bin/'
  FFMPEG_BIN = '%sffmpeg.exe'%(BIN_PATH)
  HANDBRAKECLI_BIN = '%sHandBrakeCLI.exe'%(BIN_PATH)
  MEDIAINFO_BIN = '%sMediaInfo.exe'%(BIN_PATH)
  MKVPROPEDIT_BIN = '%smkvpropedit.exe'%(BIN_PATH)
  NICE_BIN = ''
  SED_BIN = '%ssed.exe'%(BIN_PATH)
  BIFTOOL_BIN = '%sbiftool.exe'%(BIN_PATH)

# Options:

parser = argparse.ArgumentParser(description = 'Video analyzer (%s)'%(VERSION))
parser.add_argument('-a', nargs = 2, help = 'Tag audio track (track number starting at 1 + jpn/lat/spa/und/...)')
parser.add_argument('-s', nargs = 2, help = 'Tag sub track (track number starting at 1 + jpn/lat/spa/und/...)')
parser.add_argument('-f', nargs = 2, help = 'Tag sub track as forced (track number starting at 1 + 0/1)')
#parser.add_argument('-b', action = 'store_true', help = 'Generate BIF files [BETA]')
#parser.add_argument('--vose', action = 'store_true', help = 'Treat subtitle as forced')
parser.add_argument('input', nargs='*', help = 'Input file(s) (if missing process all video files)')
parser.add_argument('--upload', action = 'store_true', help = 'Upload script to GITHUB')
parser.add_argument('-v', action = 'store_true', help = 'Verbose mode')
parser.add_argument('-z', action = 'store_true', help = 'Dry run')
args = parser.parse_args()

# Auxiliar functions:

def utf8_filter(f):
  f = f.replace('á', 'a')
  f = f.replace('é', 'e')
  f = f.replace('í', 'i')
  f = f.replace('ó', 'o')
  f = f.replace('ú', 'u')
  f = f.replace('ü', 'u')
  f = f.replace('ñ', 'n')
  f = f.replace('ç', 'c')
  f = f.replace('Á', 'A')
  f = f.replace('É', 'E')
  f = f.replace('Í', 'I')
  f = f.replace('Ó', 'O')
  f = f.replace('Ú', 'U')
  f = f.replace('Ü', 'U')
  f = f.replace('Ñ', 'N')
  f = f.replace('¿', '')
  f = f.replace('?', '')
  f = f.replace('¡', '')
  f = f.replace('!', '')
  return f

def language_code(name):
  if name == SPANISH:
    return 'spa'
  else:
    if name == ENGLISH:
      return 'eng'
    else:
      if name == JAPANESE:
        return 'jpn'
      else:
        if name == UNDETERMINED:
          return 'und'
        else:
          return 'unk'

def boolean2integer(b):
  if b:
    return 1
  else:
    return 0

# Classes:

class MediaInfo:

  def __init__(self):
    self.audio_codec = []
    self.audio_languages = []
    self.audio_channels = []
    self.audio_descriptions = []
    self.audio_default = []
    self.sub_languages = []
    self.sub_titles = []
    self.sub_formats = []
    self.sub_forced = []

  def audio_tracks_count(self):
    return len(self.audio_languages)

  def sub_tracks_count(self):
    return len(self.sub_languages)

  def print_info(self):
    print('* Media info found:')
    print('- Video width: %d (%dp)'%(self.video_width, self.video_resolution))
    for t in range(0, self.audio_tracks_count()):
      print('- Audio track %d: Codec = %s, Language = %s, Channels = %d, Audio Description = %s, Default = %s'%(t, self.audio_codec[t], self.audio_languages[t], self.audio_channels[t], self.audio_descriptions[t], self.audio_default[t]))
    for t in range(0, self.sub_tracks_count()):
      print('- Subtitle track %d: Language = %s, Format = %s, Forced = %s'%(t, self.sub_languages[t], self.sub_formats[t], self.sub_forced[t]))

  def select_audio_track(self, l):
    #print '* Searching for %s audio track...'%(l)
    r = -1
    for i in range(0, self.audio_tracks_count()):
      if not args.p:
        if (not self.audio_descriptions[i]) and self.audio_languages[i] == l:
          #if (args.d and self.audio_channels[i] == 6) or ((not args.d) and self.audio_channels[i] == 2):
          if self.audio_channels[i] == 2:
            r = i
            break
      else: # Prioritize default audio tracks
        if self.audio_languages[i] == l and self.audio_default[i]:
          r = i
          break
    if r < 0:
      print('* Searching for %s audio track (2nd lap)...'%(l))
      for i in range(0, self.audio_tracks_count()):
        if (not self.audio_descriptions[i]) and self.audio_languages[i] == l:
          r = i
          break
    print('- Audio track selected = %d'%(r))
    return r

  def select_sub_track(self, l, f):
    print('* Searching for %s (Forced = %s) subtitle track...'%(l, f))
    r = -1
    for i in range(0, self.sub_tracks_count()):
      if self.sub_languages[i] == l and not self.sub_formats[i] == 'PGS' and self.sub_forced[i] == f:
        r = i
        break
    print('- Subtitle track selected = %d'%(r))
    return r

class MediaFile:

  def __init__(self, input_file):

    self.input_file = input_file

    # Extension extraction
    #print '* Extracting file name path & extension...'
    r = os.path.splitext(self.input_file)
    n = r[0]
    input_path = r[0].rsplit('/', 1)
    if len(input_path) > 1:
      self.input_path = input_path[0] + '/'
      self.base_input_filename = input_path[1]
    else:
      self.input_path = ''
      self.base_input_filename = input_path[0]
    self.extension = r[1].lower()
    self.extension = self.extension[1:]
    r2 = os.path.splitext(self.base_input_filename)
    pre_ext = r2[1].lower()
    pre_ext = pre_ext[1:]
    if pre_ext == '4k':
      self.base_input_filename = self.base_input_filename[0:-3]
    #print '- Input path: "%s"'%(self.input_path)
    #print '- Base input file name: "%s"'%(self.base_input_filename)
    #print '- Extension: "%s"'%(self.extension)

    # Movie name:
    #tmp_movie_name = self.base_input_filename.split('[')[0]
    tmp_movie_name = self.base_input_filename.split('[')
    #print tmp_movie_name
    #tmp_movie_name = tmp_movie_name.rstrip()
    #tmp_movie_name = tmp_movie_name.split('/')
    #print tmp_movie_name
    #self.movie_name = tmp_movie_name[-1]
    tmp_movie_name = tmp_movie_name[0].rstrip()
    movnamyea = tmp_movie_name
    movnamyea = movnamyea.split('/')
    movnamyea = movnamyea[-1]
    movnamyea = movnamyea.split('\\')
    movnamyea = movnamyea[-1]
    movnam = movnamyea
    self.movie_name = movnam
    #print '- Extracted title: "%s"'%(self.movie_name)

    # Media info extraction
    self.info = MediaInfo()
    if self.extension == 'mkv' or self.extension == 'mp4' or self.extension == 'avi' or self.extension == 'wmv':
      #print '> Extracting file media info...'
      # Video with
      o = subprocess.check_output('%s --Inform="Video;%%Width%%" "%s"'%(MEDIAINFO_BIN, self.input_file), shell=True)
      o = o.decode().rstrip()
      try:
        self.info.video_width = int(o)
      except:
        self.info.video_width = 0
      if self.info.video_width > 1500:
        self.info.video_resolution = 1080
      else:
        self.info.video_resolution = 720
      # Audio tracks count
      o = subprocess.check_output('%s --Inform="General;%%AudioCount%%" "%s"'%(MEDIAINFO_BIN, self.input_file), shell=True)
      o = o.decode().rstrip()
      try:
        audcnt = int(o)
      except:
        audcnt = 0
      #print '- Audio tracks found = %d'%(audcnt)
      # Audio CODECs
      o = subprocess.check_output('%s --Inform="General;%%Audio_Format_List%%" "%s"'%(MEDIAINFO_BIN, self.input_file), shell=True)
      #print '*'+o+'*'
      o = o.decode().rstrip()
      o = o.split(' / ')
      for i in range(0, audcnt):
        self.info.audio_codec.append(o[i])
      # Audio Languages
      o = subprocess.check_output('%s --Inform="General;%%Audio_Language_List%%" "%s"'%(MEDIAINFO_BIN, self.input_file), shell=True)
      o = o.decode().rstrip()
      o = o.split(' / ')
      for i in range(0, audcnt):
        if len(o) >= i + 1:
          if o[i] == '':
            o[i] = 'Unknown'
        else:
          o.append('Unknown')
        self.info.audio_languages.append(o[i])
      # Audio Channels
      o = subprocess.check_output('%s --Inform="Audio;%%Channel(s)%%" "%s"'%(MEDIAINFO_BIN, self.input_file), shell=True)
      #print '*'+o+'*'
      for i in range(0, audcnt):
        try:
          channels_amount = int(o[0:1])
        except:
          channels_amount = 0
        self.info.audio_channels.append(channels_amount)
        if o[1:4] == ' / ':
          o = o[5:]
        else:
          o = o[1:]
      # Audiodescription
      o = subprocess.check_output('%s --Inform="Audio;%%Title%%#@#" "%s"'%(MEDIAINFO_BIN, self.input_file), shell=True)
      s = o.decode().split('#@#')
      for t in range(0, len(s) - 1):
        if ('descri' in s[t].lower()) or ('comenta' in s[t].lower()) or ('comment' in s[t].lower()):
          self.info.audio_descriptions.append(True)
        else:
          self.info.audio_descriptions.append(False)
      # Audio default
      o = subprocess.check_output('%s --Inform="Audio;%%Default%%#@#" "%s"'%(MEDIAINFO_BIN, self.input_file), shell=True)
      o = o.decode().rstrip()
      o = o.split('#@#')
      self.info.audio_default = []
      for i in range(0, len(o) - 1):
        if o[i] == 'Yes':
          self.info.audio_default.append(True)
        else:
          self.info.audio_default.append(False)
      # Subtitle tracks count
      o = subprocess.check_output('%s --Inform="General;%%TextCount%%" "%s"'%(MEDIAINFO_BIN, self.input_file), shell=True)
      o = o.decode().rstrip()
      if o == '':
        subcnt = 0
      else:
        subcnt = int(o)
      #print '- Subtitle tracks found = %d'%(subcnt)
      if subcnt == 0:
        self.info.sub_languages = []
        self.info.sub_forced = []
      else:
        # Subtitle languages
        o = subprocess.check_output('%s --Inform="General;%%Text_Language_List%%" "%s"'%(MEDIAINFO_BIN, self.input_file), shell=True)
        o = o.decode().rstrip()
        o = o.split(' / ')
        self.info.sub_languages = o
        # Subtitle formats
        o = subprocess.check_output('%s --Inform="General;%%Text_Format_List%%" "%s"'%(MEDIAINFO_BIN, self.input_file), shell=True)
        o = o.decode().rstrip()
        o = o.split(' / ')
        self.info.sub_formats = o
        # Subtitle forced (by "Forced" field)
        o = subprocess.check_output('%s --Inform="Text;%%Forced%%/" "%s"'%(MEDIAINFO_BIN, self.input_file), shell=True)
        o = o.decode().rstrip()
        o = o.split('/')
        self.info.sub_forced = []
        for i in range(0, len(o) - 1):
          if o[i] == 'Yes':
            self.info.sub_forced.append(True)
          else:
            self.info.sub_forced.append(False)
        # Subtitle forced (by "Title" field)
        o = subprocess.check_output('%s --Inform="Text;%%Title%%#@#" "%s"'%(MEDIAINFO_BIN, self.input_file), shell=True)
        o = o.decode().rstrip()
        o = o.split('#@#')
        for i in range(0, len(o) - 1):
          if ('forz' in o[i].lower()) or ('forc' in o[i].lower()):
            self.info.sub_forced[i] = True
          self.info.sub_titles.append(utf8_filter(o[i]))
      #self.info.print_info()

# Subroutines:

def colorize_green(s):
  #return '\033[1;32;40m{}\033[0;0m'.format(s)
  #return '\033[0;0;42m{}\033[0;0m'.format(s)
  return s

def colorize_red(s):
  #return '\033[1;31;40m{}\033[0;0m'.format(s)
  #return '\033[0;0;41m{}\033[0;0m'.format(s)
  return s

def colorize_purple(s):
  #return '\033[1;35;40m{}\033[0;0m'.format(s)
  #return '\033[0;0;45m{}\033[0;0m'.format(s)
  return s

def colorize_yellow(s):
  #return '\033[1;33;40m{}\033[0;0m'.format(s)
  #return '\033[0;0;43m{}\033[0;0m'.format(s)
  return s

def colorize_blue(s):
  #return '\033[1;36;40m{}\033[0;0m'.format(s)
  return s

def execute_command(c):
  if NICE_BIN != '':
    c = NICE_BIN + ' ' + c
  if args.v:
    print('> Executing: %s'%(c))
  if not args.z:
    os.system(c)

def print_bar():
  print(colorize_blue('-' * 132))

def analyze_video_file(f):

  v = MediaFile(f)

  if not (v.extension in VXT):
    #print '* ERROR: input file is not a video file (skipping)'
    return

  f = utf8_filter(v.input_file)
  #while len(f) > 68:
  #  f = f[:33] + '...' + f[len(f) - 32:]
  if len(f) > 68:
    f = f[:65] + '...'
  while len(f) < 68:
    f = f + ' '

  a1 = '   '
  a2 = '   '
  a3 = '   '
  s1 = '   '
  s2 = '   '
  s3 = '   '
  f1 = ' '
  f2 = ' '
  f3 = ' '
  t1 = '      '
  t2 = '      '
  t3 = '      '
  if len(v.info.audio_languages) > 0:
    a1 = v.info.audio_languages[0][:3];
  if len(v.info.audio_languages) > 1:
    a2 = v.info.audio_languages[1][:3];
  if len(v.info.audio_languages) > 2:
    a3 = v.info.audio_languages[2][:3];
  if len(v.info.sub_languages) > 0:
    s1 = v.info.sub_languages[0][:3];
    if v.info.sub_forced[0]:
      f1 = 'F'
    t1 = v.info.sub_titles[0][:6];
  if len(v.info.sub_languages) > 1:
    s2 = v.info.sub_languages[1][:3];
    if v.info.sub_forced[1]:
      f2 = 'F'
    t2 = v.info.sub_titles[1][:6];
  if len(v.info.sub_languages) > 2:
    s3 = v.info.sub_languages[2][:3];
    if v.info.sub_forced[2]:
      f3 = 'F'
    t3 = v.info.sub_titles[2][:6];

  audio_spa = False
  sub_spa = False
  if a1 == 'Spa':
    audio_spa = True
  if a2 == 'Spa':
    audio_spa = True
  if a3 == 'Spa':
    audio_spa = True
  if s1 == 'Spa' and f1 == 'F':
    sub_spa = True
  if s2 == 'Spa' and f2 == 'F':
    sub_spa = True
  if s3 == 'Spa' and f3 == 'F':
    sub_spa = True

  w = 0
  if not audio_spa:
    w = w + 2
  if not sub_spa:
    w = w + 1

  if w == 0:
    w_string = '  '
  if w == 1:
    w_string = 'W1'
  if w == 2:
    w_string = 'W2'
  if w >= 3:
    w_string = 'W3'

  salida = '{:68} | {:3} {:3} {:3} | {:3} {} {:6} | {:3} {} {:6} | {:3} {} {:6} | {}'.format(f, a1, a2, a3, s1, f1, t1, s2, f2, t2, s3, f3, t3, w_string)

  if w == 0:
    salida = colorize_green(salida)
  if w == 1:
    salida = colorize_yellow(salida)
  if w == 2:
    salida = colorize_red(salida)
  if w >= 3:
    salida = colorize_purple(salida)

  print(salida)

def process_directory(dir):
  lis = sorted(os.listdir(dir))
  for arc in lis:
    rut = dir + '/' + arc
    if os.path.isdir(rut):
      process_directory(rut)
    else:
      analyze_video_file(rut)

def process_file(f):
  analyze_video_file(f)
  if args.a or args.s or args.f:
    if args.a:
      o = '--edit track:a{} --set language={}'.format(args.a[0], args.a[1])
      if args.v:
        c = '{} "{}" {}'.format(MKVPROPEDIT_BIN, f, o)
      else:
        c = '{} "{}" -q {}'.format(MKVPROPEDIT_BIN, f, o)
      execute_command(c)
    if args.s:
      o = '--edit track:s{} --set language={}'.format(args.s[0], args.s[1])
      if args.v:
        c = '{} "{}" {}'.format(MKVPROPEDIT_BIN, f, o)
      else:
        c = '{} "{}" -q {}'.format(MKVPROPEDIT_BIN, f, o)
      execute_command(c)
    if args.f:
      o = '--edit track:s{} --set flag-forced={}'.format(args.f[0], args.f[1])
      if args.v:
        c = '{} "{}" {}'.format(MKVPROPEDIT_BIN, f, o)
      else:
        c = '{} "{}" -q {}'.format(MKVPROPEDIT_BIN, f, o)
      execute_command(c)
    analyze_video_file(f)
    print_bar()

def verify_software(b, critical):
  if not b == '':
    print('Checking for %s...'%(b),)
    if shutil.which(b) is None:
      if critical:
        sys.exit('MISSING!')
      else:
        print('MISSING! (WARNING)')
    else:
      print('OK')

# Main routine:


if args.upload:
  c = 'cd /home/ale/bin/video-analyzer ; git commit -a -m "%s" ; git push'%(VERSION)
  execute_command(c)
else:
  print
  verify_software(MEDIAINFO_BIN, True)
  verify_software(NICE_BIN, True)
  verify_software(MKVPROPEDIT_BIN, True)
  print
  print(colorize_blue("{:68}   {:3} {:3} {:3}   {:12}   {:12}   {:12}   {}".format("File", "Au1", "Au2", "Au3", "Sub1", "Sub2", "Sub3", "WL")))
  print_bar()
  if args.input:
    for f in args.input:
      process_file(f)
  else:
    process_directory('.')
  print
