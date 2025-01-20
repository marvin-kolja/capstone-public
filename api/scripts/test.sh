#!/usr/bin/env bash

# Execute tests using a temporary SQLite database

set -e
set -x

DB_PATH=test.db.sqlite3

# Make sure we start clean
rm -f $DB_PATH

# Migrate the database to head before running tests
SQLITE_PATH=$DB_PATH sh scripts/migrate.sh

# Run the tests
SQLITE_PATH=$DB_PATH coverage run -m pytest tests/ $@

# Clean up
rm -f $DB_PATH
