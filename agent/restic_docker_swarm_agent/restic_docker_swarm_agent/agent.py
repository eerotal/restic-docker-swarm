"""Main executable script for restic-docker-swarm."""

import os
import logging
import argparse
import shutil

import docker

from restic_docker_swarm_agent._internal.exceptions import \
    MissingDependencyException
from restic_docker_swarm_agent._internal.resticwrapper import \
    ResticWrapper
from restic_docker_swarm_agent._internal.backupscheduler import \
    BackupScheduler

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s]: %(message)s",
)
logger = logging.getLogger()


def check_dependencies():
    """Make sure all required dependencies exist."""

    if shutil.which('restic') is None:
        raise MissingDependencyException(
            "'restic' binary is missing."
        )

    if not os.path.exists("/var/run/docker.sock"):
        raise MissingDependencyException(
            "Docker socket must exist at '/var/run/docker.sock'"
        )


def entrypoint():
    """Entrypoint method."""

    check_dependencies()

    ap = argparse.ArgumentParser(description="restic-docker-swarm")

    ap.add_argument(
        "-s",
        "--ssh-host",
        type=str,
        required=True,
        help="The restic SSH host to "
    )
    ap.add_argument(
        "-b",
        "--backup-base",
        type=str,
        required=True,
        help="The backup base path where backups are taken from."
    )
    ap.add_argument(
        "-f",
        "--forget-policy",
        type=str,
        required=True,
        help="Set the backup forget policy."
    )
    ap.add_argument(
        "-p",
        "--ssh-port",
        type=int,
        default=None,
        help="The TCP port number of the SSH server."
    )
    ap.add_argument(
        "-o",
        "--ssh-option",
        action="append",
        help="Additional options passed to ssh."
    )
    ap.add_argument(
        "-v",
        "--verbose",
        action='store_true',
        help="Print verbose output."
    )
    ap.add_argument(
        "-e",
        "--restic-arg",
        type=str,
        action="append",
        help="Pass an argument to restic."
    )
    ap.add_argument(
        "-l",
        "--listen",
        type=str,
        required=True,
        help="Address and port of the status query server."
    )
    ap.add_argument(
        "backup_path",
        type=str,
        help="The directory to backup."
    )
    args = ap.parse_args()

    # Enable more verbose logs if --verbose was used.
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Parse the value of the --listen flag.
    query_server = args.listen.split(":")

    if len(query_server) > 2:
        raise ValueError("Invalid value for --listen: {}".format(args.listen))

    try:
        query_server = (query_server[0], int(query_server[1]))
    except ValueError as e:
        raise ValueError(
            "Invalid port for --listen: {}".format(query_server[1])
        ) from e

    docker_client = docker.from_env()

    rds = ResticWrapper(
        docker_client,
        args.ssh_host,
        args.backup_base,
        args.forget_policy,
        restic_args=args.restic_arg,
        ssh_opts=args.ssh_option,
        ssh_port=args.ssh_port
    )

    backupscheduler = BackupScheduler(
        docker_client,
        rds.backup,
        query_server
    )
    backupscheduler.run()


if __name__ == "__main__":
    entrypoint()
