#!/bin/sh

#
# A script for periodically backing up, archiving, encrypting and rsyncing
# the contents of a Docker volume. This script runs as a cron job.
#

set -e

. /root/config.sh

# Load environment from a script because we are running in a cron job.
. "$ENV_FILE"

exec_hooks() {
    #
    # Execute hooks in external containers.
    #
    # Containers are identifier by two labels:
    #
    #   - ${LABEL_PREFIX}.identifier must match ${BACKUP_IDENTIFIER}.
    #   - ${LABELPREFIX}.${1} must exist. The value of the label is
    #     the shell command that's executed in the container.
    #
    # This function requires that the Docker socket is mounted into
    # the docker-auto-backup container. If the socket is not mounted,
    # this function does nothing.
    #
    # $1 = The hook to execute.
    #

    if [ -e "${DOCKER_SOCK}" ]; then
        printf "[INFO] Running ${1}.\n"

        f1="label=${LABEL_PREFIX}identifier=${BACKUP_IDENTIFIER}"
        f2="label=${LABEL_PREFIX}${1}"

        ids="$(docker container ls --filter "$f1" --filter "$f2" -q)"
        printf "[INFO] --> Found $(printf "$ids" | wc -l) container(s) with "
        printf "hooks and backup ID: ${BACKUP_IDENTIFIER}.\n"

        for id in $ids; do
            template="{{ index .Config.Labels  \"${LABEL_PREFIX}${1}\" }}"
            cmd="$(docker inspect --format "$template" $id)"
            printf "[INFO] --> Executing '${cmd}' in '${id}'.\n"
            docker exec $id $cmd
        done
    else
        printf "[INFO] Skipping ${1} because ${DOCKER_SOCK} doesn't exist.\n"
    fi
}

backup_tmp="docker-volume-backup.tar.gz"
backup_enc="$(date +"%Y-%m-%dT%H-%M-%S").tar.gz.gpg"

printf "[INFO] Backup started at $(date -Iseconds).\n"

# Execute pre-hooks.
exec_hooks pre-hook

# Skip backup if /backup directory is empty.
if [ -z "$(ls -A $BACKUP_DIR)" ]; then
    printf "[INFO] Nothing to backup. Skipping...\n"
    exit 0
fi

# Archive files into a .tar.gz archive in a temporary directory.
cd "$BACKUP_DIR"
tar -zcf "$TMP_DIR/$backup_tmp" .

if [ ! -f "$ENCRYPTION_KEY_FILE" ]; then
    printf "[ERROR] You must specify a GPG public key to use for encryption.\n"
    exit 1
fi

# Encrypt the .tar.gz archive using GPG and a user-supplied public key.
printf "[INFO] Encrypting archive.\n"
gpg --verbose \
    --output "$TMP_DIR/$backup_enc" \
    --encrypt \
    --recipient-file "$ENCRYPTION_KEY_FILE" \
    "$TMP_DIR/$backup_tmp"

# Remove (unencrypted) temporary files.
printf "[INFO] Removing temporary files.\n"
rm -fv "$TMP_DIR/$backup_tmp"

# Store the encrypted backup archive locally.
printf "[INFO] Moving encrypted archive to output directory.\n"
mkdir -p "$ARCHIVE_DIR"
mv -v "$TMP_DIR/$backup_enc" "$ARCHIVE_DIR"

# Rotate locally stored backups.
printf "[INFO] Rotating locally stored backups.\n"
python3 "${WORKDIR}/rotate.py" \
    --dir="$ARCHIVE_DIR" \
    --keep="$ROTATE_AFTER"

# Rsync the encrypted backup archive onto a remote backup server.
if [ "$ENABLE_RSYNC" = "y" ]; then
    if [ ! -f "$SSH_KEY_FILE" ]; then
        printf "[Error] You must mount an SSH key at '$SSH_KEY_FILE'.\n"
        exit 1
    fi
    if [ ! -f "$SSH_KNOWN_HOSTS_FILE" ]; then
        printf "[Error] You must mount a known_hosts file at '$SSH_KNOWN_HOSTS_FILE'.\n"
        exit 1
    fi
    if [ -z "$SSH_HOST" ]; then
        printf "[Error] You must specify a valid SSH host in SSH_HOST.\n"
        exit 1
    fi
    if [ -z "$RSYNC_DEST" ]; then
        printf "[Error] You must specify a rsync destination path in RSYNC_DEST.\n"
        exit 1
    fi

    printf "[INFO] Rsync'ing encrypted archive to backup server.\n"
    export RSYNC_RSH="ssh $SSH_OPTS"
    rsync -av "$ARCHIVE_DIR/$backup_enc" "${SSH_HOST}:${RSYNC_DEST}"

    # Rotate backups stored on a remote.
    printf "[INFO] Rotating remotely stored backups.\n"

    export RSYNC_RSH="ssh $SSH_OPTS"
    rsync -aq \
        "${WORKDIR}/rotate.py" \
        "${SSH_HOST}:${RSYNC_DEST}/rb.py"

    printf "[INFO] ---- RUNNING IN REMOTE SHELL\n"
    ssh $SSH_OPTS "$SSH_HOST" \
        "cd $RSYNC_DEST && " \
        "python3 rb.py -d'${RSYNC_DEST}' -k'${ROTATE_AFTER}' && " \
        "rm -f rb.py"
    printf "[INFO] ---- RETURNING TO LOCAL SHELL\n"
else
    printf "[INFO] Skipping rsync.\n"
fi

# Store the last time a backup succeeded. This is used by the
# periodic Docker healthcheck.
date +"%s" > "$LAST_BACKUP_FILE"

# Execute post-hooks.
exec_hooks post-hook

printf "[INFO] Backup done at $(date -Iseconds).\n"
