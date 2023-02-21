#!/bin/bash

#
# Build a release archive
#

build_dir=$(dirname "$0")

# Location of created archive
TARGET=$build_dir/dynquee.zip

# list of files to include
MANIFEST=$build_dir/MANIFEST

# exclude my personal files in media/ and log files
EXCLUDE='-x!media/generic/astrocade* -x!logs/*'

# warn if working copy has uncommitted changes
if ! git diff-index --quiet HEAD -- ; then
    echo "Warning: working copy is not clean!"
fi

# generate temporary VERSION file to include in release
VERSION_FILE=VERSION
$build_dir/gen_version.sh > $build_dir/../$VERSION_FILE

# build archive
if [ -f "$TARGET" ]; then
    # remove existing archive if present
    rm $TARGET
fi
/usr/bin/7z a -tzip -bd $EXCLUDE $TARGET @$MANIFEST $VERSION_FILE

# remove temporary VERSION file
rm $build_dir/../$VERSION_FILE
