"""A wrapper class for running restic."""

import subprocess
import re
import time
import datetime
import logging
from typing import List

import docker
from docker.models.services import Service

from .exceptions import *

logger = logging.getLogger(__file__)

class ResticWrapper:
    """Main restic wrapper class."""

    def __init__(
        self,
        ssh_host: str,
        repo_path: str,
        backup_path: str,
        restic_args: str=None,
        service_name: str=None,
        pre_hook: str=None,
        post_hook: str=None,
        run_at: str=None,
        ssh_opts: str=None,
        ssh_port: int=None
    ):
        self.docker_client = docker.from_env()

        self.ssh_host = ssh_host
        self.repo_path = repo_path
        self.backup_path = backup_path

        self.restic_args = restic_args
        self.service_name = service_name
        self.pre_hook = pre_hook
        self.post_hook = post_hook
        self.run_at = run_at
        self.ssh_opts = ssh_opts
        self.ssh_port = ssh_port

    def run(self):
        """Run the backup once or in a loop."""

        if not self.run_at:
            self.backup()
        else:
            last_run = ""
            while True:
                dt = datetime.datetime \
                             .now() \
                             .replace(second=0, microsecond=0) \
                             .isoformat()

                if dt != last_run and re.match(self.run_at, dt):
                    logger.info("Backup started.")

                    if self.backup():
                        logger.info("Backup finished.")
                    else:
                        logger.info("Backup failed.")

                    last_run = dt

                time.sleep(1)

    @property
    def service(self) -> Service:
        """Get the service to be backed up.

        :return: The service object.
        :rtype: Service
        """

        if self.service_name:
            for service in self.docker_client.services.list():
                if service.name == self.service_name:
                    logger.debug(
                        "Service name %s matches ID %s.",
                        self.service_name,
                        service.id
                    )
                    return service

        return None

    @property
    def full_repo(self) -> str:
        """Get the full repository address.

        :return: The full repository address string.
        :rtype: str
        """

        return "sftp:{}:{}".format(self.ssh_host, self.repo_path)

    @property
    def ssh_cmd(self):
        """Build the SSH command used by restic.

        :return: The SSH command as a list of strings.
        :rtype: List[str]
        """

        ssh_cmd = ["ssh", self.ssh_host]
        ssh_cmd.extend(self.ssh_opts)

        if self.ssh_port is not None:
            ssh_cmd.extend(["-p", str(self.ssh_port)])

        ssh_cmd.extend(["-s", "sftp"])

        return ssh_cmd

    @property
    def restic_default_cmd(self) -> List[str]:
        """Get the default restic command template.

        :return: A command template as a list of strings.
        :rtype: List[str]
        """

        ret = [
            "restic",
            "-o", "sftp.command='{}'".format(" ".join(self.ssh_cmd)),
            "-r", self.full_repo
        ]

        if self.restic_args is not None:
            ret.extend(self.restic_args)

        return ret

    def run_in_service(self, service: Service, cmd: str):
        """Run a command in all tasks of a service.

        :param Service service: The Service to run the command in.
        :param str cmd: The command to run.

        :raises Exception: If 'docker exec' fails.
        :raises Exception: If the service has no running tasks.
        """

        logger.info("Running in service %s: %s", service.id, cmd)
        tasks = service.tasks(filters={"desired-state": "Running"})

        if len(tasks) > 1:
            logger.info(
                ("Service %s has multiple tasks. Will only run "
                "the requested command in one of them."),
                service.id
            )
        elif len(tasks) == 0:
            raise Exception(
                "No running tasks in service {}. Unable to run command."
                .format(service.id)
            )

        cid = tasks[0].get("Status").get("ContainerStatus").get("ContainerID")
        container = self.docker_client.containers.get(cid)
        if container.exec_run(cmd)[0] != 0:
            raise Exception("Failed to execute command.")

    def run_restic(self, suppress_output, *args):
        """A thin wrapper for running restic commands.

        All varargs are passed to the restic command after
        the default arguments. The restic command is run using
        subprocess.run(). The return value of subprocess.run()
        is returned by this method.

        :param bool suppress_output: Redirect command output to /dev/null.
        """

        cmd = self.restic_default_cmd
        cmd.extend(args)
        logger.debug("Exec: %s", " ".join(cmd))

        sp_kwargs = {
            "stdout": subprocess.PIPE,
            "stdin": subprocess.PIPE,
            "stderr": subprocess.PIPE
        }

        if suppress_output:
            sp_kwargs["stdout"] = subprocess.DEVNULL
            sp_kwargs["stderr"] = subprocess.DEVNULL

        return subprocess.run(
            " ".join(cmd),
            check=True,
            shell=True,
            **sp_kwargs
        )

    def init_repo(self):
        """Initialize the restic repository if it doesn't exist.

        :raises Exception: If initialization fails.
        """

        # Check whether the repo already exists.
        logger.debug(
            "Checking whether the repository %s exists.",
            self.full_repo
        )
        try:
            self.run_restic(True, "cat", "config")
            logger.debug("Restic repo already exists.")
            return
        except subprocess.CalledProcessError:
            logger.debug("Restic repository doesn't exist.")

        # Initilize the repo if it doesn't exist.
        logger.debug("Creating repository %s.", self.full_repo)
        try:
            self.run_restic(False, "init")
        except subprocess.CalledProcessError as e:
            raise ResticException("'restic init' failed.") from e

    def backup(self):
        """Backup files with restic and run pre-hooks and post-hooks.

        :return: True on success, False on failure.
        :rtype: bool
        """

        ret = True

        try:
            self.init_repo()
        except ResticException:
            logger.error("Failed to init restic repo.")

        # Run pre-backup hook.
        if self.service and self.pre_hook:
            logger.info("Running pre-backup hook.")
            try:
                self.run_in_service(self.service, self.pre_hook)
            except Exception as e:
                logger.error(e)
                return False

        # Backup.
        try:
            self.run_restic(False, "backup", self.backup_path)
        except subprocess.CalledProcessError as e:
            logger.error("Restic returned error code: %s", e.returncode)
            ret = False

        # Run post-backup hook.
        if self.service and self.post_hook:
            logger.info("Running post-backup hook.")
            try:
                self.run_in_service(self.service, self.post_hook)
            except Exception as e:
                logger.error(e)
                return False

        return ret
