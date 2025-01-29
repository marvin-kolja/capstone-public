#!/bin/sh

#  build_dmg.sh
#  Client
#
#  Created by Marvin Willms on 29.01.25.
#

set -e

BASEDIR=$(dirname "$0")
DIST_DIR=$BASEDIR/../dist
DMG_DIR=$DIST_DIR

if [ -z "$NOTARY_PASSWORD" ]; then
  echo "❌ NOTARY_PASSWORD is not set"
  exit 1
fi

echo "🔄 Notarizing DMG"
xcrun notarytool submit \
  --team-id '***REDACTED***' \
  --apple-id '***REDACTED***' \
  --password "$NOTARY_PASSWORD" \
  --wait \
  "$DMG_DIR/Client 1.0.dmg"
echo "✅ Notarized DMG"

echo "🚀 Ready to distribute macOS Client"
