#!/bin/bash

SCRIPT_PATH="$(dirname ${BASH_SOURCE[0]})/.."
if [ "$1" = "--setup" ]
then
    echo export PYTHONPATH=${SCRIPT_PATH}
    echo alias scancode_manifestor=\"${SCRIPT_PATH}/scancode_manifestor/__main__.py\"
    echo alias scancode-manifestor=\"${SCRIPT_PATH}/scancode_manifestor/__main__.py\"
    exit 0
fi
PYTHONPATH=${SCRIPT_PATH} ${SCRIPT_PATH}/scancode_manifestor/__main__.py $*

#ls -al ${SCRIPT_PATH} ${SCRIPT_PATH}/scancode_manifestor/__main__.py
