#!/usr/bin/env bash

# *** For testing ***
# changes to install_common.sh constants for testing only

# Base dynquee directory
BASEDIR=/net/bungle/chris/projects/Retrocade_2022/dynquee

# Test config files
OPENBOX_CFG=$BASEDIR/tests/rc.xml
XINITRC=$BASEDIR/tests/xinitrc


# make a copy of the original files to test on
cp -v $BASEDIR/tests/rc.xml.orig $BASEDIR/tests/rc.xml
cp -v $BASEDIR/tests/xinitrc.orig $BASEDIR/tests/xinitrc
chmod u+w $BASEDIR/tests/rc.xml $BASEDIR/tests/xinitrc
