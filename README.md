# docker-auto-backup - Automate encrypted Docker volume backups

`docker-auto-backup` is a utility Docker image for automating Docker
volume backups to local and remote directories. Backups are encrypted
using `gpg` and remote backup storage is implemented using `sshg` and `rsync`.

## Usage

A example `docker-compose.yml` file is provided in this repository. In a
nutshell you must configure the container to your liking with the provided
Docker environment variables listed in the table below.

| Variable     | Default   | Description                                                   |
|--------------|-----------|---------------------------------------------------------------|
| CRON_EXPR    | 0 4 * * * | The cron expression for automatic backups.                    |
| ENABLE_RSYNC | n         | Enable (y) / disable (n) backup rsync'ing to a remote server. |
| RSYNC_DEST   |           | The backup archive directory path on the remote SSH server.   |
| SSH_HOST     |           | The SSH user@host where backups are rsync'd to.               |
| ROTATE_AFTER | 5         | How many backups to keep locally and on the remote.           |

Additionally, if using remote backups, you must also mount volumes or files at
the following locations in the container.

| Mountpoint             | Example source       | Description                                                 |
|------------------------|----------------------|-------------------------------------------------------------|
| /backup/               | backup-volume        | The directory from where backups are made.                  |
| /archive/              | ./archive/           | The directory where local backups are stored.               |
| /root/encryption_key   | ./pubkey.gpg         | A gpg public key to use for encrypting backups.             |
| /root/.ssh/ssh_key     | ~/.ssh/id_rsa        | An ssh private key to use for accessing the remote server.  |
| /root/.ssh/known_hosts | ~/.ssh/known_hosts   | An ssh `known_hosts` file which includes the remote server. |
| /var/run/docker.sock   | /var/run/docker.sock | Docker socket required for running hooks.                   |

You should mount the volume you want to backup at `/backup/`. All other paths
can be bind mounted.

After configuring the container, you can simply start it up and it'll
automatically backup your volume according to `CRON_EXPR`. If you are using
`rsync` to copy the backups onto a remote server, make sure your SSH key
isn't password protected.

## Dependencies

`docker-auto-backup` is a self-contained Docker image based on Alpine Linux
so the only "dependency" you need is the Docker runtime. If you want to rsync
backups to a remote server, you need to install Python3, ssh and rsync there.
No other dependencies are needed.

## Manual backups

You can also backup volumes manually by executing the `backup.sh` script
in the container. You can start an interactive shell in a Docker container
by running:

`docker exec -it [container id/name] sh`

If you are using using docker-compose you can also use:

`docker-compose exec [service] sh`

The `backup.sh` script is located in `/root` and can be run without
specifying any arguments: `cd /root && sh backup.sh`.

## Pre- and post-hooks

`docker-auto-backup` also supports running pre- and post-backup hooks in
containers. Hooks are defined using Docker labels and the `CONTAINERS`
environment variable. To add a pre- or post-backup hook to a service container,
do the following:

1. Add the container name to the `CONTAINERS` environment variable. This is
   a space-separated list of container names. Only containers listed in this
   variable are included in hook searches.1
2. Add a lable to the service container. The format of the label must be
   `docker-auto-backup.[pre/post]-hook=[shell command to execute]`.

Once the hooks are defined, the `docker-auto-backup` container automatically
executes them when needed. Pre-hooks are executed in all configured containers
before each backup. Post-hooks are executed in all configured containers after
each backup.

Hooks are useful for example when backing up a database. You can dump the
database to a file in a pre-backup hook and delete the database dump in a
post-backup hook.

## Docker container healthcheck

The default image configuration also includes a Docker HEALTHCHECK. The actual
healthcheck logic is implemented in `/root/docker-healthcheck.sh`. The default
configuration is described in the table below.

| Value                                | Default value |
|--------------------------------------|---------------|
| interval                             | 8600s         |
| timeout                              | 5s            |
| start-period                         | 1ms           |
| retries                              | 2             |
| docker-healthcheck.sh fail threshold | 86400         |

This configuration runs `docker-healthcheck.sh` every day and marks the
container healthy if a backup has succeeded in the last 86400 seconds, ie.
the last successful backup is a day old at the most. It takes two healthcheck
failures to mark the container unhealthy because `retries=2`. This configuration
probably only makes sense if you also use the default `CRON_EXPR` expression
`0 4 * * *`.

## License

This Docker image is license under the BSD 3-clause license. See the whole
license text in `LICENSE.md` in the root of this repository.
