"""Utility methods for controlling restic."""

from typing import List, Optional, Set

from docker.models.services import Service


class ResticUtils:
    """Utility methods for controlling restic."""

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
    def ssh_cmd(
        cls,
        host: str,
        port: str,
        opts: Optional[List[str]]
    ) -> List[str]:
        """Build an SSH command used by restic.

        :param str host: The SSH host.
        :param str port: The SSH port number.
        :param List[str] opts: A list of SSH options.

        :return: The SSH command as a list of strings.
        :rtype: List[str]
        """

        ssh_cmd = ["ssh", host]

        if opts is not None:
            ssh_cmd.extend(opts)

        if port is not None:
            ssh_cmd.extend(["-p", str(port)])

        ssh_cmd.extend(["-s", "sftp"])

        return ssh_cmd

    @classmethod
    def restic_cmd(
        cls,
        host: str,
        port: str,
        repo: str,
        ssh_opts: List[str],
        restic_args: List[str]
    ) -> List[str]:
        """Build a restic command.

        :param str host: The SSH host.
        :param str port: The SSH port number.
        :param str repo: The restic repository path.
        :param List[str] ssh_opts: A list of SSH options.
        :param List[str] restic_args: Arguments passed to restic.

        :return: A command template as a list of strings.
        :rtype: List[str]
        """

        ssh_cmd = " ".join(cls.ssh_cmd(host, port, ssh_opts))
        ret = [
            "restic",
            "-o", "sftp.command='{}'".format(ssh_cmd),
            "-r", cls.full_repo(host, repo)
        ]

        if restic_args is not None:
            ret.extend(restic_args)

        return ret

    @staticmethod
    def service_should_backup(s: Service) -> Optional[bool]:
        """Get the value of the rds.backup label for a Service."""
        return s.attrs.get("Spec").get("Labels").get("rds.backup") == "true"

    @staticmethod
    def service_cron_line(s: Service) -> Optional[str]:
        """Get the value of the rds.run-at label for a Service."""
        return s.attrs.get("Spec").get("Labels").get("rds.run-at")

    @staticmethod
    def service_repo_names(s: Service) -> Set[str]:
        """Get the values of the rds.repos label for a Service."""
        tmp = s.attrs.get("Spec").get("Labels").get("rds.repos")
        repos = set() if not tmp else {x.strip() for x in tmp.split(",")}
        return {x for x in repos if x}

    @staticmethod
    def service_pre_hook(s: Service) -> Optional[str]:
        """Get the value of the rds.pre-hook label for a Service."""
        return s.attrs.get("Spec").get("Labels").get("rds.pre-hook")

    @staticmethod
    def service_post_hook(s: Service) -> Optional[str]:
        """Get the value of the rds.post-hook label for a Service."""
        return s.attrs.get("Spec").get("Labels").get("rds.post-hook")