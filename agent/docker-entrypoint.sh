#!/bin/sh

if [ $(stat -c "%a" "${SSH_PRIVKEY_FILE}") != "600" ]; then
    printf "[WARNING] Permissions for ${SSH_PRIVKEY_FILE} are too open. If "
    printf "possible, you should set them to: UID=${TARGET_USER_UID}, "
    printf "MODE=600.\n"
fi

# Copy the SSH private key to /home/${TARGET_USER}/.ssh because the permissions
# of the original file can't be changed (read-only).
printf "[INFO] Copying SSH private key to ${SSH_ID_FILE}.\n"
mkdir -p "$(dirname ${SSH_ID_FILE})"
chmod 700 "$(dirname ${SSH_ID_FILE})"
cp "${SSH_PRIVKEY_FILE}" "${SSH_ID_FILE}"
chmod 600 "${SSH_ID_FILE}"
chown "${TARGET_USER}:root" "${SSH_ID_FILE}"

# Switch away from root for increased security.
su "${TARGET_USER}"

rds-agent \
    --backup-base="${BACKUP_BASE}" \
    --ssh-host="${SSH_HOST}" \
    --ssh-port="${SSH_PORT}" \
    --ssh-option="-o UserKnownHostsFile=${SSH_KNOWN_HOSTS_FILE}" \
    --ssh-option="-i ${SSH_ID_FILE}" \
    --restic-arg="--password-file=${RESTIC_REPO_PASSWORD_FILE}" \
    ${EXTRA_ARGS} \
    "${BACKUP_PATH}"
