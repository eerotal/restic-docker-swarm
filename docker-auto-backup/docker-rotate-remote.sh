#!/bin/sh

set -e

. /root/docker-config.sh
. "$ENV_FILE"

BOLD=$(tput bold)
NORMAL=$(tput sgr0)

echo "[INFO] Rotating remotely stored backups."

export RSYNC_RSH="ssh $SSH_OPTS"
rsync -aq "${WORKDIR}/docker-rotate-backups.sh" "${SSH_HOST}:${RSYNC_DEST}/tmp.sh"

echo "${BOLD}[INFO] ---- RUNNING IN REMOTE SHELL${NORMAL}"
ssh $SSH_OPTS \
    "$SSH_HOST" \
    "cd $RSYNC_DEST && sh tmp.sh '$RSYNC_DEST' '$ROTATE_AFTER' && rm -f tmp.sh "
echo "${BOLD}[INFO] ---- RETURNING TO LOCAL SHELL${NORMAL}"
