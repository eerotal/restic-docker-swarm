import docker

from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import Http404

from .models import *


class ClusterView(TemplateView):
    template_name = "cluster.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            "nodes": ClusterNode.objects.all(),
            "services": DockerService.objects.all(),
            "containers": DockerService.objects.all()
        })

        return context

class ServiceView(TemplateView):
    template_name = "service.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the Docker Service associated with the ID.
        try:
            service = DockerService.objects.get(
                identifier=self.kwargs['service_id']
            )
        except DockerService.DoesNotExist:
            raise Http404

        context.update({
            "service": service,
            "containers": service.dockercontainer_set
        })

        return context
