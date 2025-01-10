#!/bin/bash

BASEDIR=$(dirname "$0")

cd $BASEDIR/../

poetry run python scripts/xcresult_model_generator
