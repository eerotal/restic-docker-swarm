# restic-docker-swarm - Encrypted Docker Swarm backups with restic

![Build and push to Docker Hub badge](https://github.com/eerotal/restic-docker-swarm/workflows/Deployment/badge.svg)
![Unit tests badge](https://github.com/eerotal/restic-docker-swarm/workflows/Tests/badge.svg)

`restic-docker-swarm` is a utility Docker image for automating Docker volume backups to
SFTP directories using *restic*. `restic-docker-swarm` consists of one Docker image:
`restic-docker-swarm-agent`. The project also includes another image: `restic-docker-swarm-server`,
however this image is mainly intended for development purposes.

## Images

Docker images are available on Docker Hub:
[eerotal/restic-docker-swarm-agent](https://hub.docker.com/repository/docker/eerotal/restic-docker-swarm-agent).

## Usage

A example Swarm stack file `test/stack.yml` is provided in this repository. In a
nutshell, you must configure the containers to your liking using environment
variables, service labels, volume mounts and Docker secrets. Using the stack file
from `test/stack.yml` as an example is the best way to get started, however some
modifications are needed because that stack file is mainly intended for development
testing.

## Agent configuration

The `restic-docker-swarm-agent` container can be configured with the following
environment variables.

| Variable                  | Default                             | Description                                       |
|---------------------------|-------------------------------------|---------------------------------------------------|
| SSH_HOST                  |                                     | Remote SFTP host.                                 |
| SSH_PORT                  | 2222                                | SFTP port used by the remote.                     |
| SSH_PRIVKEY_FILE          | /run/secrets/restic-ssh-privkey     | SSH identity file in the container.               |
| SSH_KNOWN_HOSTS_FILE      | /run/secrets/restic-ssh-known-hosts | SSH known hosts file in the container.            |
| RESTIC_REPO_PASSWORD_FILE | /run/secrets/restic-repo-password   | Restic repo password file in the container.       |
| BACKUP_FORGET_POLICY      | 1 1 1 1 1 0y0m0d0h 0 false          | Policy for forgetting and pruning old backups.    |
| EXTRA_ARGS                |                                     | Extra arguments for the internal rds-run program. |

**Notes:**

The format for *BACKUP_FORGET_POLICY* is

```
    HOURLY DAILY WEEKLY MONTHLY YEARLY WITHIN LAST PRUNE [TAG]
```

The fields HOURLY, DAILY, WEEKLY, MONTHLY and YEARLY should contain the number of snapshots
of each type to keep. For example, if DAILY = 2, two of the newest daily snapshots are kept
and older ones are forgotten.

The WITHIN field can be used to specify a duration within which snapshots are kept. For example,
if WITHIN = 1y2m5d10h, all snapshots taken within 1 year, 2 months, 5 days and 10 hours are kept.

If TAG is set, all snapshots with the given tag are kept. Multiple tags can be specified
as a comma separated list. The TAG field is optional.

Each service you want to back up should define the following **service** labels.

## Service configuration

Services to be backed up must be configured with the following service labels. You must also
mount the volumes to be backed up under the */backup* path in the agent container.

| Label                | Description                                     | Notes |
|----------------------|-------------------------------------------------|-------|
| rds.backup           | "true" to enable backups.                       |       |
| rds.backup.repos     | Backup paths.                                   | 1     |
| rds.backup.run-at    | Cron expression for taking backups.             |       |
| rds.backup.pre-hook  | Pre-backup hook command to run in the service.  | 2     |
| rds.backup.post-hook | Post-backup hook command to run in the service. | 2     |

**Notes:**

1. The `rds.repos` label sets the backup path(s) in the agent container. Backups
   paths are relative to */backup* path in the container. Passing an absolute path
   will cause an error. The repository paths also define the destination path on the
   SFTP server. For example, if you set `rds.repos: my-volume`, backups will be stored
   on the remote server in `my-volume` under the default SFTP directory and the backups
   will be taken from `/backup/my-volume/` in the `restic-docker-swarm-agent` container.
   You can also specify multiple repositories as a comma separated list. This is useful
   for example if you want to backup multiple volumes from a single service.
2. See the section Pre- and post-backup hooks.

Secrets are passed to the container using Docker Swarm secrets. The following
secrets are required

| Secret                 | Description                                                            |
|------------------------|------------------------------------------------------------------------|
| restic-ssh-privkey     | An SSH private key used for authenticating to the remote server.       |
| restic-ssh-known-hosts | An SSH known_hosts file which contains an entry for the remote server. |
| restic-repo-password   | The password to use for restic repositories.                           |

## Agent CLI usage

The `restic-docker-swarm-agent` image includes the restic binary which you can
use to manage your restic repositories, manually take backups, restore backups etc.

You can access the container by running

```
docker exec -it CONTAINER_ID sh
```

The agent container includes a wrapper called *rds-run* for running *restic*
with a default set of arguments. *rds-run* is by default configured to perform all
operations on the SFTP host configured for the agent container. Run `rds-run -h`
for a help message. Arguments passed to *rds-run* are forwarded to the *restic*
binary following the default ones.

Example usage:

```
/home/restic # rds-run -r postgres-1 list snapshots
subprocess: restic -o sftp.command='ssh restic@rds-server -o UserKnownHostsFile=/root/host_fingerprints/known_hosts -i /home/restic/.ssh/id -p 2222 -s sftp' -r sftp:restic@rds-server:postgres-1 --password-file /run/secrets/restic-repo-password snapshots
repository d564af4e opened successfully, password is correct
ID        Time                 Host          Tags        Paths
---------------------------------------------------------------------------
154d5203  2021-05-02 16:53:01  fc18418c0d6f              /backup/postgres-1
---------------------------------------------------------------------------
1 snapshots
/home/restic #
```

## Pre- and post-backup hooks

The pre- and post-backup hooks are executed in a service container before and
after backup respectively. Even if a service has multiple replicas (ie. multiple
containers), the hooks are only run in one container. The container where hooks
are run is not guaranteed to be the same between backups.

A hook must be a single shell command. If you need to run a script, wrap the
script in `sh -c '...'` or put a script file directly into the container image
and execute that instead. The latter approach should be preferred.

Hooks are useful for example when backing up a database. You can dump the
database to a file in a pre-backup hook and delete the database dump in a
post-backup hook. The example stack in `test/stack.yml` uses hooks to backup
a Postgres database in this manner.

## Container healthcheck

The agent image includes a healthcheck which periodically queries the status of
all backups from the backup scheduler and if any of the backups has failed, marks
the container as unhealthy. The status queries are done via a simple status
query server running in *rds-agent*.

## License

This project is license under the BSD 3-clause license. See the whole
license text in `LICENSE.md` in the root of this repository.
