#!/bin/bash

set -eu

CYLC_LOCAL_PATH=/usr/local/bin/cylc

# persist environment variables
env | grep _ >> /etc/environment

# For remote login (encrypted password can be set in .env file )
echo "${MYUSER}:${MYPASSWD}" | chpasswd -e

# Kick-off services
exec /usr/sbin/init

