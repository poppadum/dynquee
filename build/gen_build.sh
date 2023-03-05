#!/usr/bin/env bash

# Generate a version/build number from latest tag on current branch
git describe --tags --long --dirty
