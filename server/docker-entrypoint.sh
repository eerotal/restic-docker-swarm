#!/bin/sh

set -e

AUTHORIZED_KEYS_FILE="/home/${USER}/.ssh/authorized_keys"
HOST_FINGERPRINTS_FILE="/etc/ssh/host_fingerprints/known_hosts"

# Set random password for the main user.
printf "[INFO] Setting random password for user ${USER}.\n"
pass="$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 1024 | head -n 1)"
echo "${USER}:${pass}" | chpasswd

# Generate SSH host keys if they don't exist.
if [ -z "$(ls /etc/ssh/ssh_host_* 2> /dev/null)" ]; then
    printf "[INFO] Generating SSH host keys.\n"
    ssh-keygen -A
fi

# Dump host public key fingerprints to file.
printf "[INFO] Dumping SSH host key fingerprints to file.\n"
/usr/sbin/sshd -D -p ${SSHD_PORT} &
sshd_pid=$!
mkdir -p "$(dirname "${HOST_FINGERPRINTS_FILE}")"
while true; do
    set +e
    ssh-keyscan -p "${SSHD_PORT}" "${SWARM_SERVICE}" > "${HOST_FINGERPRINTS_FILE}" 2>/dev/null
    if [ "$?" != 0 ]; then
        printf "[INFO] Waiting for temporary sshd process to start...\n"
        sleep 1
    else
        break
    fi
done
set -e
kill ${sshd_pid}

printf "[INFO] The fingerprints of the SSH server's host public keys are:\n\n"
cat "${HOST_FINGERPRINTS_FILE}"
printf "\n"
printf "[INFO] These are also saved in ${HOST_FINGERPRINTS_FILE}.\n"

# Install authorized SSH public keys for ${USER}.
if [ -d /run/secrets/ ]; then
    printf "[INFO] Installing SSH public keys for user ${USER}:\n"

    mkdir -p "$(dirname "${AUTHORIZED_KEYS_FILE}")"
    printf "" > "${AUTHORIZED_KEYS_FILE}"

    for keyfile in $(ls /run/secrets/); do
        printf "${keyfile}\n"
        cat "/run/secrets/${keyfile}" >> "${AUTHORIZED_KEYS_FILE}"
    done

    chown -R ${USER}:${USER} "$(dirname "${AUTHORIZED_KEYS_FILE}")"
    chmod 700 "$(dirname "${AUTHORIZED_KEYS_FILE}")"
    chmod 600 "${AUTHORIZED_KEYS_FILE}"
else
    printf "[WARNING] No authorized SSH public keys found. You won't be "
    printf "able to access the builtin SSH server.\n"
fi

printf "[INFO] Starting sshd.\n"
/usr/sbin/sshd -D -e -p ${SSHD_PORT} &

wait
