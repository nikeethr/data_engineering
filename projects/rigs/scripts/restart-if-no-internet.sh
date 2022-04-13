#!/bin/bash

_DATE=$(date +%Y-%m-%d,%T)
wget -q --spider http://google.com

if [ $? -eq 0 ]; then
    echo "${_DATE}    Online"
else
    echo "${_DATE}    Offline - restarting device"
    sudo shutdown -r now
fi
