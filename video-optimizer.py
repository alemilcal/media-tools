#!/usr/bin/python3
# -*- coding: utf8 -*-


import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import traceback

################################################################################
# Globales:
################################################################################


AUDIO_BITRATE = "128"
AUDIO_BITRATE_LQ = "32"
AUDIO_CODEC = "aac"
VIDEO_WIDTH = "1280"
VIDEO_WIDTH_LQ = "640"
VIDEO_CODEC = "libx264"
VIDEO_PRESET = "faster"
VIDEO_PROFILE = "high"
VIDEO_QUALITY = "20"
VIDEO_QUALITY_LQ = "26"
RE_TAGS = re.compile(r"\{[^{}]*\}")
RE_UNKNOWN = re.compile(
    r"[\u3040-\u309F\u30A0-\u30FF\u4300-\u9faf\u3000-\u30ff\uff00-\uffff]"
)
RE_ITALIC = re.compile(r"\\i1(?!\d)")
FFMPEG_HIDE = ""

FFMPEG_BIN = "ffmpeg"
MEDIAINFO_BIN = "mediainfo"
#MKVPROPEDIT_BIN = "mkvpropedit"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUBTITLE_CONVERTER_PY = os.path.join(BASE_DIR, "subtitle-converter.py")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    
if not os.name == "posix":
    FFMPEG_BIN = f"{FFMPEG_BIN}.exe"
    MEDIAINFO_BIN = f"{MEDIAINFO_BIN}.exe"
    #MKVPROPEDIT_BIN = f"{MKVPROPEDIT_BIN}.exe"

InputFileName = ""
OutputFileName = ""
SuccessFileName = ""
ErrorFileName = ""
AudioTracks = []
SubtitleTracks = []
AudioTrackSelected = []
SubtitleTrackSelected = []

################################################################################
# Codigo principal:
################################################################################


def main():

    global InputFileName
    global OutputFileName
    global SuccessFileName
    global ErrorFileName
    global args

    descripcion = "Video/Subtitle Optimizer"
    parser = argparse.ArgumentParser(description=descripcion)
    parser.add_argument("-c", action="store_true", help="cartoon mode")
    parser.add_argument("-l", action="store_true", help="low quality mode")
    parser.add_argument("-r", action="store_true", help="remux only (no transcode)")
    parser.add_argument("-v", action="store_true", help="verbose mode")
    parser.add_argument("-x", action="store_true", help="extract subtitle tracks only")
    parser.add_argument("-z", action="store_true", help="dry run")
    parser.add_argument("input", nargs=1, help="input file")
    parser.add_argument("output", nargs=1, help="output file")
    args = parser.parse_args()
    print(f"{descripcion}...")
    if len(sys.argv) < 3:
        print(f"Uso: {sys.argv[0]} <archivo_entrada.mkv> <archivo_salida.mkv>")
    else:
        if args.v:
            FFMPEG_HIDE = "-hide_banner -loglevel warning"
        InputFileName = args.input[0]
        OutputFileName = args.output[0]
        SuccessFileName = os.path.splitext(InputFileName)[0] + ".ok"
        ErrorFileName = os.path.splitext(InputFileName)[0] + ".err"
        if os.path.exists(SuccessFileName):
            print(f'WARNING: Input file "{InputFileName}" already procesed (OK exists)')
        elif os.path.exists(OutputFileName):
            print(f'WARNING: Output file "{OutputFileName}" exists')
        else:
            convertVideo()


