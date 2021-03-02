# restic-docker-swarm - Encrypted Docker Swarm backups with restic

`restic-docker-swarm` is a utility Docker image for automating Docker
volume backups to remote directories using *restic*.

`restic-docker-swarm` consists of two container images: `restic-docker-swarm:agent`
and `restic-docker-swarm:server`. The agent container periodically runs restic to backup
Docker volumes. The server container runs an OpenSSH server which can be used to store the
restic repositories remotely via SFTP.

## Images

Docker images are available on Docker Hub:
[eerotal/restic-docker-swarm](https://hub.docker.com/repository/docker/eerotal/restic-docker-swarm).

## Usage

A example Swarm stack file `test/stack.yml` is provided in this repository. In a
nutshell, you must configure the containers to your liking using environment
variables, volume mounts and Docker secrets. See the sections below for information
on how the agent and server images are configured. Following the example stack
file is the best way to get started.

## Agent configuration

The `restic-docker-swarm:agent` image can be configured with the following
environment variables.

| Variable                  | Default                             | Description                                                  |
|---------------------------|-------------------------------------|--------------------------------------------------------------|
| SSH_HOST                  |                                     | Name that resolves to the remote SSH host. *1                |
| SSH_PORT                  | 2222                                | SSH port used by the remote host.                            |
| BACKUP_PATH               | /backup                             | The path in the container from which backups are taken. *2   |
| REPO_PATH                 |                                     | Repository path on the remote host. *3                       |
| SERVICE_NAME              |                                     | The name of the service to backup. *4                        |
| PRE_HOOK                  |                                     | A command to run in the service before backup. *5            |
| POST_HOOK                 |                                     | A command to run in the service after backup. *5             |
| RUN_AT                    |                                     | A cron expression that sets when backups should be taken.    |
| SSH_PRIVKEY_FILE          | /run/secrets/restic-ssh-privkey     | A path to the SSH identity file in the container. *6         |
| SSH_KNOWN_HOSTS_FILE      | /run/secrets/restic-ssh-known-hosts | A path to the SSH known hosts file in the container. *6      |
| RESTIC_REPO_PASSWORD_FILE | /run/secrets/restic-repo-password   | A path to the restic repo password file in the container. *6 |
| EXTRA_ARGS                |                                     | Extra arguments passed to the internal rds.py program. *7    |

**Notes:**

1. You can use the name of the server service here if you're also running it
   as a Swarm service (eg. using `restic-docker-swarm:server`).
2. You normally don't need to change the backup path.
3. The remote path can also be relative. In that case it's relative to the
   default login path on the SSH server.
4. The service name must be complete, ie. remember to include the stack name
   if you start your services using a Swarm stack.
5. The `*_HOOK` commands are only run in one of the service's containers
   even if there are multiple replicas. Leave these empty if not needed.
6. The `*_FILE` variables are paths to the respective files inside the container.
   You can use these to configure eg. paths to secrets but usually the defaults
   should work fine.
7. Take a look into the source repository for more information. For example, you
   can pass `--verbose` in `EXTRA_ARGS` for more verbose logs but usually this
   variable is not needed.

You should mount the volume you want to backup at `BACKUP_PATH`.

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

The `restic-docker-swarm:server` image can be configured with the following
environment variables.

| Variable                  | Default                             | Description                                                  |
|---------------------------|-------------------------------------|--------------------------------------------------------------|
| SSHD_PORT                 | 2222                                | SSH port used by sshd.                                       |
| SWARM_SERVICE             |                                     | A name that resolves to the **server** service.              |

You should mount a volume at `/home/restic` for preserving your restic repositories
across container reboots.

## Agent CLI usage

The `restic-docker-swarm:agent` image includes the restic binary which you can
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

The `restic-docker-swarm:server` image includes the restic binary which you can
use to manage your restic repositories, manually take backups, restore backups etc.
Restic repositories are stored at `/home/restic` by default.

You can access the container by running

```
docker exec -it CONTAINER_ID sh
```

The server container shell also prints some convenient information and statistics
on login.

## Pre- and post-backup hooks

The agent container can run hook commands before and after backups. Hook
commands are only run in a single container of the target service even if the
service has multiple replicas.

The commands to run are set using the `PRE_HOOK` and `POST_HOOK` environment
variables. The `SERVICE_NAME` variable should contain the name of the Swarm
service from which the backup is taken. Remember to use the full name of
the service, ie. also include the stack name prefix if applicable.

Hooks are useful for example when backing up a database. You can dump the
database to a file in a pre-backup hook and delete the database dump in a
post-backup hook. The example stack in `test/stack.yml` uses hooks to backup
a Postgres database in this manner.

## Container healthcheck

TODO

## License

This project is license under the BSD 3-clause license. See the whole
license text in `LICENSE.md` in the root of this repository.
