"""A wrapper class for running restic."""

import os
import subprocess
import re
import time
import sched
from datetime import datetime
import logging
from typing import List

import docker
from docker.models.services import Service
from docker.errors import NotFound

from croniter import croniter
from croniter import CroniterBadCronError
import pause

from _internal.exceptions import *
from _internal.resticutils import ResticUtils

logger = logging.getLogger(__name__)

class ResticWrapper:
    """Main restic wrapper class."""

    def __init__(
        self,
        ssh_host: str,
        backup_base: str,
        restic_args: str=None,
        ssh_opts: str=None,
        ssh_port: int=None,
    ):
        self.docker_client = docker.from_env()

        self.ssh_host = ssh_host
        self.restic_args = restic_args
        self.ssh_opts = ssh_opts
        self.ssh_port = ssh_port
        self.backup_base = backup_base

        self.schedule_interval = 10
        self.schedule_priority = 5
        self.backup_priority = 10

    def run(self):
        """Run the backup daemon."""

        backup_sched = sched.scheduler(time.time, pause.seconds)

        def backup_executor(service: Service):
            # Reload the service to make sure backup config is up-to-date.
            tmp = None
            try:
                tmp = self.docker_client.services.get(service.id)
            except NotFound:
                logger.error("Service %s removed before backup.", service.id)
                return

            # Backup the service if it should still be backed up.
            if ResticUtils.service_should_backup(tmp):
                logger.info("Backing up %s", tmp.id)
                self.backup(tmp)

        def schedule_backups():
            for s in self.docker_client.services.list():
                if not ResticUtils.service_should_backup(s):
                    continue

                # Check a backup is already scheduled for the service.
                skip = False
                for ev in backup_sched.queue:
                    if ev.kwargs["service"].id == s.id:
                        skip = True

                if skip:
                    logger.debug("Backup already scheduled for %s.", s.id)
                    continue

                # Schedule a new backup.
                run_at = ResticUtils.service_cron_line(s)
                if run_at is not None:
                    try:
                        criter = croniter(run_at, datetime.now())
                    except CroniterBadCronError as e:
                        logger.error(e)
                        continue

                    ts = criter.get_next(float)
                    logger.info(
                        "Scheduling backup for service %s on %s.",
                        s.id,
                        datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                    )
                    backup_sched.enterabs(
                        ts,
                        self.backup_priority,
                        backup_executor,
                        [],
                        {"service": s}
                    )

            print(backup_sched.queue)
            # Schedule new backups periodically.
            backup_sched.enter(
                self.schedule_interval,
                self.backup_priority,
                schedule_backups
            )

        while True:
            # Run scheduler.
            logger.info("Starting scheduler.")
            schedule_backups()
            backup_sched.run()

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

        logger.info("Running in service %s: %s", service.id, cmd)
        tasks = service.tasks(filters={"desired-state": "Running"})

        if len(tasks) > 1:
            logger.info(
                ("Service %s has multiple tasks. Will only run "
                "the requested command in one of them."),
                service.id
            )
        elif len(tasks) == 0:
            raise SwarmException(
                "No running tasks in service {}. Unable to run command."
                .format(service.id)
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
        else:
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

    def backup(self, service: Service):
        """Backup files with restic and run pre-hooks and post-hooks.

        :param Service service: The service to backup.
        """

        repo = ResticUtils.service_repo_name()
        pre_hook = ResticUtils.service_pre_hook()
        post_hook = ResticUtils.service_post_hook()

        # Initialize the repository.
        try:
            self.init_repo(repo)
        except ResticException as e:
            logger.error("Failed to init restic repo: {}".format(e))

        # Run pre-backup hook.
        if pre_hook is not None:
            logger.info("Running pre-backup hook.")
            try:
                self.run_in_service(service, pre_hook)
            except SwarmException as e:
                logger.error(e)

        # Backup.
        try:
            self.run_restic(
                repo,
                True,
                "backup",
                os.path.join(self.backup_base, repo)
            )
        except subprocess.CalledProcessError as e:
            logger.error("Restic returned error code: %s", e.returncode)

        # Run post-backup hook.
        if post_hook is not None:
            logger.info("Running post-backup hook.")
            try:
                self.run_in_service(service, post_hook)
            except SwarmException as e:
                logger.error(e)
