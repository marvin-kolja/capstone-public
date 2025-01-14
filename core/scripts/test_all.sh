#!/bin/bash

set -e
set -x

# Get positional args
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -v|--verbose) verbose=1; shift ;;
        -u|--unit) unit=1; shift ;;
        -i|--integration) integration=1; shift ;;
        --device) device=1; shift ;;
        -h|--help) echo "Usage: $0 [-v] [-u] [-i] [--device]"; exit 0 ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

OPTIONS=()

if [ $verbose ]; then
    OPTIONS+=("--log-cli-level=DEBUG")
fi

if [ $device ]; then
    OPTIONS+=("--device")
fi

TEST_DIRS=()

if [ $unit ]; then
    TEST_DIRS+=("tests/unit")
elif [ $integration ]; then
    TEST_DIRS+=("tests/integration")
fi

if [ ${#TEST_DIRS[@]} -eq 0 ]; then
    TEST_DIRS+=("tests/unit" "tests/integration")
fi

coverage run -m pytest ${TEST_DIRS[@]} --log-level=DEBUG ${OPTIONS[@]} && poetry run coverage report -m
