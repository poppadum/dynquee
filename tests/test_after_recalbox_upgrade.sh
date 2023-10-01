#!/usr/bin/env bash

# Base dynquee directory
BASEDIR=/net/bungle/chris/projects/Astrocade_2022/dynquee

# Recalbox version of xmlstarlet is called 'xml': create alias for testing
shopt -s expand_aliases
alias xml='xmlstarlet'

source ./install/install_common.sh
source ./tests/install_common.sh

cd $BASEDIR || error "cannot change to $BASEDIR"

# Test RPi
install_rpi_init $BASEDIR/tests/init.d

# Test PC
recordScreenLayout "$XRANDR_CMD_FILE"
fixOpenboxConfig
xrandr_cmd=$(< "$XRANDR_CMD_FILE")
fixXinitrc "$xrandr_cmd"