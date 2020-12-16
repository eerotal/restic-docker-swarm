#!/bin/sh

set -e

. /root/docker-config.sh
. "$ENV_FILE"

echo "[INFO] Rotating locally stored backups."

sh "${WORKDIR}/docker-rotate-backups.sh" "$ARCHIVE_DIR" "$ROTATE_AFTER"
