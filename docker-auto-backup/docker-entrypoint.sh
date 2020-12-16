#!/bin/sh

#
# Docker entrypoint for the automatic Docker volume backup image.
#

set -e

. /root/docker-config.sh

# Store environment variables in a file so that cron jobs can use them.
{
echo "ENABLE_RSYNC='$ENABLE_RSYNC'"
echo "RSYNC_DEST='$RSYNC_DEST'"
echo "SSH_HOST='$SSH_HOST'"
echo "ROTATE_AFTER='$ROTATE_AFTER'"
} > "$ENV_FILE"

if [ -n "$CRON_EXPR" ]; then
    echo "[INFO] Install cron.d entry."
    echo "$CRON_EXPR root sh $WORKDIR/docker-backup.sh >> /proc/1/fd/1 2>&1" > "$CRONTAB_FILE"
else
    echo "[INFO] Cron expression empty. Won't create cron.d entry."
fi

echo "[INFO] Start cron."
cron -f
