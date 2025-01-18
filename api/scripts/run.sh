#! /usr/bin/env bash

set -e
set -x

# Execute migrations
sh ./scripts/migrate.sh

# Run the application
python -m api.main
