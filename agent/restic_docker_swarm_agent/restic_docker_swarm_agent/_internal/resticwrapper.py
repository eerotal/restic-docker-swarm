"""A wrapper class for running restic."""

import os
import subprocess
import logging
from typing import List

from docker.models.services import Service
from docker.client import DockerClient

from restic_docker_swarm_agent._internal.exceptions import \
    SwarmException, ResticException
from restic_docker_swarm_agent._internal.resticutils import \
    ResticUtils

logger = logging.getLogger(__name__)


class ResticWrapper:
    """A wrapper class for running restic."""

    def __init__(
        self,
        docker_client: DockerClient,
        ssh_host: str,
        backup_base: str,
        forget_policy: str,
        restic_args: str=None,
        ssh_opts: str=None,
        ssh_port: int=None
    ):
        self.docker_client = docker_client

        self.ssh_host = ssh_host
        self.restic_args = restic_args
        self.ssh_opts = ssh_opts
        self.ssh_port = ssh_port

        self.backup_base = backup_base
        self.forget_policy = ResticUtils.parse_forget_policy(forget_policy)

    def get_restic_cmd(self, repo: str) -> List[str]:
        """Build a restic command.

        :param str repo: The repository to use in the command.
        """

        return ResticUtils.restic_cmd(
            self.ssh_host,
            self.ssh_port,
            repo,
            self.ssh_opts,
            self.restic_args
        )

    def run_in_service(self, service: Service, cmd: str):
        """Run a command in all tasks of a service.

        :param Service service: The Service to run the command in.
        :param str cmd: The command to run.

        :raises Exception: If 'docker exec' fails.
        :raises Exception: If the service has no running tasks.
        """

        logger.info("Running in service %s: %s", service.name, cmd)
        tasks = service.tasks(filters={"desired-state": "Running"})

        if len(tasks) > 1:
            logger.info(
                "Service %s has multiple tasks. Will only run "
                "the requested command in one of them.",
                service.name
            )
        elif len(tasks) == 0:
            raise SwarmException(
                "No running tasks in service {}. Unable to run command."
                .format(service.name)
            )

        cid = tasks[0].get("Status").get("ContainerStatus").get("ContainerID")
        container = self.docker_client.containers.get(cid)
        ret = container.exec_run(cmd)

        output = ret.output.decode("utf-8")
        if output != "" and not output.isspace():
            logger.info("Output from container:\n\n%s\n", output)

        if ret.exit_code != 0:
            raise SwarmException("Failed to execute command.")

    def run_restic(self, repo: str, output: bool, *args):
        """A thin wrapper for running restic commands.

        All varargs are passed to the restic command after
        the default arguments. The restic command is run using
        subprocess.run(). The return value of subprocess.run()
        is returned by this method.

        :param str repo: The repository to work on.
        :param bool output: Print output of subprocess. If the current
                            logging level is logging.DEBUG, this argument
                            is ignored and output is always printed.
        """
        output = output or logger.getEffectiveLevel() <= logging.DEBUG

        cmd = self.get_restic_cmd(repo)
        cmd.extend(args)

        if not output:
            return subprocess.run(
                " ".join(cmd),
                check=True,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        logger.info("Exec: %s", " ".join(cmd))
        return subprocess.run(
            " ".join(cmd),
            check=True,
            shell=True
        )

    def init_repo(self, repo: str):
        """Initialize a restic repository if it doesn't exist.

        :param str repo: The respository to initialize.

        :raises Exception: If initialization fails.
        """

        repo_full_path = ResticUtils.full_repo(self.ssh_host, repo)

        # Check whether the repo already exists.
        logger.debug("Checking whether the repo %s exists.", repo_full_path)
        try:
            self.run_restic(repo, False, "cat", "config")
            logger.debug("Restic repo already exists.")
            return
        except subprocess.CalledProcessError:
            logger.debug("Restic repo doesn't exist.")

        # Initilize the repo if it doesn't exist.
        logger.debug("Creating repo %s.", repo_full_path)
        try:
            self.run_restic(repo, True, "init")
        except subprocess.CalledProcessError as e:
            raise ResticException("'restic init' failed.") from e

    def forget(self, service: Service):
        """Forget old snapshots from service according to the forget policy.

        :param Service service: The service who's backups to forget.
        """
        repos = ResticUtils.service_backup_repos(service)

        for r in repos:
            logger.info(
                "Forgetting old backups of service %s from repo %s.",
                service.name,
                r
            )

            args = ResticUtils.forget_policy_as_args(self.forget_policy)

            # Forget old snapshots.
            try:
                self.run_restic(r, True, "forget", *args)
            except subprocess.CalledProcessError as e:
                logger.error("Restic returned error code: %s", e.returncode)

    def backup(self, service: Service):
        """Backup files with restic and run pre-hooks and post-hooks.

        :param Service service: The service to backup.
        """

        repos = ResticUtils.service_backup_repos(service)
        pre_hook = ResticUtils.service_backup_pre_hook(service)
        post_hook = ResticUtils.service_backup_post_hook(service)

        if len(repos) == 0:
            logger.error(
                "No repositories defined for service %s.",
                service.name
            )
            return

        # Run pre-backup hook.
        if pre_hook is not None:
            logger.info("Running pre-backup hook.")
            try:
                self.run_in_service(service, pre_hook)
            except SwarmException as e:
                logger.error(e)
                return

        for r in repos:
            if os.path.isabs(r):
                logger.error(
                    "Absolute repository path %s in service %s. Skipping!",
                    r,
                    service.name
                )
                continue

            # Initialize the repository.
            logger.info("Initializing repo %s.", r)
            try:
                self.init_repo(r)
            except ResticException as e:
                logger.error("Failed to init restic repo: %s", str(e))
                continue

            # Take backup.
            logger.info("Taking backup of %s.", r)
            try:
                self.run_restic(
                    r,
                    True,
                    "backup",
                    os.path.join(self.backup_base, r)
                )
            except subprocess.CalledProcessError as e:
                logger.error("Restic returned error code: %s", e.returncode)
                continue

            # Forget old snapshots.
            self.forget(service)

        # Run post-backup hook.
        if post_hook is not None:
            logger.info("Running post-backup hook.")
            try:
                self.run_in_service(service, post_hook)
            except SwarmException as e:
                logger.error(e)
