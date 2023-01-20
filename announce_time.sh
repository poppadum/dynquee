#!/bin/bash

for i in {1..3}
do
    printf "the time is %s\n" $(date +'%H:%M:%S')
    sleep 5
done
echo $0 end at $(date) >&2