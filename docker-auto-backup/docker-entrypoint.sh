#!/bin/sh

#
# Docker entrypoint for the automatic Docker volume backup image.
#

set -e

. /root/config.sh

# Store environment variables in a file so that cron jobs can use them.
{
printf "ENABLE_RSYNC='$ENABLE_RSYNC'\n"
printf "RSYNC_DEST='$RSYNC_DEST'\n"
printf "SSH_HOST='$SSH_HOST'\n"
printf "ROTATE_AFTER='$ROTATE_AFTER'\n"
} > "$ENV_FILE"

if [ -n "$CRON_EXPR" ]; then
    printf "[INFO] Install cron.d entry.\n"
    printf "$CRON_EXPR sh $WORKDIR/backup.sh >> /proc/1/fd/1 2>&1\n" | crontab -
else
    printf "[INFO] Cron expression empty. Won't create cron.d entry.\n"
fi

printf "[INFO] Start cron.\n"
crond -f
