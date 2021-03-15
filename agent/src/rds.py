"""Main executable script for restic-docker-swarm."""

import logging
import argparse

from _internal.resticwrapper import ResticWrapper

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s]: %(message)s"
)
logger = logging.getLogger(__package__)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="restic-docker-swarm")

    ap.add_argument(
        "-s",
        "--ssh-host",
        type=str,
        required=True,
        help="The restic SSH host to "
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
        "-r",
        "--repo-path",
        type=str,
        required=True,
        help="The restic repository path on the SSH host."
    )
    ap.add_argument(
        "-n",
        "--service-name",
        type=str,
        default=None,
        help="The name of the Docker Swarm Service to run hooks in."
    )
    ap.add_argument(
        "-a",
        "--pre-hook",
        type=str,
        default=None,
        help="The pre-backup hook to run."
    )
    ap.add_argument(
        "-b",
        "--post-hook",
        type=str,
        default=None,
        help="The post-backup hook to run."
    )
    ap.add_argument(
        "-t",
        "--run-at",
        type=str,
        default=None,
        help="A regex that matches an ISO datetime when backups are taken."
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

    rds = ResticWrapper(
        args.ssh_host,
        args.repo_path,
        args.backup_path,
        restic_args=args.restic_arg,
        service_name=args.service_name,
        pre_hook=args.pre_hook,
        post_hook=args.post_hook,
        run_at=args.run_at,
        ssh_opts=args.ssh_option,
        ssh_port=args.ssh_port
    )
    rds.run()
