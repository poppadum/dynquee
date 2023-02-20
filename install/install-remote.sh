#!/bin/bash

# Install dynquee on a different machine to Recalbox

NAME=dynquee
BASEDIR=/opt/dynquee
RELEASE_URL='<dynquee-release>'
SERVICE=dynquee.service

APT_PACKAGES=(python3 python3-paho-mqtt fbi ffmpeg)

ROMDIRS=( \
    3do 64dd amiga1200 amiga600 amigacd32 amigacdtv amstradcpc apple2 \
    apple2gs atari2600 atari5200 atari7800 atari800 atarist atomiswave \
    bbcmicro bk c64 cdi channelf colecovision daphne dos dragon dreamcast \
    easyrpg fbneo fds gamegear gb gba gbc gw gx4000 intellivision jaguar \
    lowresnx lutro lynx mame mastersystem megadrive megaduck moonlight msx1 \
    msx2 msxturbor multivision n64 naomi naomigd neogeo neogeocd nes ngp \
    ngpc o2em openbor oricatmos palm pc88 pc98 pcengine pcenginecd pcfx pcv2 \
    pico8 pokemini ports psp psx samcoupe satellaview saturn scummvm scv \
    sega32x segacd sg1000 snes solarus spectravideo sufami supergrafx \
    supervision thomson ti994a tic80 trs80coco uzebox vectrex vic20 \
    videopacplus virtualboy wswan wswanc x1 x68000 zx81 zxspectrum \
)

error() {
    echo -e "\nSorry, something went wrong"
    exit 1
}

# Check we're not running on recalbox
if [ -d recalbox ]; then
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
echo -e "\nSearching for Recalbox on the local network"
# try default hostname first
recalbox_host=recalbox
while : ; do
    echo -n "trying hostname or IP address: $recalbox_host... "
    if /bin/ping -q -c 3 $recalbox_host >/dev/null 2>&1
    then
        found="found: use it? (Y/N) "
    else
        found="not found: use it anyway? (Y/N) "
    fi
    read -r -p "$found" yn
    if [[ "$yn" == [Yy] ]]; then
        echo "Using hostname / IP address: $recalbox_host"
        break
    else
        read -r -i recalbox -p "Please type the hostname or IP address of your Recalbox: " recalbox_host
    fi
done


# Create a directory for *dynquee* and download release
echo -e "\nCreating directory $BASEDIR"
mkdir -p $BASEDIR && \
cd $BASEDIR || error

echo -e "\nDownloading and extracting latest dynquee release"
/usr/bin/wget -o dynquee.zip "$RELEASE_URL" && \
/usr/bin/unzip -q dynquee.zip && \
rm dynquee.zip || error

# Create system directories within media directory
echo -e "\nCreating system directories in $BASEDIR/media"
for dir in ${ROMDIRS[@]}; do
    mkdir -p "$BASEDIR/media/$dir"
done

# Make media/ directory world-writeable so users don't need sudo to copy media
chmod --recursive a+w ./media/

# copy remote version of config
echo -e "\nInstalling config file for remote running"
cp -v install/dynquee-remote.ini ./dynquee.ini || error

# substitute discovered value of recalbox_host in config file
echo -e "\nSetting Recalbox hostname / IP address to $reacalbox_host in config file"
/usr/bin/sed -i "s/^host = recalbox$/host = $recalbox_host/" dynquee.ini

# install systemd service
echo -e "\nInstalling systemd service: $SERVICE"
cp -v install/$SERVICE /etc/systemd/system/ && \
/usr/bin/systemctl daemon-reload && \
/usr/bin/systemctl enable $SERVICE || error

# start service
echo -e "\nStarting service $SERVICE"
/usr/bin/systemctl start $SERVICE || {
    echo "Could not start service: showing journal entries for the last 2 minutes"
    /usr/bin/journalctl --unit=$SERVICE --no-pager --since="-2m"
    error
}

# Report finished
cat <<END

Installation complete: $NAME is now installed in $BASEDIR

Place your marquee images and videos in the appropriate directory within
$BASEDIR/media

Please see the file README.md for full details or read the comments in dynquee.ini
END
