#!/bin/bash

# Generate a version/build string from latest tag on current branch
# Note: can't use the --dirty tag because it invokes a filter, and
# using this script in a filter causes an infinite loop
git describe --tags --long
