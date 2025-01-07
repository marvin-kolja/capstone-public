#!/bin/bash

# Get positional args

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -v|--verbose) verbose=1; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

BASEDIR=$(dirname "$0")

cd $BASEDIR/../

OPTIONS=()

if [ $verbose ]; then
    OPTIONS+=("--log-cli-level=DEBUG")
fi

poetry run pytest tests/ --device ${OPTIONS[@]}
