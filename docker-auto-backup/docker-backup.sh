#!/bin/sh

#
# A script for periodically backing up, archiving, encrypting and rsyncing
# the contents of a Docker volume. This script runs as a cron job.
#

#
# TODO: Rotate old backups.
# TODO: Use Docker labels to dump DB before backing up.
#

set -e

. /root/docker-config.sh

# Load environment from a script because we are running in a cron job.
. "$ENV_FILE"

# Skip backup if /backup directory is empty.
if [ -z "$(ls -A $BACKUP_DIR)" ]; then
    echo "[INFO] Nothing to backup. Skipping..."
    #exit 0
fi

backup_tmp="docker-volume-backup.tar.gz"
backup_enc="backup_$(date +"%Y-%m-%dT%H-%M-%S").tar.gz.gpg"

echo "[INFO] Backup started at $(date -Iseconds)"

# Archive files into a .tar.gz archive in a temporary directory.
cd "$BACKUP_DIR"
tar -zcf "$TMP_DIR/$backup_tmp" .

if [ ! -f "$ENCRYPTION_KEY_FILE" ]; then
    echo "[ERROR] You must specify a GPG public key to use for encryption."
    exit 1
fi

# Encrypt the .tar.gz archive using GPG and a user-supplied public key.
echo "[INFO] Encrypting archive."
gpg --verbose \
    --output "$TMP_DIR/$backup_enc" \
    --encrypt \
    --recipient-file "$ENCRYPTION_KEY_FILE" \
    "$TMP_DIR/$backup_tmp"

# Remove (unencrypted) temporary files.
echo "[INFO] Removing temporary files."
rm -fv "$TMP_DIR/$backup_tmp"

# Store the encrypted backup archive locally.
echo "[INFO] Moving encrypted archive to output directory."
mkdir -p "$ARCHIVE_DIR"
mv -v "$TMP_DIR/$backup_enc" "$ARCHIVE_DIR"

# Rsync the encrypted backup archive onto a remote backup server.
if [ "$ENABLE_RSYNC" = "y" ]; then
    if [ ! -f "$SSH_KEY_FILE" ]; then
        echo "[Error] You must mount an SSH key at '$SSH_KEY_FILE'."
        exit 1
    fi

    if [ ! -f "$SSH_KNOWN_HOSTS_FILE" ]; then
        echo "[Error] You must mount a known_hosts file at '$SSH_KNOWN_HOSTS_FILE'."
        exit 1
    fi

    if [ -z "$SSH_HOST" ]; then
        echo "[Error] You must specify a valid SSH host in SSH_HOST."
        exit 1
    fi

    if [ -z "$RSYNC_DEST" ]; then
        echo "[Error] You must specify a rsync destination path in RSYNC_DEST."
        exit 1
    fi

    echo "[INFO] Rsync encrypted archive to backup server."
    export RSYNC_RSH="ssh $SSH_OPTS"
    rsync -av "$ARCHIVE_DIR/$backup_enc" "${SSH_HOST}:${RSYNC_DEST}"
else
    echo "[INFO] Skipping rsync."
fi

# Rotate backups.
sh "${WORKDIR}/docker-rotate-local.sh"
sh "${WORKDIR}/docker-rotate-remote.sh"

# Store the last time a backup succeeded. This is used by the
# periodic Docker healthcheck.
date +"%s" > "$LAST_BACKUP_FILE"

echo "[INFO] Backup done at $(date -Iseconds)."
