#!/bin/bash

# Install digimarquee on Recalbox

NAME=digimarquee
BASEDIR=/recalbox/share/digimarquee
ROMDIR=/recalbox/share/roms

error() {
    echo Sorry, something went wrong
    exit 1
}

# Check we are running on Recalbox: is /recalbox directory present?
if [ ! -d /recalbox ]; then
    echo "$NAME install script is intended to be run on Recalbox"
    exit 1
fi

# Assume archive is downloaded and extracted
# (probably in home dir /recalbox/share/system)

# Create base directory if not already present
mkdir -p "$BASEDIR"
cd "$BASEDIR"

# Copy init script & make it executable
echo Mounting root filesystem read/write
/bin/mount -o rw,remount / || error

echo Installing init script to run at startup
cp -vf S32digimarquee /etc/init.d/ && \
chmod -v +x /etc/init.d/S32digimarquee || error

echo Remounting root filesystem read-only
/bin/mount -o ro,remount /


# Create system directories within media directory
echo Creating system directories in $BASEDIR/media
for dir in "$ROMDIR/*/"; do
    mkdir -p "$BASEDIR/media/$(basename "$dir")"
done

# Start digimarquee via init script
echo Starting $NAME
/etc/init.d/S32digimarquee start

# Report finished
echo <<END

Installation complete: $NAME is now installed in $BASEDIR

Place your marquee images and videos in the appropriate directory within
$BASEDIR/media

Please see the file README.md for full details or read the comments in digimarquee.config.txt
END
