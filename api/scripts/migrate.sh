#! /usr/bin/env bash

set -e
set -x

alembic upgrade head # Will create sqlite db if it doesn't exist
