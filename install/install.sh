#!/usr/bin/env bash

# Install dynquee on Recalbox

NAME=dynquee
BASEDIR=/recalbox/share/dynquee
RELEASE_URL='<dynquee-release>'
INIT_SCRIPT=S32dynquee
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


# Create a directory for *dynquee* and download release
echo -e "\nCreating directory $BASEDIR"
mkdir -p $BASEDIR && \
cd $BASEDIR || error

echo -e "\nDownloading and extracting latest dynquee release"
/usr/bin/wget -o dynquee.zip "$RELEASE_URL" && \
/usr/bin/unzip -q dynquee.zip && \
rm dynquee.zip || error


# Copy init script & make it executable
echo -e "\nMounting root filesystem read/write"
/bin/mount -o rw,remount / || error

echo "Installing init script to run at startup"
cp -vf install/$INIT_SCRIPT /etc/init.d/ && \
chmod -v +x /etc/init.d/$INIT_SCRIPT || error

echo "Remounting root filesystem read-only"
/bin/mount -o ro,remount /


# Create system directories within media directory
echo -e "\nCreating system directories in $BASEDIR/media"
for dir in $ROMDIR/*/; do
    if [ "$dir" != "$ROMDIR/240ptestsuite/" ]; then
        mkdir -p "$BASEDIR/media/$(basename "$dir")"
    fi
done

# Start dynquee via init script
echo -e "\nStarting $NAME"
/etc/init.d/$INIT_SCRIPT start || error

# Report finished
cat <<END

Installation complete: $NAME is now installed in $BASEDIR

Place your marquee images and videos in the appropriate directory within
$BASEDIR/media

Please see the file README.md for full details or read the comments in dynquee.ini
END
