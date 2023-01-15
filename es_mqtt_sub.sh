#!/bin/bash

FIFO=/tmp/mqtt_sub_digimarquee
ES_STATE=/tmp/es_state.inf


# Event handler
# Params: $1 = Action
#         $2 = ActionData
#         $3 = SystemId
#         $4 = GamePath
#         $5 = ImagePath
handleEvent() {
	case "$1" in
		start)
			;;

		stop)
			;;

		sleep)
			;;

		wakeup)
			;;

		systembrowsing|runkodi)
			echo "Browsing system: $3"
			;;

		gamelistbrowsing)
			;;

		rungame|rundemo)
			;;

		endgame|enddemo)
			;;
	esac
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



## debug
#searchStr=$(cat <<END
#ActionData=a very long string containing an = sign!
#System=Speccy
#END
#)
#echo "searchStr = $searchStr"

#for key in "ActionData" "SystemId" "XXX"; do
#    getValueForKey "$searchStr" "$key"
#    echo "rc $?"
#done

#exit




###
### Main
###


# Create named pipe if it doesn't exist
if [ ! -p  $FIFO ]; then
	mkfifo $FIFO
fi

# Start MQ subscriber and output to fifo
mosquitto_sub -h 127.0.0.1 -p 1883 -q 0 -t Recalbox/EmulationStation/Event > $FIFO &

while true; do
	# wait for event to be published
	IFS= read -r event

	# handle event
	#echo  "Event received: $event:"

	# read event params from ES state file
	evParams=$(<$ES_STATE)
	#echo "$evParams"

	actionData=$(getValueForKey "$evParams" "ActionData")
	systemId=$(getValueForKey "$evParams" "SystemId")
	gamePath=$(getValueForKey "$evParams" "GamePath")
	imagePath=$(getValueForKey "$evParams" "ImagePath")

	printf "Action: %s\nActionData: %s\nSystemId: %s\nGamePath: %s\nImagePath: %s\n\n" "$event" "$actionData" "$systemId" "$gamePath" "$imagePath"

	handleEvent "$event" "$actionData" "$systemId" "$gamePath" "$imagePath"
done < $FIFO
