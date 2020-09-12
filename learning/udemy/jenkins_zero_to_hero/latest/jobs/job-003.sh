#!/bin/sh

TITLE=$1
FIRST_NAME=$2
LAST_NAME=$3
SHOW=$4

if [[ "$4" ==  "True" ]]; then
    echo "Hello $1 $2 $3!"
else
    echo "SHOW needs to be set to True."
fi
