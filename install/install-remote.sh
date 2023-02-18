#!/bin/bash

# Install dynquee on a different machine to Recalbox

NAME=dynquee
BASEDIR=/opt/dynquee
RELEASE_URL='<dynquee-release>'
SERVICE=dynquee.service

APT_PACKAGES=(python3 python3-paho-mqtt fbi ffmpeg)


error() {
    echo -e "\nSorry, something went wrong"
    exit 1
}

# Check we're not running on recalbox
if [ -d /recalbox ]; then
    echo "/recalbox directory found on this machine:"
    echo "$NAME is intended to be run on a different machine to Recalbox"
    exit 1
fi

# Check we are running as root
if [[ $EUID != 0 ]]; then
    echo "This script needs root privileges to run. Please run again as: sudo $0"
    exit 1
fi

# Install required packages
echo -e "\nInstalling required packages: ${APT_PACKAGES[@]}"
/usr/bin/apt install -y ${APT_PACKAGES[@]} || error

# Check network connection to Recalbox:
# try default hostname first
echo -e "\nSearching for Recalbox on the local network"
recalbox_host=recalbox
while true; do
    echo -n "trying hostname or IP address: $recalbox_host... "
    if /bin/ping -q -c 3 $recalbox_host >/dev/null 2>&1
    then
        echo "found"
        break
    fi
    echo "not found"
    read -r -i recalbox -p "Please type the hostname or IP address of your Recalbox: " recalbox_host
done
# found recalbox host

# Create a directory for *dynquee* and download release
echo -e "\nCreating directory $BASEDIR"
mkdir -p $BASEDIR && \
cd $BASEDIR || error

echo "Downloading latest dynquee release"
#/usr/bin/wget -o dynquee.zip "$RELEASE_URL" && \
/usr/bin/unzip dynquee.zip  || error

# Make media/ directory world-writeable so users don't need sudo to copy media
chmod --recursive +w ./media/

# copy remote/ versions of config & log config files
echo -e "\nInstalling config file and log config file for remote running"
cp -v install/dynquee-remote.ini ./dynquee.ini && \
cp -v install/dynquee-remote.log.conf ./dynquee.log.conf || error

# substitute discovered value of recalbox_host in config file
echo -e "\nSetting Recalbox hostname / IP address in config file"
/usr/bin/sed -i "s/^host = recalbox$/host = $recalbox_host/" dynquee.ini


# install systemd service
echo -e "\nInstalling systemd service: $SERVICE"
cp -v install/$SERVICE /etc/systemd/system/ && \
/usr/bin/systemctl daemon-reload && \
/usr/bin/systemctl enable $SERVICE

# start service
echo -e "\nStarting service $SERVICE"
systemctl start $SERVICE || \
    journalctl -u $SERVICE && error

# Report finished
cat <<END

Installation complete: $NAME is now installed in $BASEDIR

Place your marquee images and videos in the appropriate directory within
$BASEDIR/media

Please see the file README.md for full details or read the comments in dynquee.ini
END
