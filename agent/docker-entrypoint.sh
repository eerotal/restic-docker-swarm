#!/bin/sh

if [ $(stat -c "%a" "${SSH_PRIVKEY_FILE}") != "600" ]; then
    printf "[WARNING] Permissions for ${SSH_PRIVKEY_FILE} are too open. If "
    printf "possible, you should set them to: UID=${USER_UID}, "
    printf "MODE=600.\n"
fi

# Copy the SSH private key to /home/${USER}/.ssh because the permissions
# of the original file can't be changed (read-only).
printf "[INFO] Copying SSH private key to /home/${USER}/.ssh.\n"
mkdir -p "/home/${USER}/.ssh/"
chmod 700 "/home/${USER}/.ssh/"
cp "${SSH_PRIVKEY_FILE}" "/home/${USER}/.ssh/id"
chmod 600 "/home/${USER}/.ssh/id"
chown "${USER}:root" "/home/${USER}/.ssh/id"

# Switch away from root for increased security.
su "${USER}"

printf "[INFO] Waiting 5s before starting the backup daemon.\n"
sleep 5

python3 rds/rds.py \
    --verbose \
    --ssh-host="${SSH_HOST}" \
    --ssh-port="${SSH_PORT}" \
    --ssh-option="-o UserKnownHostsFile=${SSH_KNOWN_HOSTS_FILE}" \
    --ssh-option="-i /home/${USER}/.ssh/id" \
    --repo-path="${REPO_PATH}" \
    --restic-arg="--password-file=${RESTIC_REPO_PASSWORD_FILE}" \
    --service-name="${SERVICE_NAME}" \
    --pre-hook="${PRE_HOOK}" \
    --post-hook="${POST_HOOK}" \
    --run-at="${RUN_AT}" \
    "${EXTRA_ARGS}" \
    "${BACKUP_PATH}"
