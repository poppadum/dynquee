#!/usr/bin/env bash

# Help user decide which video output to use for the marquee screen
# (used on Recalbox PC)
#
# All output goes to stderr except for final screen layout command;
# this allows calling scripts to capture the command


# Ask user to choose a screen
# args
#   $1 "Recalbox" or "marquee": used in on-screen prompts
# outputs device name of chosen screen
chooseScreen() {
    local screen
    local found
    while : ; do
        read -r -p "Which screen is your $1 screen: " screen
        # warn if screen not found in xrandr list
        if printf '%s\n' "${screens[@]}" | grep -Fxq -- "$screen"
        then
            found="screen '$screen' found: use it? (Y/N) "
        else
            found="WARNING: screen '$screen' not found: are you sure you want to use it? (Y/N) "
        fi
        if yesNo "$found"; then
            echo "Using $screen for $1" >&2
            echo "$screen"
            break
        fi
    done
}

# --- main ---

# Include library functions
source $(dirname "$0")/install_common.sh

cat >&2 <<END
From the list below identify which screen is your Recalbox screen
and which screen you want to use for your marquee:
(screen name is the first item on each line and is case-sensitive)

END

# List detected screens (exclude modes to keep list readable)
xrandr --query | grep -v '^ ' | grep -v '^Screen' | grep '^\S*' >&2
screens=( $(xrandr --query | grep -v '^Screen' | grep -o '^\S*') )

# Ask user to choose Recalbox screen
scr_recalbox=$(chooseScreen "Recalbox")

# Ask user to choose marquee screen
scr_marquee=$(chooseScreen "marquee")

# output correct xrandr command
xrandr_cmd="xrandr --output $scr_recalbox --auto --primary --output $scr_marquee --auto --right-of $scr_recalbox"
echo -e "Your screen setup command is:\n$xrandr_cmd" >&2
echo $xrandr_cmd
