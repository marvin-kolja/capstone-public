#!/bin/sh

#  archive.sh
#  Client
#
#  Created by Marvin Willms on 28.01.25.
#

# TODO: It probably make sense to split this up into multiple scripts. For now this is fine, though.

set -e

BASEDIR=$(dirname "$0")
DIST_DIR=$BASEDIR/../dist
ARCHIVE_PATH=$DIST_DIR/Client.xcarchive
PROJECT_PATH=$BASEDIR/../Client.xcodeproj

echo "🔄 Archiving macOS Client"
xcodebuild \
  archive \
  -project "$PROJECT_PATH" \
  -scheme Production \
  -destination 'generic/platform=macOS' \
  -archivePath "$ARCHIVE_PATH"
echo "✅ Archived macOS Client to $ARCHIVE_PATH"
