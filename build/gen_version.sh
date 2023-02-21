#!/bin/bash

# generate a version/build string from latest tag on current branch
git describe --tags --dirty --long
