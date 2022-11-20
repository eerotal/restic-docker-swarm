import docker

from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView
from django.http import Http404
from django.urls import reverse
from django.forms.models import model_to_dict

from .models import *
from restic.models import BackupConfig

from .forms import BackupConfigForm, ResticRepositoryForm


###
# View endpoints
###

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

        # Create the BackupConfig form.
        backup_config = service.backupconfig if hasattr(service, "backupconfig") else None
        backup_config_form = BackupConfigForm(instance=backup_config)

        # Create forms for all existing repositories.
        repos = []
        if backup_config is not None:
            for repo in backup_config.resticrepository_set.all():
                repos.append(ResticRepositoryForm(instance=repo))

        # Create the "Add repository" form.
        repos.append(ResticRepositoryForm())

        context.update({
            "service": service,
            "backup_config": backup_config,
            "backup_config_form": backup_config_form,
            "repos": repos,
            "containers": service.dockercontainer_set
        })

        return context

###
# Form action endpoints
###

class BackupConfigCreateAction(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        # Get the Docker Service associated with the ID.
        try:
            service = DockerService.objects.get(
                identifier=self.kwargs['service_id']
            )
        except DockerService.DoesNotExist:
            raise Http404

        # Create the backup config instance.
        backup_config = BackupConfig()
        backup_config.service = service
        backup_config.save()

        # Update the backup status.
        service.backup_status = service.BACKUP_STATUS_PENDING
        service.save()

        # Redirect to the original service view.
        return redirect(
            reverse(
                "cluster:service",
                kwargs={'service_id': service.identifier}
            )
        )

class BackupConfigSaveAction(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        # Get the Docker Service associated with the ID.
        try:
            service = DockerService.objects.get(
                identifier=self.kwargs['service_id']
            )
        except DockerService.DoesNotExist:
            raise Http404

        # Make sure a backup configuration already exists.
        if not hasattr(service, "backupconfig"):
            raise Exception("Service has no backup configuration.")

        # Validate and save data.
        form = BackupConfigForm(request.POST, instance=service.backupconfig)

        if form.is_valid():
            form.save()

            # Update the backup status.
            service.backup_status = service.BACKUP_STATUS_PENDING
            service.save()

        # Redirect to the original service view.
        return redirect(
            reverse(
                "cluster:service",
                kwargs={'service_id': service.identifier}
            )
        )

class BackupConfigDeleteAction(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        # Get the Docker Service associated with the ID.
        try:
            service = DockerService.objects.get(
                identifier=self.kwargs['service_id']
            )
        except DockerService.DoesNotExist:
            raise Http404

        # Make sure a backup configuration already exists.
        if not hasattr(service, "backupconfig"):
            raise Exception("Service has no backup configuration.")

        # Delete the requested BackupConfig.
        service.backupconfig.delete()

        # Update the backup status.
        service.backup_status = service.BACKUP_STATUS_DISABLED
        service.save()

        # Redirect to the original service view.
        return redirect(
            reverse(
                "cluster:service",
                kwargs={'service_id': service.identifier}
            )
        )


class ResticRepositoryCreateAction(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        # Get the Docker Service associated with the ID.
        try:
            service = DockerService.objects.get(
                identifier=self.kwargs['service_id']
            )
        except DockerService.DoesNotExist:
            raise Http404

        # Make sure a backup configuration already exists.
        if not hasattr(service, "backupconfig"):
            raise Exception("Service has no backup configuration.")

        # Create the requested repository.
        form = ResticRepositoryForm(request.POST)
        if form.is_valid():
            repo = form.save(commit=False)
            repo.backupconfig = service.backupconfig
            repo.save()

        # Redirect to the original service view.
        return redirect(
            reverse(
                "cluster:service",
                kwargs={'service_id': service.identifier}
            )
        )


class ResticRepositorySaveAction(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        # Get the Docker Service associated with the ID.
        try:
            service = DockerService.objects.get(
                identifier=self.kwargs['service_id']
            )
        except DockerService.DoesNotExist:
            raise Http404

        # Make sure a backup configuration already exists.
        if not hasattr(service, "backupconfig"):
            raise Exception("Service has no backup configuration.")

        form = ResticRepositoryForm(request.POST)

        if form.is_valid():
            repo = form.save(commit=False)
            repo.backup_config = service.backupconfig
            repo.save()

        # Redirect to the original service view.
        return redirect(
            reverse(
                "cluster:service",
                kwargs={'service_id': service.identifier}
            )
        )


class ResticRepositoryDeleteAction(View):
    http_method_names = ["post"]
