#!/usr/bin/env bash

# Script to launch dynquee from `/etc/X11/xinit/xinitrc` on Recalbox PC

emulationstation --windowed &

LOGFILE=/tmp/dynquee_start.log
cd /recalbox/share/dynquee
pwd >>$LOGFILE
python3 -m dynquee >>$LOGFILE 2>&1 &
