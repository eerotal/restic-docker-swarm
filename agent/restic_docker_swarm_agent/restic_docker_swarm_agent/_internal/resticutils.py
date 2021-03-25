"""Utility methods for controlling restic."""

from typing import List, Optional, Set, Dict, Union

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
    def parse_forget_policy(spec: str) -> Dict[str, Union[str, int, set]]:
        """Parse a forget policy string.

        The expected format is

        HOURLY DAILY WEEKLY MONTHLY YEARLY WITHIN LAST PRUNE [TAG]

        where each word corresponds to an argument passed to 'restic forget'.
        PRUNE should be 'true' or 'false' depending on whether forgotten
        backups should be pruned automatically. [TAG] is optional and it can
        also be a comma separated list of multiple tags to keep.

        :param str spec: The policy string to parse.

        :return: The policy as a dictionary.
        :rtype: Dict[str, Union[str, int, set]]
        """

        parts = [x.strip() for x in spec.split(" ")]
        parts = [x for x in parts if x]

        # Make sure the policy format is valid.
        if len(parts) < 8 or len(parts) > 9:
            raise ValueError(
                "Invalid backup forget policy. Expected: "
                "'H D W M Y WITHIN LAST PRUNE [TAG]'."
            )

        # Destructure the keep-* values into variables.
        h, d, w, m, y, within, last, prune = parts

        # Parse tags from a comma-separated list.
        tags = set()
        if len(parts) == 9:
            tags = {x.strip() for x in parts[8].split(",")}
            tags = {x for x in tags if x}

        return {
            "keep-hourly": int(h),
            "keep-daily": int(d),
            "keep-weekly": int(w),
            "keep-monthly": int(m),
            "keep-yearly": int(y),
            "keep-within": within,
            "keep-last": int(last),
            "prune": prune == "true",
            "keep-tag": tags
        }

    @staticmethod
    def forget_policy_as_args(
        policy: Dict[str, Union[str, int, set]]
    ) -> List[str]:
        """Build restic arguments from the forget policy.

        :param Dict[str, Union[str, int, set]] policy: The policy as returned
            by ResticUtils.parse_forget_policy().

        :return: A list of command line arguments.
        :rtype: List[str]
        """

        args = []
        for key in policy:
            if isinstance(policy[key], set):
                # If the key contains a set, add multiple similar args.
                for item in policy[key]:
                    args.append("--{}={}".format(key, item))
            else:
                # If not, add the key as an argument directly.
                if isinstance(policy[key], bool):
                    args.append("--{}".format(key))
                else:
                    args.append(
                        "--{}={}".format(
                            key,
                            str(policy[key])
                        )
                    )

        return args

    @staticmethod
    def service_backup(s: Service) -> bool:
        """Get the value of the rds.backup label for a Service."""
        return s.attrs.get("Spec").get("Labels").get("rds.backup") == "true"

    @staticmethod
    def service_backup_at(s: Service) -> Optional[str]:
        """Get the value of the rds.backup.at label for a Service."""
        return s.attrs.get("Spec").get("Labels").get("rds.backup.at")

    @staticmethod
    def service_backup_repos(s: Service) -> Set[str]:
        """Get the values of the rds.backup.repos label for a Service."""
        tmp = s.attrs.get("Spec").get("Labels").get("rds.backup.repos")
        repos = set() if not tmp else {x.strip() for x in tmp.split(",")}
        return {x for x in repos if x}

    @staticmethod
    def service_backup_pre_hook(s: Service) -> Optional[str]:
        """Get the value of the rds.backup.pre-hook label for a Service."""
        return s.attrs.get("Spec").get("Labels").get("rds.backup.pre-hook")

    @staticmethod
    def service_backup_post_hook(s: Service) -> Optional[str]:
        """Get the value of the rds.backup.post-hook label for a Service."""
        return s.attrs.get("Spec").get("Labels").get("rds.backup.post-hook")
