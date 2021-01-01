#!/bin/sh

#
# Docker entrypoint for the automatic Docker volume backup image.
#

set -e

. /root/config.sh

# Store environment variables in a file so that cron jobs can use them.
{
printf "ENABLE_RSYNC='${ENABLE_RSYNC}'\n"
printf "BACKUP_IDENTIFIER='${BACKUP_IDENTIFIER}'"
printf "RSYNC_DEST='${RSYNC_DEST}'\n"
printf "SSH_HOST='${SSH_HOST}'\n"
printf "ROTATE_AFTER='${ROTATE_AFTER}'\n"
} > "$ENV_FILE"

if [ -z "${BACKUP_IDENTIFIER}" ]; then
    printf "[ERROR] BACKUP_IDENTIFIER cannot be empty!"
    exit 1
fi

if [ -n "${CRON_EXPR}" ]; then
    printf "[INFO] Install cron.d entry.\n"
    printf "${CRON_EXPR} sh ${WORKDIR}/backup.sh >> /proc/1/fd/1 2>&1\n" | crontab -
else
    printf "[INFO] Cron expression empty. Won't create cron.d entry.\n"
fi

printf "[INFO] Starting cron.\n"
crond -f
