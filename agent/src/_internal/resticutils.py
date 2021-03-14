"""Utility methods for controlling restic."""

from typing import List

class ResticUtils:
    @classmethod
    def full_repo(cls, host: str, repo: str) -> str:
        """Get the full address of a restic repository.

        :param str host: The SSH host.
        :param str repo: The restic repository path.

        :return: The full repository address string.
        :rtype: str
        """

        return "sftp:{}:{}".format(host, repo)

    @classmethod
    def ssh_cmd(cls, host: str, port: str, opts: List[str]) -> List[str]:
        """Build an SSH command used by restic.

        :param str host: The SSH host.
        :param str port: The SSH port number.
        :param List[str] opts: A list of SSH options.

        :return: The SSH command as a list of strings.
        :rtype: List[str]
        """

        ssh_cmd = ["ssh", host]
        ssh_cmd.extend(opts)

        if port is not None:
            ssh_cmd.extend(["-p", str(port)])

        ssh_cmd.extend(["-s", "sftp"])

        return ssh_cmd

    @classmethod
    def restic_default_cmd(
        cls,
        host: str,
        port: str,
        repo: str,
        ssh_opts: List[str],
        restic_args: List[str]
    ) -> List[str]:
        """Get the default restic command.

        :param str host: The SSH host.
        :param str port: The SSH port number.
        :param str repo: The restic repository path.
        :param List[str] ssh_opts: A list of SSH options.
        :param List[str] restic_args: Arguments passed to restic.

        :return: A command template as a list of strings.
        :rtype: List[str]
        """

        ret = [
            "restic",
            "-o", "sftp.command='{}'".format(" ".join(cls.ssh_cmd(host, port, ssh_opts))),
            "-r", cls.full_repo(host, repo)
        ]

        if restic_args is not None:
            ret.extend(restic_args)

        return ret