#!/bin/bash

SCRIPT_PATH="$(dirname ${BASH_SOURCE[0]})/.."

PYTHONPATH=${SCRIPT_PATH} ${SCRIPT_PATH}/scancode_manifestor/__main__.py $*
#ls -al ${SCRIPT_PATH} ${SCRIPT_PATH}/scancode_manifestor/__main__.py
