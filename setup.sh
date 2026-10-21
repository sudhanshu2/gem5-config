#!/bin/bash

set -e

BASE_DIR=$(pwd)
VENV_DIR=$BASE_DIR/.venv

echo "Setup virtualenv"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv $VENV_DIR
  source $VENV_DIR/bin/activate
  python -m pip install -r $BASE_DIR/requirements.txt
  deactivate
fi

source $VENV_DIR/bin/activate
echo "Setup pre-commit"
$VENV_DIR/bin/pre-commit install
deactivate
