#!/bin/bash

if [ "$1" = "-v" ]
then

   DEBUG_FLAGS="-v"
   shift
fi

SC_REPORT=$1
shift

if [ ! -f $SC_REPORT ]
then
    echo "missing scancode report file: $SC_REPORT"
    exit 2
fi


if [ "$1" = "--html" ] 
then
    if [ ! -f config.json ]
    then
        echo "*** Missing config file \"config.json\" ***"
        exit 2
    fi
    SCANCODE_MANIFESTOR_PY="$( realpath "${BASH_SOURCE[0]}" | sed 's,\.sh,\.py,g')"
    $SCANCODE_MANIFESTOR_PY $DEBUG_FLAGS -ae -i $SC_REPORT -c config.json -of markdown -- create > manifest.md
    if [ $? -ne 0 ]
    then
        echo "Failed (in $(pwd)):"
        echo "$SCANCODE_MANIFESTOR_PY -ae -i $SC_REPORT -c config.json -of markdown -- create > manifest.md"
        exit 2
    fi
        
    pandoc manifest.md -o manifest.html
    if [ $? -ne 0 ]
    then
        echo "Failed (in $(pwd)):"
        echo "pandoc manifest.md -o manifest.html"
        exit 2
    fi
else
    echo "unsupport argument: $*"
fi
   
exit 0
