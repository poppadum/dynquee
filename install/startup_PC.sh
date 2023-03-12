#!/usr/bin/env bash

# Script to launch dynquee from `/etc/X11/xinit/xinitrc` on Recalbox PC

emulationstation --windowed &
cd /recalbox/share/dynquee
python3 dynquee.py >/dev/null 2>&1 &