def convertVideo():

    getAudioInfo()
    getAudioTrack()
    getSubtitleInfo()
    getSubtitleTrack()

    o = "-movflags +faststart -sn -map_metadata -1 -map_chapters -1"
    if args.r:
        o += " -c copy -map 0:v -map 0:a"
    else:
        tune = "animation" if args.c else "film"
        videoWidth    = VIDEO_WIDTH_LQ   if args.l else VIDEO_WIDTH
        videoQuality  = VIDEO_QUALITY_LQ if args.l else VIDEO_QUALITY
        audioBitrate  = AUDIO_BITRATE_LQ if args.l else AUDIO_BITRATE
        audioChannels = 1                if args.l else 2
        audioSampling = "-ar 22050"      if args.l else ""
        o = (
            f" -c:v {VIDEO_CODEC} -preset faster -profile:v high -max_muxing_queue_size 9999"
            f" -crf {videoQuality} -tune {tune} -vf scale='{videoWidth}:-2',format=yuv420p -map 0:v:0"
            f" -c:a {AUDIO_CODEC} -ac {audioChannels} -b:a {audioBitrate}k {audioSampling}"
        )
        #print(AudioTrackSelected)
        #print(AudioTracks)
        for k in range(len(AudioTrackSelected)):
            c = languageCode3Char(AudioTracks[AudioTrackSelected[k]]["language"])
            o += f" -map 0:a:{AudioTracks[k]['id']} -metadata:s:a:{k} language={c}"
    for k in SubtitleTrackSelected:
        extractSubtitleTrack(SubtitleTracks[k]["id"])

    if not args.x:
        try:
            # 1. Creamos el temporal y lo cerramos al instante para liberar el bloqueo en Windows
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tmp_path = tmp.name
            tmp.close()

            try:
                # 2. Ejecutamos FFMPEG sobre la ruta (ya no hay bloqueo)
                executeCommand(
                    f'{FFMPEG_BIN} {FFMPEG_HIDE} -y -i "{InputFileName}" {o} "{tmp_path}"'
                )

                # 3. Ejecutamos mkvpropedit
                #for k in range(len(AudioTrackSelected)):
                #    c = languageCode3Char(
                #        AudioTracks[AudioTrackSelected[k]]["language"]
                #    )
                #    executeCommand(
                #        f'{MKVPROPEDIT_BIN} "{tmp_path}" --edit track:a{k + 1} --set language={c}'
                #    )

                # 4. Movemos el archivo final
                output_dir = os.path.dirname(OutputFileName)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                shutil.move(tmp_path, OutputFileName)

            except Exception as e:
                # Si algo falla, limpiamos el temporal manualmente ya que delete=False
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise e

            success_path = pathlib.Path(SuccessFileName)
            success_path.parent.mkdir(parents=True, exist_ok=True)
            success_path.touch(exist_ok=True)
        except Exception as e:
            print(f"Error detectado: {e}")
            traceback.print_exc()
            error_path = pathlib.Path(ErrorFileName)
            error_path.parent.mkdir(parents=True, exist_ok=True)
            error_path.touch(exist_ok=True)


################################################################################
# Subrutinas:
################################################################################


def executeCommand(c):

    print(f"Executing command: {c}")
    r = False
    if not args.z:
        r = os.system(f"nice -n 19 ionice -c 3 {c}" if os.name == "posix" else c)
    print(f"Exit code: {r}")
    if r:
        pathlib.Path(ErrorFileName).touch(exist_ok=True)


def extractSubtitleTrack(t):

    p = pathlib.Path(OutputFileName)
    b = p.stem
    l = "." + SubtitleTracks[t]["language"][0:2]
    f = ".forced" if SubtitleTracks[t]["forced"] else ""
    e = ".srt" if SubtitleTracks[t]["codec"] == "utf-8" else ".ass"
    a0 = p.parent / f"{b}{l}{f}"
    a1 = f"{a0}{e}.bak"
    a2 = f"{a0}.srt"
    executeCommand(
        f'{FFMPEG_BIN} {FFMPEG_HIDE} -y -i "{InputFileName}" -vn -an -c:s copy -map 0:s:{t} -f {"ass" if e == ".ass" else "srt"} "{a1}"'
    )
    executeCommand(f'{SUBTITLE_CONVERTER_PY} "{a1}" "{a2}"')


def getAudioInfo():

    global AudioTracks

    t = mediaInfoQuery("Audio", "Title")
    l = mediaInfoQuery("Audio", "Language")
    p = [0] * len(t)

    for k in range(len(t)):
        if "lat" in t[k] or l[k] == "la" or "lat" in l[k]:
            l[k] = "es-419"
        elif l[k] == "es" or any(x in t[k] for x in ["castellano", "(es)", "spa"]):
            l[k] = "es-es"
        elif l[k][0:3] == "es-":
            l[k] = "es-419"
        elif l[k][0:2] == "en":
            l[k] = "en-us"
        elif l[k][0:2] == "jp":
            l[k] = "ja-jp"

        p[k] = 0
        if l[k] == "es-es":
            p[k] += 400
        if l[k] == "es-419":
            p[k] += 300
        if l[k] == "en-us":
            p[k] += 200
        if l[k] == "ja-jp":
            p[k] += 100
        if "coment" in t[k] or "comment" in t[k]:
            p[k] -= 10

    for k in range(len(t)):
        AudioTracks.append({"id": k, "title": t[k], "language": l[k], "points": p[k]})


