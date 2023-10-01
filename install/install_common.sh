#!/usr/bin/env bash

# Library functions for dynquee install scripts

# constants
readonly INIT_SCRIPT=S32dynquee
readonly XRANDR_CMD_FILE=xrandr_cmd.txt

# suffix to add to original config files before modifying
readonly BACKUP_SUFFIX=dynquee.orig

# PC config file paths:
OPENBOX_CFG=/etc/openbox/rc.xml
XINITRC=/etc/X11/xinit/xinitrc


# Remount / read/write
remountRootRW() {
    echo -e "\nMounting root filesystem read/write"
    /bin/mount -o rw,remount / || error

}

# Remount / read-only
remountRootRO() {
    echo -e "\nMounting root filesystem read-only"
    /bin/mount -o ro,remount / || error
}

# Create backup of file $1 named "$1.$BACKUP_SUFFIX"
# if a backup file does not already exist
backupFile() {
    if [ ! -f "$1.$BACKUP_SUFFIX" ]; then
        echo -e "\nMaking backup of '$1' in '$1.$BACKUP_SUFFIX'"
        cp -f "$1" "$1.$BACKUP_SUFFIX"
    fi
}

# Ask user for "yes or no" answer
# args
#  $1 - prompt string
# returns 0 if yes, 1 otherwise
yesNo() {
    local yn
    read -r -p "$1" yn
    [[ "$yn" == [Yy] ]] && return 0
    return 1
}

# Report an error and exit with non-zero code
# args
#  $1 - optional error message
error() {
    echo "Sorry, something went wrong. Please report this bug at https://github.com/poppadum/dynquee/issues" >&2
    [ ! -z "$1" ] && echo "$1" >&2
    exit 1
}

# Install RPi init script
# args
#  $1 - destination directory (default /etc/init.d)
install_rpi_init() {
    local dest=/etc/init.d
    if ! [ -z "$1" ]; then
        dest="$1"
    fi
    # Copy init script to destination & make it executable
    echo "Installing init script to run at startup"
    cp -vf install/$INIT_SCRIPT $dest/ && \
    chmod -v +x $dest/$INIT_SCRIPT || error
}

# Insert the following XML into a document as a subnode of <applications>:
#   <application class="…"><focus>…</focus></application>
# args:
#   $1 path to XML file
#   $2 <application> element's class attribute value
#   $3 text within <focus> element
insertAppFocusXML() {
    local TEMPNODE='__xxx'
    xml ed \
        --inplace \
        --subnode '//_:applications' --type elem -n "$TEMPNODE" \
        --subnode "//$TEMPNODE" --type attr -n class -v "$2" \
        --subnode "//$TEMPNODE" --type elem -n focus \
        --subnode "//$TEMPNODE/focus" --type text -n _ -v "$3" \
        --rename "//$TEMPNODE" -v application \
        "$1"
    return $?
}

# Ask user for preferred screens for Recalbox & marquee.
# User's preference is written to stdout
recordScreenLayout() {
    local new_xrandr_file=no
    # Check if screen layout command file already exists
    if [ ! -f "$XRANDR_CMD_FILE" ]; then
        new_xrandr_file=yes
    else
        echo "Found an existing screen layout file:"
        xrandr_cmd=$(< "$XRANDR_CMD_FILE")
        echo -e "$xrandr_cmd\n"
        if ! yesNo "Do you want to use this screen layout? (Y/N) "; then
            new_xrandr_file=yes
        fi
    fi

    # If not using existing layout, prompt user to identify screens
    if [ "$new_xrandr_file" == "yes" ]; then
        xrandr_cmd=$(bash "$BASEDIR/install/find_marquee_output.sh") || error
        # record screen layout command to screen layout command file
        echo "Recording screen layout to file '$XRANDR_CMD_FILE'"
        echo "$xrandr_cmd" > "$XRANDR_CMD_FILE" || error
    fi
}

# Adjust Openbox config to prevent mpv stealing the focus
fixOpenboxConfig() {
    # Make backup of Openbox config file if not already present
    backupFile "$OPENBOX_CFG"
    # Edit Openbox config file to fix application focus
    echo -e "\nTweaking Openbox config file '$OPENBOX_CFG' to prevent mpv grabbing focus"
    insertAppFocusXML "$OPENBOX_CFG" EmulationStation yes || error
    insertAppFocusXML "$OPENBOX_CFG" mpv no || error
}

# Adjust xinitrc to launch  startup_pc.sh when X starts
# args:
#   $1 - `xrandr` command to insert
fixXinitrc() {
    # Make backup of xinitrc if not already present
    backupFile "$XINITRC"
    # Replace ES start command with dynquee startup script in xinitrc
    echo -e "\nAdding dynquee start script and screen layout to '$XINITRC'"
    local LINE='/^openbox --config-file \/etc\/openbox\/rc.xml --startup/'
    local FIND='"emulationstation --windowed"'
    local REPL="\"bash $BASEDIR/startup_pc.sh\""
    sed -i -E \
        "$LINE s|$FIND\$|$REPL|" \
        "$XINITRC" \
        || error

    # Insert screen set up `xrandr` command into xinitrc
    LINE='/^\/usr\/bin\/externalscreen.sh/'
    sed -i \
        "$LINE a $1" \
        "$XINITRC" \
        || error
}
