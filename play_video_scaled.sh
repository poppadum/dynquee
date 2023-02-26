#!/usr/bin/env bash

# Play video scaled to marquee height and centred horizontally
#
# requires:
# * ffmpeg & ffprobe
# * sed
# * bc

# uncomment for debug output:
#DEBUG=y

CONFIG_FILE="$(dirname "$0")/dynquee.ini"

error() {
    echo "unable to retrieve video width/height from '$1'"
    exit 1
}

# Get marquee width and height from config file
marquee_width=$(sed -nr 's/^\s*marquee_width *= *(.+)\s*$/\1/p' < "$CONFIG_FILE")
marquee_height=$(sed -nr 's/^\s*marquee_height *= *(.+)\s*$/\1/p' < "$CONFIG_FILE")
# Set default marquee size if not found in config file
if [ -z "$marquee_width" ]; then marquee_width=1280; fi
if [ -z "$marquee_height" ]; then marquee_height=360; fi
[ -n "$DEBUG" ] && echo "DEBUG: marquee_width=$marquee_width marquee_height=$marquee_height" >&2

# Get video size
width=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=s=x:p=0 "$1") \
    || error "$1"
height=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=s=x:p=0 "$1") \
    || error "$1"
[ -n "$DEBUG" ] && echo "DEBUG: width=$width height=$height" >&2

# Calculate X offset to centre video horizontally
height_ratio=$(echo "scale=2; $height / $marquee_height" | bc)
xoffset=$(echo "($marquee_width - ($width / $height_ratio)) / 2" | bc)
[ -n "$DEBUG" ] && echo "DEBUG: xoffset=$xoffset height_ratio=$height_ratio" >&2

# Play video: fork ffmpeg and record pid
ffmpeg \
    -hide_banner \
    -loglevel error \
    -c:v rawvideo \
    -pix_fmt rgb565le \
    -filter:v scale=-2:$marquee_height \
    -f fbdev -xoffset $xoffset /dev/fb0 \
    -re \
    -i "$1" &
pid=$!
[ -n "$DEBUG" ] && echo "ffmpeg pid=$pid"

# stop ffmpeg on SIGINT
trap "kill -INT $pid" SIGINT

# wait for ffmpeg to exit and capture exit code
wait $pid
rc=$?

# exit with ffmpeg's exit code
[ -n "$DEBUG" ] && echo "$0 exit with code $rc"
exit $rc
