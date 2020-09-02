#!/bin/bash

set -eu

# For remote login (encrypted password can be set in .env file )
echo "${MYUSER}:${MYPASSWD}" | chpasswd -e

# Kick-off services
exec /usr/sbin/init

