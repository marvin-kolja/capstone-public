#!/bin/sh

#  build_dmg.sh
#  Client
#
#  Created by Marvin Willms on 29.01.25.
#

set -e

BASEDIR=$(dirname "$0")
DIST_DIR=$BASEDIR/../dist
ARCHIVE_PATH=$DIST_DIR/Client.xcarchive
APP_DIR=$DIST_DIR
EXPORT_OPTIONS_PATH=$BASEDIR/../Client/ExportOptions.plist
DMG_DIR=$DIST_DIR

if ! command -v create-dmg &> /dev/null; then
  echo "❌ create-dmg is not installed."
  echo "ℹ️ Follow the instructions at https://github.com/sindresorhus/create-dmg to install it."
  exit 1
fi

echo "🔄 Exporting archive"
xcodebuild \
  -exportArchive \
  -archivePath "$ARCHIVE_PATH" \
  -exportOptionsPlist "$EXPORT_OPTIONS_PATH" \
  -exportPath "$APP_DIR" \
  -allowProvisioningUpdates
echo "✅ Exported macOS Client to $APP_DIR"


echo "🔄 Creating DMG"
create-dmg "$APP_DIR/Client.app" "$DMG_DIR" --overwrite --dmg-title='Client'
echo "✅ Created DMG in $DMG_DIR"
