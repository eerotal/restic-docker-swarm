from django.conf import settings
from django.core.management.base import BaseCommand

from typing import Union, List, Callable

from docker import DockerClient
from docker.models.nodes import Node
from docker.models.services import Service
from docker.models.containers import Container

from cluster.models import ClusterNode, DockerService, DockerContainer

class Command(BaseCommand):
    help = "Fetch cluster information from Docker."

    def __init__(
        self,
        cluster_node_cls: type=ClusterNode,
        docker_service_cls: type=DockerService,
        docker_container_cls: type=DockerContainer
    ):
        """Initialize the command.

        :param cluster_node_cls: The Django model to use for cluster nodes.
        :param docker_service_cls: The Django model to use for services.
        :param docker_container_cls: The Django model to use for containers.
        """

        self.cluster_node_cls = cluster_node_cls
        self.docker_service_cls = docker_service_cls
        self.docker_container_cls = docker_container_cls

    def store_generic(
        self,
        objects: Union[Node, Service, Container],
        model_cls: type,
        value_init: Callable[[
            Union[ClusterNode, DockerService, DockerContainer],
            Union[Node, Service, Container]
        ], None],
        value_set: Callable[[
            Union[ClusterNode, DockerService, DockerContainer],
            Union[Node, Service, Container]
        ], None],
    ) -> None:
        """ Generic function for storing objects of a certain type from the Docker daemon.

        Results are stored in the Django database as model_cls objects.

        :param objects: The Docker objects to store.
        :param model_cls: The Django model class to instantiate.
        :param value_init: A callable for initializing a model_cls instance from Docker data.
        :param value_set: A callable for updating a model_cls instance from Docker data.
        """

        # Create model_cls objects for new Docker objects and update existing.
        for src in objects:
            dest = None

            try:
                dest = model_cls.objects.get(identifier=src.id)
                value_set(dest, src)
                print("Update %s (%s)" % (dest.identifier, type(src).__name__))
            except model_cls.DoesNotExist:
                dest = model_cls()
                value_init(dest, src)
                print("Create %s (%s)" % (dest.identifier, type(src).__name__))

            dest.save()

        # Delete model_cls objects of Docker objects which don't exist anymore.
        for dest in model_cls.objects.all():
            found = False

            for src in objects:
                if dest.identifier == src.id:
                    found = True
                    break

            if not found:
                print("Delete %s (%s)" % (dest.identifier, type(src).__name__))
                dest.delete()

    def fetch_nodes(self, docker_client: DockerClient) -> None:
        """Fetch and store nodes from Docker.

        :param docker_client: The Docker client instance to use.
        """

        def value_init(dest: ClusterNode, src: Node) -> None:
            dest.identifier = src.id
            dest.hostname = src.attrs.get('Description').get('Hostname')

            # Assign node status.
            dest.status = None
            status = src.attrs.get('Status').get('State').upper()
            for choice in [ x[0] for x in self.cluster_node_cls.STATUS_CHOICES ]:
                if status == choice:
                    dest.status = choice
                    break

            if dest.status is None:
                raise Exception("Unknown node state received from Docker daemon: %s" % status)

            # Assign default agent status.
            dest.agent_status = self.cluster_node_cls.AGENT_STATUS_NOT_RUNNING

        def value_set(dest: ClusterNode, src: Node) -> None:
            dest.status = src.attrs.get('Status').get('State')

        self.store_generic(
            docker_client.nodes.list(),
            self.cluster_node_cls,
            value_init,
            value_set
        )

    def fetch_services(self, docker_client: DockerClient) -> None:
        """Fetch and store services from Docker.

        :param docker_client: The Docker client instance to use.
        """

        def value_init(dest: DockerService, src: Service) -> None:
            dest.identifier = src.id
            dest.name = src.name

        def value_set(dest: DockerService, src: Service) -> None:
            pass

        self.store_generic(
            docker_client.services.list(),
            self.docker_service_cls,
            value_init,
            value_set
        )

    def fetch_containers(self, docker_client: DockerClient) -> None:
        """Fetch and store containers from Docker.

        :param docker_client: The Docker client instance to use.
        """

        def value_init(dest: DockerContainer, src: Container) -> None:
            dest.identifier = src.id
            dest.name = src.name

            # Assign container status.
            dest.status = None
            status = src.attrs.get("State").get("Status").upper()
            for choice in [ x[0] for x in self.docker_container_cls.STATUS_CHOICES ]:
                if status == choice:
                    dest.status = choice
                    break

            if dest.status is None:
                raise Exception("Unknown container state received from Docker daemon: %s" % status)

            # Assign node cross reference.
            node_id = src.attrs.get("Config").get("Labels").get("com.docker.swarm.node.id")
            dest.node = self.cluster_node_cls.objects.get(identifier=node_id)

            # Assign service cross reference.
            service_id = src.attrs.get("Config").get("Labels").get("com.docker.swarm.service.id")
            dest.service = self.docker_service_cls.objects.get(identifier=service_id)

        def value_set(dest: DockerContainer, src: Container) -> None:
            pass

        self.store_generic(
            docker_client.containers.list(),
            self.docker_container_cls,
            value_init,
            value_set
        )

    def handle(self, *args, **options):
        self.fetch_nodes(settings.DOCKER)
        self.fetch_services(settings.DOCKER)
        self.fetch_containers(settings.DOCKER)
