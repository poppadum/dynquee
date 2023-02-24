#!/usr/bin/env bash

# Fetch latest version of recalbox-next theme's system logos from gitlab


REPO_URL=https://gitlab.com/recalbox/recalbox-themes/-/archive/master/recalbox-themes-master.tar.bz2?path=themes/recalbox-next

basedir=$(dirname "$0")
echo "basedir=$basedir"

OUTFILE="$basedir/recalbox-themes-master.tar.bz2"

echo "Fetching latest version of recalbox-next theme from gitlab"
wget --output-document="$OUTFILE" --show-progress $REPO_URL && \

echo "extracting logo.svg & console.svg files to recalbox-next/" ; 
echo tar -jxvf "$OUTFILE" --strip-components=2 --wildcards --no-anchored 'logo.svg' 'console.svg' --directory="$basedir/" && \

if [ -f "$OUTFILE" ]; then rm "$OUTFILE"; fi