#! /usr/bin/env bash

set -e

REPO_URL="git@github.com:marvin-kolja/capstone-public.git"
INSTALL_DIR="$HOME/capstone"
TMP_REPO_DIR="$INSTALL_DIR/tmp/repo"

echo "🔍 Checking dependencies..."
if ! command -v python3.13 &> /dev/null; then
    echo "❌ Python 3.13 is not installed. Please install it and run this script again."
    exit 1
fi

echo "🚀 Setting up the API and Socket Server..."

if [ ! -d "$TMP_REPO_DIR" ]; then
    echo "📥 Cloning repository..."
    git clone "$REPO_URL" "$TMP_REPO_DIR"
else
    echo "❌ Repository already exists at $TMP_REPO_DIR"
    exit 1
fi

echo "📂 Moving files..."

mkdir -p "$INSTALL_DIR/server/core"
cp -R "$TMP_REPO_DIR/core/." "$INSTALL_DIR/core"

mkdir -p "$INSTALL_DIR/server/api"
cp -R "$TMP_REPO_DIR/api/api/." "$INSTALL_DIR/server/api"

mkdir -p "$INSTALL_DIR/server/scripts"
cp "$TMP_REPO_DIR/api/scripts/run.sh" "$INSTALL_DIR/server/scripts/"
cp "$TMP_REPO_DIR/api/scripts/migrate.sh" "$INSTALL_DIR/server/scripts/"
cp "$TMP_REPO_DIR/api/alembic.ini" "$INSTALL_DIR/server/"
cp "$TMP_REPO_DIR/api/poetry.lock" "$INSTALL_DIR/server/"
cp "$TMP_REPO_DIR/api/pyproject.toml" "$INSTALL_DIR/server/"
cp "$TMP_REPO_DIR/api/README.md" "$INSTALL_DIR/server/"

cp "$TMP_REPO_DIR/misc/start_server.sh" "$INSTALL_DIR/"
cp "$TMP_REPO_DIR/misc/start_tunnel_server.sh" "$INSTALL_DIR/"

cd "$INSTALL_DIR/server"

if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3.13 -m venv venv
fi

source venv/bin/activate

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install .

echo "🔧 Setting up environment..."

mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/data/build_dir"
mkdir -p "$INSTALL_DIR/data/test_session_dir"

if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat <<EOF > .env
PROJECT_NAME=Capstone API
API_PORT=8000
ENVIRONMENT=production
SQLITE_PATH=$INSTALL_DIR/data/database.sqlite3
TUNNEL_CONNECT_PORT=49151
BUILD_DIR=$INSTALL_DIR/data/build_dir
TEST_SESSIONS_DIR=$INSTALL_DIR/data/test_session_dir
EOF
    echo "✅ Default .env file created. You can edit it later."
else
    echo "✅ .env file already exists."
fi

echo "🗑 Cleaning up..."

rm -rf "$TMP_REPO_DIR"
rm -rf "$INSTALL_DIR/core"

echo "Done! 🎉"

echo "Run the server:"
echo "sh $INSTALL_DIR/start_server.sh"

echo "Run the tunnel server:"
echo "sh $INSTALL_DIR/start_tunnel_server.sh"

