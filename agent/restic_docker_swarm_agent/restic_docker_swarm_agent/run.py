#!/usr/bin/env python3

"""A wrapper script for running restic with a set of default arguments.

This script runs the 'restic' binary, passing it a set of configuration
options based on various environment variables. This makes it easy to
run restic without specifying a lot of custom repository and SSH related
configuration options manually.

The environment variables used by this script are:

  SSH_HOST = The remote SSH host.
  SSH_PORT = SSH host port number.
  SSH_ID_FILE = SSH private key file for authenticating to the SSH host.
  SSH_KNOWN_HOSTS_FILE = Populated known_hosts file for identifying SSH hosts.
  RESTIC_REPO_PASSWORD_FILE = Restic repository password file.

"""

import os
import subprocess
from typing import List
from argparse import ArgumentParser

from restic_docker_swarm_agent._internal.resticutils import ResticUtils


def get_restic_cmd(repo: str) -> str:
    """Get the default restic command as a list of strings.

    :param str repo: The repository path to use.

    :return: The default restic command.
    :rtype: List[str]
    """

    host = os.environ["SSH_HOST"]
    port = os.environ["SSH_PORT"]
    id_file = os.environ["SSH_ID_FILE"]
    known_hosts_file = os.environ["SSH_KNOWN_HOSTS_FILE"]

    ssh_opts = [
        "-o", "UserKnownHostsFile={}".format(known_hosts_file),
        "-i", id_file
    ]

    restic_args = [
        "--password-file", os.environ["RESTIC_REPO_PASSWORD_FILE"]
    ]

    return ResticUtils.restic_cmd(
        host,
        port,
        repo,
        ssh_opts,
        restic_args
    )


def run_restic(repo: str, argv: List[str]) -> int:
    """Run restic with a set of arguments.

    :param str repo: The repository to use.
    :param List[str] argv: Arguments to restic.

    :return: The exit code returned by restic.
    :rtype: int
    """

    cmd = get_restic_cmd(repo)
    cmd.extend(argv)

    print("subprocess: " + " ".join(cmd))
    return subprocess.run(
        " ".join(cmd),
        check=False,
        shell=True
    ).returncode


def entrypoint():
    """Entrypoint method."""

    ap = ArgumentParser(description=__doc__)

    ap.add_argument(
        "-r",
        "--repo",
        type=str,
        required=True,
        help="The repository path passed to restic."
    )
    ap.add_argument(
        "args",
        type=str,
        nargs="*",
        help="Arguments passed to restic."
    )
    args = ap.parse_args()

    run_restic(args.repo, args.args)


if __name__ == "__main__":
    entrypoint()
