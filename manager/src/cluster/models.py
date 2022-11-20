from django.db import models
from django.db.models import Q

class ClusterNode(models.Model):
    """Class representing a node in the Swarm cluster."""

    STATUS_DOWN = 'DOWN'
    STATUS_READY = 'READY'

    STATUS_CHOICES = [
        (STATUS_DOWN, 'Down'),
        (STATUS_READY, 'Ready')
    ]

    AGENT_STATUS_NOT_RUNNING = 'NOT_RUNNING'
    AGENT_STATUS_RUNNING = 'RUNNING'

    AGENT_STATUS_CHOICES = [
        (AGENT_STATUS_NOT_RUNNING, 'Not running'),
        (AGENT_STATUS_RUNNING, 'Running')
    ]

    # Docker data
    identifier = models.TextField(unique=True, blank=False)
    hostname = models.TextField(blank=False)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, blank=False)

    # RDS data
    agent_status = models.CharField(max_length=50, choices=AGENT_STATUS_CHOICES, blank=False)

    class Meta:
        constraints = [
            models.CheckConstraint(check=~Q(identifier=""), name="clusternode_non_empty_identifier"),
            models.CheckConstraint(check=~Q(hostname=""), name="clusternode_non_empty_hostname"),
            models.CheckConstraint(check=~Q(status=""), name="clusternode_non_empty_status"),
            models.CheckConstraint(check=~Q(agent_status=""), name="clusternode_non_empty_agent_status")
        ]

    @property
    def is_ready(self) -> bool:
        """Check whether the node status is ready.

        :return: True if the node status is ready, False otherwise.
        """

        return self.status == self.STATUS_READY


class DockerService(models.Model):
    """Class representing a service in the Swarm cluster."""

    BACKUP_STATUS_DISABLED = 'DISABLED'
    BACKUP_STATUS_PENDING = 'PENDING'
    BACKUP_STATUS_ACTIVE = 'ACTIVE'
    BACKUP_STATUS_FAILING = 'FAILING'

    BACKUP_STATUS_CHOICES = [
        (BACKUP_STATUS_DISABLED, 'Disabled'),
        (BACKUP_STATUS_PENDING, 'Pending'),
        (BACKUP_STATUS_ACTIVE, 'Active'),
        (BACKUP_STATUS_FAILING, 'Failing')
    ]

    TASK_STATUS_RUNNING = 'RUNNING'
    TASK_STATUS_PARTIAL = 'PARTIAL'
    TASK_STATUS_FAILING = 'FAILING'

    TASK_STATUS_DISPLAY = [
        (TASK_STATUS_RUNNING, 'Running'),
        (TASK_STATUS_PARTIAL, 'Partial'),
        (TASK_STATUS_FAILING, 'Failing')
    ]

    # Docker data
    identifier = models.TextField(unique=True, blank=False)
    name = models.TextField(blank=False)

    # RDS data
    backup_status = models.CharField(
        max_length=50,
        choices=BACKUP_STATUS_CHOICES,
        default=BACKUP_STATUS_DISABLED,
        blank=False
    )

    class Meta:
        constraints = [
            models.CheckConstraint(check=~Q(identifier=""), name="dockerservice_non_empty_identifier"),
            models.CheckConstraint(check=~Q(name=""), name="dockerservice_non_empty_name")
        ]

    @property
    def is_backup_disabled(self) -> bool:
        """Check whether backups are disabled for this service.

        :return: True if backups are disabled, False otherwise.
        """

        return self.backup_status == self.BACKUP_STATUS_DISABLED

    @property
    def is_backup_active(self) -> bool:
        """Check whether backups are active for this service.

        :return: True if backups are active, False otherwise.
        """
        return self.backup_status == self.BACKUP_STATUS_ACTIVE

    @property
    def is_backup_failing(self) -> bool:
        """Check whether backups are failing for this service.

        :return: True if backups are failing, False otherwise.
        """
        return self.backup_status == self.BACKUP_STATUS_FAILING

    @property
    def task_status(self) -> str:
        """Get a summarized status of all tasks in this service.

        :return: One of the DockerService.TASK_STATUS_* constants.
        """

        # Check running tasks.
        total_tasks = self.dockercontainer_set.all().count()
        running_tasks = list(map(
            lambda x: x.is_running,
            self.dockercontainer_set.all()
        )).count(True)

        # Return the summarized task status.
        if total_tasks == 0 or running_tasks == 0:
            return self.TASK_STATUS_FAILING
        elif running_tasks == total_tasks:
            return self.TASK_STATUS_RUNNING
        elif running_tasks < total_tasks:
            return self.TASK_STATUS_PARTIAL

    @property
    def get_task_status_display(self) -> str:
        """Get the summarized task status display string.

        :return: A display string corresponding to self.task_status().
        """

        status = self.task_status
        for c in self.TASK_STATUS_DISPLAY:
            if c[0] == status:
                return c[1]


