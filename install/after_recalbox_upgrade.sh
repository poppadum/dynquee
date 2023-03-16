#!/usr/bin/env bash

# Run this script after a Recalbox upgrade to restore changes
# that Recalbox has overwritten

readonly XRANDR_CMD_FILE=xrandr_cmd.txt
BASEDIR=/recalbox/share/dynquee


# Are we on RPi, PC or something else?
arch=$(cat /recalbox/recalbox.arch) || error

# FOR TESTING ONLY:
#arch=x86_64
#arch=rpi4_x64
echo "Detected arch: $arch"

# Include library functions
source $BASEDIR/install/install_common.sh

# FOR TESTING ONLY:
#source ./tests/install_common.sh

cd $BASEDIR || error "cannot change to $BASEDIR"
remountRootRW

case "$arch" in
    x86*)
        recordScreenLayout "$XRANDR_CMD_FILE"
        fixOpenboxConfig
        xrandr_cmd=$(< "$XRANDR_CMD_FILE")
        fixXinitrc "$xrandr_cmd"
        ;;
    rpi*)
        install_rpi_init
        ;;
    *)
        # e.g. odroidxu4, odroidgo
        echo "dynquee is not yet tested on this hardware: trying the Raspberry Pi config"
        install_rpi_init
        ;;
esac

remountRootRO

# Report complete
echo "Post-upgrade script complete"
