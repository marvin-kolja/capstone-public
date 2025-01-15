#!/usr/bin/env bash

# This script generates a new migration revision for the database using alembic.
# Script is based on: https://www.funkthat.com/gitea/jmg/medashare/src/commit/5d339516dc217b948e76a659bec8781af5f820f8/ui/medashare/autogen.sh

if [ -z "$*" ]; then
	echo "Provide the upgrade message as an argument."
	exit 1
fi

set -e
set -x

DB_PATH=autogen.db.sqlite3

# Make sure we start clean
rm -f $DB_PATH

# Upgrade the database to head
SQLITE_PATH=$DB_PATH alembic upgrade head

# Autogenerate the migrations
SQLITE_PATH=$DB_PATH alembic revision --autogenerate -m "$*"

## Clean up
rm -f $DB_PATH
