#! /usr/bin/env bash

set -e

cd "$(dirname "$0")/server"

export $(grep -v '^#' .env | xargs)

source venv/bin/activate

echo "🚀 Starting Tunnel Connect server..."
sudo python -m core.tunnel.server_executable $TUNNEL_CONNECT_PORT
