"""Backup scheduler class."""

import logging
import time
import sched
from datetime import datetime
from typing import Callable

import pause
from croniter import croniter
from croniter import CroniterBadCronError
from docker.errors import NotFound
from docker.models.services import Service
from docker.client import DockerClient

from restic_docker_swarm_agent._internal.resticutils import ResticUtils

logger = logging.getLogger(__name__)


class BackupScheduler:
    """Backup scheduler class."""

    def __init__(
        self,
        docker_client: DockerClient,
        backup_func: Callable[[Service], None]
    ):
        """Initialize a BackupScheduler.

        :param DockerClient docker_client: The DockerClient to use.
        :param Callable[[Service], None] backup_func: The backup method to use.
            This should accept the Service to backup as the only argument.
        """

        self.docker_client = docker_client
        self.backup_func = backup_func

        self.backup_sched = sched.scheduler(time.time, pause.seconds)
        self.schedule_interval = 10
        self.schedule_priority = 5
        self.backup_priority = 10

    def backup_executor(self, service: Service) -> None:
        """Take a new backup of a service.

        :param Service service: The service to backup,
        """

        # Reload the service to make sure backup labels are up-to-date.
        tmp = None
        try:
            tmp = self.docker_client.services.get(service.id)
        except NotFound:
            logger.error("Service %s removed before backup.", service.name)
            return

        # Backup the service if it should still be backed up.
        if ResticUtils.service_backup(tmp):
            logger.info("Backing up %s", tmp.name)
            self.backup_func(tmp)

    def schedule_backups(self) -> None:
        """Schedule backups based on Service labels."""

        for s in self.docker_client.services.list():
            if not ResticUtils.service_backup(s):
                continue

            # Check whether a backup is already scheduled for the service.
            skip = False
            for ev in self.backup_sched.queue:
                if ev.kwargs["service"].id == s.id:
                    skip = True

            if skip:
                logger.debug("Backup already scheduled for %s.", s.name)
                continue

            # Schedule a new backup.
            run_at = ResticUtils.service_backup_at(s)
            if run_at is not None:
                try:
                    criter = croniter(run_at, datetime.now().astimezone())
                except CroniterBadCronError as e:
                    logger.error(e)
                    continue

                ts = criter.get_next(float)
                logger.info(
                    "Scheduling backup for service %s on %s.",
                    s.name,
                    datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                )
                self.backup_sched.enterabs(
                    ts,
                    self.backup_priority,
                    self.backup_executor,
                    [],
                    {"service": s}
                )
            else:
                logger.warning(
                    "Cron expression '%s' for service %s is invalid.",
                    run_at,
                    s.name
                )

        # Schedule new backups periodically.
        self.backup_sched.enter(
            self.schedule_interval,
            self.backup_priority,
            self.schedule_backups
        )

    def run(self):
        """Run the backup scheduler."""

        while True:
            # Run scheduler.
            logger.info("Starting BackupScheduler.")
            self.schedule_backups()
            self.backup_sched.run()
