#!/usr/bin/env bash

# Play video scaled to marquee height and centred horizontally
# args:
#  $1: path to video file
#
# requires:
# * ffmpeg & ffprobe
# * sed
# * bc

CONFIG_FILE="$(dirname "$0")/dynquee.ini"
LOG_FILE="$(dirname "$0")/logs/play_video_scaled.log"

pid="n/a"

error() {
    echo "unable to retrieve video width/height from '$1'"
    exit 1
}

# output message to log file and stderr
log() {
    echo $@ >&2
    echo $@ >> $LOG_FILE
}

# kill ffmpeg process
kill_child() {
    log "killing child process pid=$pid"
    kill $pid

}

# wait for ffmpeg to exit and capture exit code
end() {
    log "wait for pid=$pid to exit"
    wait -f $pid
    rc=$?
    # exit with ffmpeg's exit code
    log "$0 exit with code $rc"
    exit $rc
}


# Get marquee width and height from config file
marquee_width=$(sed --silent --regexp-extended 's/^\s*marquee_width *= *(.+)\s*$/\1/p' < "$CONFIG_FILE")
marquee_height=$(sed --silent --regexp-extended 's/^\s*marquee_height *= *(.+)\s*$/\1/p' < "$CONFIG_FILE")
# Set default marquee size if not found in config file
if [ -z "$marquee_width" ]; then marquee_width=1280; fi
if [ -z "$marquee_height" ]; then marquee_height=360; fi

# Get video file dimensions
dimensions=$( \
    ffprobe \
    -loglevel error \
    -select_streams v:0 \
    -show_entries stream=width,height -of csv=s=x:p=0 \
    "$1"
) || error "$1"
width=${dimensions%x*}
height=${dimensions#*x}

# Calculate X offset to centre video horizontally
height_ratio=$(echo "scale=5; $height / $marquee_height" | bc)
xoffset=$(echo "($marquee_width - ($width * 2/ $height_ratio)) / 2" | bc)
log "'$1' w=$width h=$height xoffset=$xoffset height_ratio=$height_ratio marquee:${marquee_width}x${marquee_height}"

# Stop ffmpeg on SIGINT or SIGTERM
trap "kill_child" SIGINT SIGTERM
# Report exit code on EXIT
trap "end" EXIT

# Play video: fork ffmpeg and record pid
ffmpeg \
    -hide_banner \
    -loglevel error \
    -c:v rawvideo \
    -pix_fmt rgb565le \
    -filter:v scale=iw*2/$height_ratio:$marquee_height \
    -f fbdev -xoffset $xoffset /dev/fb0 \
    -re \
    -i "$1" &
pid=$!
log "fork ffmpeg pid=$pid"
