#!/bin/bash

# Git filter
# smudge / clean version string in python module

CLEAN_STR='__version__ = "$Version"'
SEARCH_PATTERN='^\s*__version__ *= *".*"'

dir="$(dirname -- "$0")"
version="$($dir/gen_version.sh)"
smudge_pattern="__version__ = \"$version\""

case "$1" in
    --smudge|-s)
        # replace $SEARCH_PATTERN with $replace_pattern
        sed -E "s/$SEARCH_PATTERN/$smudge_pattern/"
        ;;

    --clean|-c)
        # replace $SEARCH_PATTERN with $CLEAN_STR
        sed -E "s/$SEARCH_PATTERN/$CLEAN_STR/"
        ;;
    
    *)
        echo "Usage: $0 [--smudge | --clean]" >&2
        # pass stdin to stdout without change
        cat
        ;;
esac
