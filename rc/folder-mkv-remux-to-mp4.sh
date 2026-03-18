#!/bin/bash

find . -name "*.mkv" -exec ~/media-tools/mkv-remux-to-mp4.sh "{}" \;
