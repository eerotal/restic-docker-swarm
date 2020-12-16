#!/bin/sh

#
# Docker entrypoint for the automatic Docker volume backup image.
#

set -e

. ./docker-config.sh

terminate_pids() {
    trap "" CHLD
    echo "[INFO] A service exited. Stopping container."
    for p in $@; do
        kill $p 2> /dev/null
    done
}

# Store environment variables in a file so that cron jobs can use them.
{
echo "ENABLE_RSYNC='$ENABLE_RSYNC'"
echo "RSYNC_DEST='$RSYNC_DEST'"
echo "SSH_HOST='$SSH_HOST'"
} > "$ENV_FILE"

if [ -n "$CRON_EXPR" ]; then
    echo "[INFO] Install cron.d entry."
    echo "$CRON_EXPR root sh $WORKDIR/docker-backup.sh >> /proc/1/fd/1 2>&1" > "$CRONTAB_FILE"
else
    echo "[INFO] Cron expression empty. Won't create cron.d entry."
fi

pids=""

echo "[INFO] Start cron."
cron
pids="$pids $!"

# Terminate all child processes if a child terminates.
trap "terminate_pids $pids" CHLD

for p in $pids; do
    wait $p
done
