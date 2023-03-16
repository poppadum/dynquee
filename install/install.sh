#!/usr/bin/env bash

# Install dynquee on Recalbox

# constants
readonly NAME=dynquee
readonly RELEASE_URL=https://github.com/poppadum/dynquee/releases/latest/download/dynquee.zip
readonly ROMDIR=/recalbox/share/roms
readonly INIT_SCRIPT=S32dynquee
readonly XRANDR_CMD_FILE=xrandr_cmd.txt

BASEDIR=/recalbox/share/dynquee

# Check this script is running on a Recalbox; exit if not
checkRecalbox() {
    if [ ! -d /recalbox ]; then
        echo "$NAME install script is intended to be run on Recalbox"
        exit 1
    fi
}

# Create base dynquee directory & change to it
createBaseDir() {
    echo -e "\nCreating directory $BASEDIR"
    mkdir -p $BASEDIR && \
    cd $BASEDIR || error
}

# Download latest dynquee release ZIP file & unzip it
downloadDynqueeRelease() {
    echo -e "\nDownloading and extracting latest dynquee release"
    /usr/bin/wget --quiet --output-document=dynquee.zip "$RELEASE_URL" && \
    /usr/bin/unzip -q dynquee.zip && \
    rm dynquee.zip || error
}

# Create system directories within media directory
createSystemDirs() {
    echo -e "\nCreating system directories in $BASEDIR/media"
    for dir in $ROMDIR/*/; do
        if [ "$dir" != "$ROMDIR/240ptestsuite/" ]; then
            mkdir -p "$BASEDIR/media/$(basename "$dir")"
        fi
    done
}

# Start dynquee via init script
start_rpi() {
    echo -e "\nStarting $NAME"
    /etc/init.d/$INIT_SCRIPT start || error
}

# Performs:
#   - install PC startup script & config files
#   - adjust Openbox config
#   - modify xinitrc to start dynquee
install_PC() {
    # Copy PC startup script & PC config file to program directory
    echo -e "\nInstalling startup script"
    cp -vf install/startup_pc.sh ./ || error

    echo -e "\nInstalling PC config file"
    cp -vf install/dynquee-pc.ini ./dynquee.ini || error

    fixOpenboxConfig

    local xrandr_cmd=$(< "$XRANDR_CMD_FILE")
    fixXinitrc "$xrandr_cmd"
}

# Start dynquee via ES restart (causes X to exit and restart)
start_PC() {
    echo -e "\nRestarting Emulation Station and starting dynquee"
    es stop
    sleep 3
    es start
    return $?
}



# --- main ---

checkRecalbox
createBaseDir
downloadDynqueeRelease

# Are we on RPi, PC or something else?
arch=$(cat /recalbox/recalbox.arch) || error

# FOR TESTING ONLY:
#arch=x86_64
#arch=rpi4_x64
echo "Detected arch: $arch"

# Include library functions
source ./install/install_common.sh

# FOR TESTING ONLY:
#source ./tests/install_common.sh


createSystemDirs
remountRootRW

case "$arch" in
    x86*)
        recordScreenLayout "$XRANDR_CMD_FILE"
        install_PC
        start_PC
        ;;
    rpi*)
        install_rpi_init
        start_rpi
        ;;
    *)
        # e.g. odroidxu4, odroidgo
        echo "$NAME is not yet tested on this hardware: trying the Raspberry Pi config"
        install_rpi_init
        start_rpi
        ;;
esac

remountRootRO

# Report installation complete
cat <<END

Installation complete: $NAME is now installed in $BASEDIR

Place your marquee images and videos in the appropriate directory within
$BASEDIR/media

Please see the file README.md for full details or read the comments in dynquee.ini
END
