#!/bin/bash

#
# Build a release archive
#

build_dir=$(dirname "$0")

# Location of created archive
TARGET=$build_dir/dynquee-release.zip

# list of files to include
MANIFEST=$build_dir/MANIFEST

# exclude my personal files in media/ and log files
EXCLUDE='-x!media/generic/astrocade* -x!logs/*'

# build archive
if [ -f "$TARGET" ]; then
    # remove existing archive if present
    rm $TARGET
fi
/usr/bin/7z a -tzip $EXCLUDE $TARGET @$MANIFEST