def getAudioTrack():

    global AudioTrackSelected

    searchGroups = [
        [("es-es"), ("es-419")],
        [("en-us")],
        [("ja-jp")],
    ]

    for g in searchGroups:
        w = None
        for l in g:
            c = [k for k in AudioTracks if k["language"] == l and k["points"] > 0]
            if c:
                c.sort(key=lambda x: x["points"], reverse=True)
                w = c[0]["id"]
                break
        if w is not None and w not in AudioTrackSelected:
            AudioTrackSelected.append(w)

    if len(AudioTrackSelected) == 0:
        AudioTrackSelected.append(0)

    for k in range(len(AudioTracks)):
        s = " *" if k in AudioTrackSelected else ""
        print(
            f"Audio Track {k}: Title = {AudioTracks[k]['title']}, "
            f"Language = {AudioTracks[k]['language']}, "
            f"Points = {AudioTracks[k]['points']}{s}"
        )


def getSubtitleInfo():

    global SubtitleTracks

    t = mediaInfoQuery("Text", "Title")
    l = mediaInfoQuery("Text", "Language")
    c = mediaInfoQuery("Text", "Format")
    f = mediaInfoQuery("Text", "Forced")
    p = [0] * len(t)

    for k in range(len(t)):
        if any(x in t[k] for x in ["forc", "forz"]):
            f[k] = "yes"
        if "lat" in t[k]:
            l[k] = "es-419"
        elif l[k] == "es" or any(x in t[k] for x in ["castellano", "(es)", "spa"]):
            l[k] = "es-es"
        elif l[k][0:2] == "en":
            l[k] = "en-us"
        if c[k] == "pgs":
            l[k] = "NOT VALID (PGS)"
        if c[k] == "vobsub":
            l[k] = "NOT VALID (VOBSUB FORMAT)"

        p[k] = 0
        if l[k] == "es-es":
            p[k] += 300
        if l[k] == "es-419":
            p[k] += 200
        if l[k] == "en-us":
            p[k] += 100
        if f[k] == "yes":
            p[k] += 50
        if c[k] != "utf-8":
            p[k] -= 20
        if "sdh" in t[k]:
            p[k] -= 10
        if "coment" in t[k] or "comment" in t[k]:
            p[k] -= 10

    for k in range(len(t)):
        SubtitleTracks.append(
            {
                "id": k,
                "language": l[k],
                "codec": c[k],
                "forced": f[k] == "yes",
                "points": p[k],
            }
        )


def getSubtitleTrack():

    global SubtitleTrackSelected

    searchGroups = [
        [("es-es", True), ("es-419", True)],
        [("es-es", False), ("es-419", False)],
        [("en-us", True)],
        [("en-us", False)],
    ]

    for g in searchGroups:
        w = None
        for l, f in g:
            c = [
                k
                for k in SubtitleTracks
                if k["language"] == l and k["forced"] == f and k["points"] > 0
            ]
            if c:
                c.sort(key=lambda x: x["points"], reverse=True)
                w = c[0]["id"]
                break
        if w is not None and w not in SubtitleTrackSelected:
            SubtitleTrackSelected.append(w)

    for k in range(len(SubtitleTracks)):
        s = " *" if k in SubtitleTrackSelected else ""
        print(
            f"Subtitle Track {k}: Language = {SubtitleTracks[k]['language']}, "
            f"CODEC = {SubtitleTracks[k]['codec']}, "
            f"Forced = {SubtitleTracks[k]['forced']}, "
            f"Points = {SubtitleTracks[k]['points']}{s}"
        )


def languageCode3Char(code):
    if code[0:2] == "es":
        return "spa"
    elif code[0:2] == "en":
        return "eng"
    elif code[0:2] == "ja":
        return "jpn"
    else:
        return "und"


def mediaInfoQuery(section, query):

    o = subprocess.check_output(
        f'{MEDIAINFO_BIN} --Inform="{section};%{query}%#*@" "{InputFileName}"',
        shell=True,
    )
    r = o.decode().lower().strip().split("#*@")[:-1]
    return r


################################################################################
# Main call:
################################################################################

if __name__ == "__main__":
    main()
