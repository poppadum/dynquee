#!/bin/bash


#
# User configurable options
#
# Path where marquee media files are located
readonly MARQUEE_BASE=/recalbox/share/digimarquee/media
# TODO: eventually put marquees in roms/system/media/images/marquees for compatibility with miniTFT support?


#
# Constants
#
LOGFILE=/tmp/digimarquee.log
LOGDATEFMT='%Y-%m-%d %H:%M:%S'
FIFO=/tmp/mqtt_sub_digimarquee
ES_STATE=/tmp/es_state.inf
PLAYER=/usr/bin/mpv
PLAYER_OPTS="--vo=drm --drm-connector=1.HDMI-A-2 --hwdec=mmal --loop"
PLAYER_PID_UNKNOWN=na


#
# Global vars
#
playerPid=$PLAYER_PID_UNKNOWN
actionData=""

shopt -s nullglob


# Send timestamped message to logfile
# Params: $@ = text to log
# DEBUG: for now, log to stderr while developing
log() {
	printf "%s: %s\n" "$(date +"$LOGDATEFMT")" "$*" >&2 #>> "$LOGFILE"
	# TODO: also log to recallog
}


# Choose a random item from a list
# Params: $@ = a list
chooseRandomFrom() {
	log "chooseRandomFrom $@ ($# items)"
	# Can't pick from an empty list: exit with code 1
	if [ $# -eq 0 ]; then
		return 1
	fi
	# Pick a random item and return it
	items=("$@")
	numItems=${#items[@]}
	#echo "numItems=$numItems"
	randomIndex=$(( $RANDOM % $numItems ))
	#echo "randomIndex=$randomIndex"
	echo "${items[$randomIndex]}"
}


#chooseRandomFrom a b c d
#chooseRandomFrom || echo empty list
#exit



# Event handler
# Params: $1 = Action
#         $2 = ActionData
#         $3 = SystemId
#         $4 = GamePath
#         $5 = ImagePath
handleEvent() {
	case "$1" in
		systembrowsing|gamelistbrowsing)
			getMarqueeMedia "$1" "$2" "$3" "$4" "$5"
			;;

		start|stop|runkodi)
			;;

		sleep)
			;;

		wakeup)
			;;

		rungame|rundemo)
			;;

		endgame|enddemo)
			;;
	esac
}



# Display a still image or video clip on the marquee
# Params: $1 = path to image/video file
#         $2 = additional options to mpv
showOnMarquee() {
	# Stop the previous player if one is running
	if [[ "$playerPid" != "$PLAYER_PID_UNKNOWN" ]]; then
		kill $playerPid && \
			playerPid=$PLAYER_PID_UNKNOWN
	fi
	# launch player and record pid so we can stop it later
	printf "DEBUG: run command: %s\n" "$PLAYER $PLAYER_OPTS \"$1\""
	if $PLAYER $PLAYER_OPTS "$1" &
	then
		echo "DEBUG: command exit code $?"
		playerPid=$!
	fi
}



# Search for ROM-specific media files, and if >1 found, return one at random.
# If none found, exits with return code 1
# Params: $1 = SystemId
#         $2 = gameBasename
getMarqueeMediaForROM() {
	# find ROM-specific media files in $MARQUEE_BASE/$SystemId/$gameBasename
	files=( "$MARQUEE_BASE/$1/$2".* )
	log "searching for marquee media in '$MARQUEE_BASE/$1/$2.*'"
	log "found ${#files[@]} files: ${files[@]}"
	if [[ ${#files[@]} -eq 0 ]]; then
		return 1
	fi
	chooseRandomFrom "$files"
}


# Work out which media file to display on the marquee.
# Precedence:
#  1. ROM-specific media file (if browsing or playing a game)
#  2. genre media file
#  3. system media file
#  4. generic file
#
# Params: $1 = Action
#         $2 = ActionData
#         $3 = SystemId
#         $4 = GamePath
#         $5 = ImagePath
getMarqueeMedia() {
	# Get game filename without directory and extension
	gameBasename=$(basename "$4")
	# strip leading directories
	gameBasename="${gameBasename##*/}"
	# strip last part of filename from last dot onwards
	# TODO: What if filename ends e.g. .tar.gz? Assume no dots in filename & strip everything from first dot?
	gameBasename="${gameBasename%.*}"
	log "gameBase=$gameBasename"
	
	# ROM-specific media file
	if file=$( getMarqueeMediaForROM "$3" "$gameBasename" ); rc=$?; [[ $rc -eq 0 ]]; then
		log "selected ROM-specific media file '$file'"
	# Scraped image
	elif  [[ "$5" != "" ]]; then
		file="$5"
		log "selected ROM image file '$file'"
	# last resort: Recalbox logo
	else
		file=/recalbox/share_init/system/tft_logos/320p/recalbox.png
	fi

	# display chosen media
	showOnMarquee "$file"
}



# Get the value from a multiline input string in the format:
#   key1=some string value
#   key2=another string
#
# Params: $1 = multiline string to search
#         $2 = key
# Output: e.g. "some string value"
getValueForKey() {
	#printf "DEBUG: getValueForKey('...', '%s')\n" "$2"
	value=$(grep "^$2=" <<< "$1") || return 1
	#printf "DEBUG: value='%s'\n" "$value"
	# remove key= from start of line and return just the value
	echo $(cut -f 2- -d'=' <<< "$value") || return 2
}




###
### Main
###


# Create named pipe if it doesn't exist
if [ ! -p  $FIFO ]; then
	mkfifo $FIFO
fi

# Start MQ subscriber and output to fifo
mosquitto_sub -h 127.0.0.1 -p 1883 -q 0 -t Recalbox/EmulationStation/Event > $FIFO &

while [[ "$actionData" != "quitrequested" ]]; do
	# wait for event to be published
	IFS= read -r event

	# handle event
	#echo  "Event received: $event:"

	# read event params from ES state file, stripping any CR characters
	evParams=$(tr -d '\r' < $ES_STATE)
	actionData=$(getValueForKey "$evParams" "ActionData")
	systemId=$(getValueForKey "$evParams" "SystemId")
	gamePath=$(getValueForKey "$evParams" "GamePath")
	imagePath=$(getValueForKey "$evParams" "ImagePath")

	printf "Action: %s\nActionData: %s\nSystemId: %s\nGamePath: %s\nImagePath: %s\n\n" "$event" "$actionData" "$systemId" "$gamePath" "$imagePath"

	handleEvent "$event" "$actionData" "$systemId" "$gamePath" "$imagePath"
done < $FIFO

# cleanup
# trap SIGTERM here?

# unsubscribe from MQTT topic
mosquitto_sub -U Recalbox/EmulationStation/Event
mosquitto_sub -E
