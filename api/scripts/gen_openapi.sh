#! /usr/bin/env bash

set -e
set -x

BASEDIR=$(dirname "$0")

python -c "import api.main; import yaml; print(yaml.dump(api.main.app.openapi()))" > "$BASEDIR/../../macOS/Client/Client/openapi.yaml"
