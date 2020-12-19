#!/bin/sh

#
# Docker healthcheck for the automatic Docker volume backup image.
#

set -e

. /root/config.sh

if [ $# -lt 1 ]; then
    printf "[Error] You must specify the failure threshold in seconds as the only argument.\n"
    exit 1
fi

FAIL_THRESHOLD="$1"

if [ ! -f "$LAST_BACKUP_FILE" ]; then
    exit 1
fi

if [ $(( $(date +"%s") - $(cat "$LAST_BACKUP_FILE") )) -gt $FAIL_THRESHOLD ]; then
    exit 1
fi
