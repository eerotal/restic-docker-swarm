# restic-docker-swarm - Encrypted Docker Swarm backups with restic

`restic-docker-swarm` is a utility Docker image for automating Docker
volume backups to remote directories using *restic*.

`restic-docker-swarm` consists of two container images: `restic-docker-swarm-agent`
and `restic-docker-swarm-server`. The agent container periodically runs restic to backup
Docker volumes. The server container runs an OpenSSH server which can be used to store the
restic repositories remotely via SFTP. You can also use a normal SSH server as the remote
in which case you don't need to deploy the server image at all.

## Images

Docker images are available on Docker Hub:
[eerotal/restic-docker-swarm-agent](https://hub.docker.com/repository/docker/eerotal/restic-docker-swarm-agent)
and [eerotal/restic-docker-swarm-server](https://hub.docker.com/repository/docker/eerotal/restic-docker-swarm-server).

## Usage

A example Swarm stack file `test/stack.yml` is provided in this repository. In a
nutshell, you must configure the containers to your liking using environment
variables, service labels, volume mounts and Docker secrets. See the sections below
for information on how the agent and server images are configured. Using the stack file
from `test/stack.yml` as an example is the best way to get started.

## Agent configuration

The `restic-docker-swarm-agent` container can be configured with the following
environment variables.

| Variable                  | Default                             | Description                                                  |
|---------------------------|-------------------------------------|--------------------------------------------------------------|
| SSH_HOST                  |                                     | Name that resolves to the remote SSH host. *1                |
| SSH_PORT                  | 2222                                | SSH port used by the remote host.                            |
| SSH_PRIVKEY_FILE          | /run/secrets/restic-ssh-privkey     | A path to the SSH identity file in the container. *2         |
| SSH_KNOWN_HOSTS_FILE      | /run/secrets/restic-ssh-known-hosts | A path to the SSH known hosts file in the container. *2      |
| RESTIC_REPO_PASSWORD_FILE | /run/secrets/restic-repo-password   | A path to the restic repo password file in the container. *2 |
| BACKUP_FORGET_POLICY      | 1 1 1 1 1 0y0m0d0h 0 false          | Policy for forgetting and pruning old backups. *3            |
| EXTRA_ARGS                |                                     | Extra arguments passed to the internal rds-run program. *4   |

**Notes:**

1. You can use the name of the server service here if you're also running it
   as a Swarm service (eg. using `restic-docker-swarm-server`).
2. The `*_FILE` variables are paths to the respective files inside the container.
   You can use these to configure eg. paths to secrets but usually the defaults
   should work fine.
3. The expected format for the forget policy is `HOURLY DAILY WEEKLY MONTHLY YEARLY
   WITHIN LAST PRUNE [TAG]` where each word corresponds to an argument passed to
   'restic forget'. PRUNE should be 'true' or 'false' depending on whether
   forgotten backups should be pruned automatically. '[TAG]' is optional and it
   can also be a comma separated list of multiple tags to keep. See the [restic
   documentation](https://restic.readthedocs.io/en/latest/060_forget.html) for more
   info.
4. Take a look into the source repository for more information. For example, you
   can pass `--verbose` in `EXTRA_ARGS` for more verbose logs but usually this
   variable is not needed.

Each service you want to back up should define the following **service** labels.

| Label                | Description                                        |
|----------------------|----------------------------------------------------|
| rds.backup           | "true" to enable backups.                          |
| rds.backup.repos     | Repository paths. *1                               |
| rds.backup.run-at    | Cron expression for taking backups.                |
| rds.backup.pre-hook  | Pre-backup hook command to run in the service. *2  |
| rds.backup.post-hook | Post-backup hook command to run in the service. *2 |

**Notes:**

1. The `rds.repos` label sets the repository path(s) on the remote SFTP server as well
   as the backup path(s) in the agent container. Repo paths must always be relative.
   Absolute repository paths are skipped with an error. For example, if you set
   `rds.repos: my-volume`, the backups will be stored on the remote server in
   `my-volume` under the default SFTP directory. The backups will also be taken
   from `/backup/my-volume/` in the `restic-docker-swarm-agent` container meaning
   you must mount your volume at this path. You can also specify multiple repositories
   as a comma separated list. This is useful for example if you want to backup
   multiple volumes from a single service.
2. See the section Pre- and post-backup hooks.

Secrets are passed to the container using Docker Swarm secrets. The following
secrets are required

| Secret                 | Description                                                            |
|------------------------|------------------------------------------------------------------------|
| restic-ssh-privkey     | The SSH private key used for authenticating to the remote server.      |
| restic-ssh-known-hosts | An SSH known_hosts file which contains an entry for the remote server. |
| restic-repo-password   | The password to use for the restic repository.                         |

A suitable known_hosts file for `restic-ssh-known-hosts` is automatically generated
by the server image on first boot. The file is placed at `/etc/ssh/host_fingerprints/known_hosts`.
You can create the `restic-ssh-known-hosts` secret directly from this file. In the
example setup at `test/stack.yml` the known_hosts file is directly mounted between the
server and agent containers and `SSH_KNOWN_HOSTS_FILE` is modified to suit. This will,
however, only work if the agent and server containers are running on the same node since
volumes are not shared between nodes by default.

If you run the containers on separate nodes (which usually should be the case) you have to start the
server container first and manually create a Swarm secret from the known_hosts file it generates.
After doing this you can launch all agent containers which use manually created Swarm secret.

## Server configuration

The `restic-docker-swarm-server` image can be configured with the following
environment variables.

| Variable                  | Default                             | Description                                                  |
|---------------------------|-------------------------------------|--------------------------------------------------------------|
| SSHD_PORT                 | 2222                                | SSH port used by sshd.                                       |
| SWARM_SERVICE             |                                     | A name that resolves to the **server** service.              |

You should mount a volume at `/home/restic` for preserving your restic repositories
across container reboots.

## Agent CLI usage

The `restic-docker-swarm-agent` image includes the restic binary which you can
use to manage your restic repositories, manually take backups, restore backups etc.

You can access the container by running

```
docker exec -it CONTAINER_ID sh
```

Because using the restic binary directly requires you to specify quite a few
arguments manually, the agent container also includes a script called *runrestic.py*
for running restic with a default set of arguments. This script is also symlinked to
PATH as *runrestic* so that you can easily run it with eg. `docker exec ...`.

The default command *runrestic* uses depends on the agent configuration and it is
such that restic performs all operations on the remote repository configured for
the agent. You can see the default command and a help text by running *runrestic*
without arguments. All arguments passed to *runrestic* are passed directly to the
original restic binary after the default ones.

The agent container shell also prints some convenient help information on login.

## Server CLI usage

The `restic-docker-swarm-server` image includes the restic binary which you can
use to manage your restic repositories, manually take backups, restore backups etc.
Restic repositories are stored at `/home/restic` by default.

You can access the container by running

```
docker exec -it CONTAINER_ID sh
```

The server container shell also prints some convenient information and statistics
on login.

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

TODO

## License

This project is license under the BSD 3-clause license. See the whole
license text in `LICENSE.md` in the root of this repository.
