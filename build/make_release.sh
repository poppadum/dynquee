#!/bin/bash

#
# Build a release archive
#

# Location of created archive
TARGET=$(dirname "$0")/release.zip

# list of files to include
MANIFEST=$(dirname "$0")/MANIFEST

# exclude my personal files in media/
EXCLUDE='-x!media/generic/astrocade*'

# build archive
if [ -f "$TARGET" ]; then
    # remove existing archive if present
    rm $TARGET
fi
/usr/bin/7z a -tzip $EXCLUDE $TARGET @$MANIFEST
