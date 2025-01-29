#! /usr/bin/env bash

set -e

cd "$(dirname "$0")/server"

source venv/bin/activate

echo "🚀 Starting API server..."

sh scripts/run.sh
