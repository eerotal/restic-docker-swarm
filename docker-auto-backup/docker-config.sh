# WORKDIR=... is inserted here by Dockerfile.
BACKUP_DIR="/backup/"
ARCHIVE_DIR="/archive/"
TMP_DIR="/tmp/"

LAST_BACKUP_FILE="$WORKDIR/last_backup"
ENV_FILE="$WORKDIR/.env"
CRONTAB_FILE="/etc/cron.d/docker-autobackup"
ENCRYPTION_KEY_FILE="$WORKDIR/encryption_key"
SSH_KEY_FILE="$WORKDIR/.ssh/ssh_key"
SSH_KNOWN_HOSTS_FILE="$WORKDIR/.ssh/known_hosts"

SSH_OPTS="-i $SSH_KEY_FILE -o UserKnownHostsFile=$SSH_KNOWN_HOSTS_FILE"