class DockerContainer(models.Model):
    """Class representing a container in the Swarm cluster."""

    STATUS_NEW = 'NEW'
    STATUS_PENDING = 'PENDING'
    STATUS_ASSIGNED = 'ASSIGNED'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_PREPARING = 'PREPARING'
    STATUS_STARTING = 'STARTING'
    STATUS_RUNNING = 'RUNNING'
    STATUS_COMPLETE = 'COMPLETE'
    STATUS_FAILED = 'FAILED'
    STATUS_SHUTDOWN = 'SHUTDOWN'
    STATUS_REJECTED = 'REJECTED'
    STATUS_ORPHANED = 'OPRHANED'
    STATUS_REMOVE = 'REMOVE'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_STARTING, 'Starting'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_COMPLETE, 'Complete'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_SHUTDOWN, 'Shutdown'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_ORPHANED, 'Orphaned'),
        (STATUS_REMOVE, 'Remove'),
    ]

    # Docker data
    identifier = models.TextField(unique=True, blank=False)
    name = models.TextField(blank=False)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, blank=False)
    node = models.ForeignKey(ClusterNode, on_delete=models.CASCADE, blank=False, null=False)
    service = models.ForeignKey(DockerService, on_delete=models.CASCADE, blank=False, null=False)

    class Meta:
        constraints = [
            models.CheckConstraint(check=~Q(identifier=""), name="dockercontainer_non_empty_identifier"),
            models.CheckConstraint(check=~Q(name=""), name="dockercontainer_non_empty_name"),
            models.CheckConstraint(check=~Q(status=""), name="dockercontainer_non_empty_status")
        ]

    @property
    def is_starting(self) -> bool:
        """Check whether the container is in the process of starting up.

        :return: True if the container is starting up, False otherwise.
        """

        return self.status in [
            self.STATUS_NEW,
            self.STATUS_PENDING,
            self.STATUS_ASSIGNED,
            self.STATUS_ACCEPTED,
            self.STATUS_PREPARING,
            self.STATUS_STARTING
        ]

    @property
    def is_running(self) -> bool:
        """Check whether the container is running.

        :return: True if the container is running, False otherwise.
        """

        return self.status in [
            self.STATUS_RUNNING
        ]

    @property
    def is_shutdown(self) -> bool:
        """Check whether the container has been shutdown cleanly.

        :return: True if the container has been shutdown, False otherwise.
        """

        return self.status in [
            self.STATUS_COMPLETE,
            self.STATUS_SHUTDOWN,
            self.STATUS_REMOVE
        ]

    @property
    def is_failed(self) -> bool:
        """Check whether the container has failed.

        :return: True if the container has failed, False otherwise.
        """

        return self.status in [
            self.STATUS_FAILED,
            self.STATUS_REJECTED,
            self.STATUS_ORPHANED,
            self.STATUS_REMOVE,
            self.STATUS_PREPARING,
            self.STATUS_STARTING
        ]
