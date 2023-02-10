#!/bin/bash

# Run unit tests & integration tests


report() {
    if [ $1 -ne 0 ]; then
        printf "\033[1m\x1b[31m----- Error: exit code $1 ------\x1b[0m\033[0m\n"
    fi
    echo
}


# static type checking
echo "Running static type tests:"
mypy *.py tests/*.py
report $?

# unit tests
echo "Running unit tests:"
python3 -m unittest tests.test_dynquee
report $?

# integration tests
echo "Running EventHandler integration tests:"
python3 -m tests.test_EventHandler
report $?

echo "Running Slideshow integration tests:"
python3 -m tests.test_Slideshow
report $?
