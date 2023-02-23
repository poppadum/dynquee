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

# generate temporary BUILD file to include in release
BUILD_FILE=$build_dir/../BUILD
build_num="$($build_dir/gen_build.sh)"
echo "Build number: $build_num"
echo "$build_num" > $BUILD_FILE

# insert build number into module
sed -i -E "s/^\s*__build *= *\".*\"/__build = \"$build_num\"/" $build_dir/../dynquee.py

# build archive
if [ -f "$TARGET" ]; then
    # remove existing archive if present
    rm $TARGET
fi
/usr/bin/7z a -tzip -bd $EXCLUDE $TARGET @$MANIFEST $BUILD_FILE

# remove temporary BUILD file
rm $BUILD_FILE

# remove build number from module
sed -i -E "s/^\s*__build *= *\".*\"/__build = \"develop\"/" $build_dir/../dynquee.py
