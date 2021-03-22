#!/usr/bin/env python3

"""A wrapper script for running restic with a set of default arguments."""

import os
import sys
import subprocess
from typing import List

from restic_docker_swarm_agent._internal.resticutils import ResticUtils


def get_default_restic_cmd():
    """Get the default restic command as a list of strings.

    :return: The default restic command.
    :rtype: List[str]
    """

    host = os.environ["SSH_HOST"]
    port = os.environ["SSH_PORT"]
    repo = os.environ["REPO_PATH"]
    known_hosts_file = os.environ["SSH_KNOWN_HOSTS_FILE"]
    user = os.environ["USER"]

    ssh_opts = [
        "-o", "UserKnownHostsFile={}".format(known_hosts_file),
        "-i", "/home/{}/.ssh/id".format(user)
    ]

    restic_args = [
        "--password-file", os.environ["RESTIC_REPO_PASSWORD_FILE"]
    ]

    return ResticUtils.restic_default_cmd(
        host,
        port,
        repo,
        ssh_opts,
        restic_args
    )


def usage() -> int:
    """Print a help text.

    :return: The exit code returned by restic.
    :rtype: int
    """

    print("runrestic.py - Run restic with a set of default arguments.\n")
    print("The default restic command executed by this script is:")
    print("  " + " ".join(get_default_restic_cmd()) + "\n")
    print("This command is built from shell environment variables.")
    print("All arguments are appended to end of the default command.")

    return 0


def main(argv: List[str]) -> int:
    """Run restic with a set of arguments.

    :param List[str] argv: Additional arguments to restic.

    :return: The exit code returned by restic.
    :rtype: int
    """

    cmd = get_default_restic_cmd()
    cmd.extend(argv[1:])

    print(" # " + " ".join(cmd))
    return subprocess.run(
        " ".join(cmd),
        check=False,
        shell=True
    ).returncode


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.exit(usage())
    else:
        sys.exit(main(sys.argv))
