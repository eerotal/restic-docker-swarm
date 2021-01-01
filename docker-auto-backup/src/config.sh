# WORKDIR=... is inserted here by Dockerfile.
BACKUP_DIR="/backup/"
ARCHIVE_DIR="/archive/"
TMP_DIR="/tmp/"

LAST_BACKUP_FILE="$WORKDIR/last_backup"
ENV_FILE="$WORKDIR/.env"
CRONTAB_FILE="/etc/cron.d/docker-autobackup"
LABEL_PREFIX="docker-auto-backup."
DOCKER_SOCK="/var/run/docker.sock"

SECRETS_BASE_DIR="/run/secrets/"
SSH_KEY_FILE="$SECRETS_BASE_DIR/ssh-key"
SSH_KNOWN_HOSTS_FILE="$SECRETS_BASE_DIR/ssh-known-hosts"
ENCRYPTION_KEY_FILE="$SECRETS_BASE_DIR/gpg-encryption-key"

SSH_OPTS="-i $SSH_KEY_FILE -o UserKnownHostsFile=$SSH_KNOWN_HOSTS_FILE"
