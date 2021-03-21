"""Main executable script for restic-docker-swarm."""

import os
import logging
import argparse
import shutil

import docker

from _internal.exceptions import MissingDependencyException
from _internal.resticwrapper import ResticWrapper
from _internal.backupscheduler import BackupScheduler

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s]: %(message)s",
)
logger = logging.getLogger()

def check_dependencies():
    """Make sure all required dependencies exist."""

    if shutil.which('restic') == None:
        raise MissingDependencyException(
            "'restic' binary is missing."
        )

    if not os.path.exists("/var/run/docker.sock"):
        raise MissingDependencyException(
            "Docker socket must exist at '/var/run/docker.sock'"
        )

if __name__ == "__main__":
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
        "backup_path",
        type=str,
        help="The directory to backup."
    )
    args = ap.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    docker_client = docker.from_env()

    rds = ResticWrapper(
        docker_client,
        args.ssh_host,
        args.backup_base,
        restic_args=args.restic_arg,
        ssh_opts=args.ssh_option,
        ssh_port=args.ssh_port
    )

    backupscheduler = BackupScheduler(
        docker_client,
        rds.backup
    )
    backupscheduler.run()
