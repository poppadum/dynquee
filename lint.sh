#!/bin/bash

# Run linting on all Python files

pylint *.py

cd artwork
pylint *.py

cd ../tests
pylint *.py