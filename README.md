# docker-auto-backup - Automate encrypted Docker volume backups

`docker-auto-backup` is a utility Docker image for automating Docker
volume backups to local and remote directories. Backups are encrypted
using GPG and remote backup storage is implemented using rsync.

## How to use docker-auto-backup

A example `docker-compose.yml` file is provided in this repository. In a
nutshell you must configure the container to your liking with the provided
Docker environment variables listed in the table below.

| VARIABLE     | DEFAULT   | DESCRIPTION                                                   |
|--------------|-----------|---------------------------------------------------------------|
| CRON_EXPR    | 0 4 * * * | The cron expression for automatic backup.                     |
| ENABLE_RSYNC | n         | Enable (y) / disable (n) backup rsync'ing to a remote server. |
| RSYNC_DEST   | <empty>   | The backup archive directory path on the remote SSH server.   |
| SSH_HOST     | <empty>   | The SSH user@host where backups are rsync'd to.               |
| ROTATE_AFTER | 5         | How many backups to keep locally and on the remote.           |

Additionally, if using remote backups, you must also mount volumes or files at
the following locations in the container.

| FILE                   | DESCRIPTION                                                               |
|------------------------|---------------------------------------------------------------------------|
| /archive/              | The directory where the local backups are stored.                         |
| /backup/               | The directory from where backups are taken.                               |
| /root/encryption_key   | A GPG public key to use for encrypting backups.                           |
| /root/.ssh/ssh_key     | An SSH key to use for accessing the remote server.                        |
| /root/.ssh/known_hosts | An SSH known_hosts file for accepting the signature of the remote server. |

You should mount the volume you want to backup at `/backup/`. All other paths
can be bind mounted.

After configuring the container, you can simply start it up and it'll
automatically backup your volume according to CRON_EXPR. If you are using
rsync to copy the backups onto a remote server, make sure your SSH key
isn't password protected.
