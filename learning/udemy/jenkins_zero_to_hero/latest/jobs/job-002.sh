#!/bin/sh

NAME=$1
LASTNAME=$2
{
    echo "Hello ${NAME} $LASTNAME,"
    echo "Current date: $(date)"
    echo "Directory of job: $(pwd)"
} > /tmp/hello

