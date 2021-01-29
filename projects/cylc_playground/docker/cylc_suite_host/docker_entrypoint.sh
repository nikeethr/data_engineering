#!/bin/bash

set -eu

CYLC_LOCAL_PATH=/usr/local/bin/cylc

# persist environment variables
env | grep _ >> /etc/environment

# Run cylc review as cylc-user
sudo -u ${MYUSER} setsid \
    $CYLC_LOCAL_PATH review start 0</dev/null 1>/dev/null 2>&1 &

# For remote login (encrypted password can be set in .env file )
echo "${MYUSER}:${MYPASSWD}" | chpasswd -e

# Kick-off services
exec /usr/sbin/init

