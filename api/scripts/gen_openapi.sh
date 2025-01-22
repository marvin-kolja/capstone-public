#! /usr/bin/env bash

set -e
set -x

BASEDIR=$(dirname "$0")

python "$BASEDIR/custom_openapi.py" > "$BASEDIR/../../macOS/Client/Client/openapi.yaml"
