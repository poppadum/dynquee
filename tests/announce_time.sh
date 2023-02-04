#!/bin/bash

# Announce time repeatedly on stdout
#
# Options:
# -c n: stop after n announcements (default 50)
# -d x: wait x seconds between announcements (default 5s)


# defaults:
stopafter=50
delay=5

# read cmdline opts
while(($#)) ; do
    case "$1" in
        "-c")
            stopafter="$2"
            shift; shift
            ;;
        "-d")
            delay="$2"
            shift; shift
            ;;
    esac
done

echo "Announcing time every ${delay}s, exiting after $stopafter announcements" >&2
for i in $(seq 1 $stopafter)
do
    printf "the time is %s (%02d)\n" $(date +'%H:%M:%S') $i
    sleep $delay
done
echo $0 end at $(date) >&2