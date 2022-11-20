from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View, TemplateView

from .models import *
from .forms import *


###
# View endpoints
###

class ResticView(TemplateView):
    template_name = "restic.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        backends = [(
            ResticBackendForm(instance=x),
            globals()[x.protocol_attrs.form_class](instance=x.protocol_attrs)
        ) for x in ResticBackend.objects.all()]

        backends.append((ResticBackendForm(), None))

        context.update({
            "backends": backends
        })

        return context

###
# Form action endpoints
###

class ResticBackendCreateAction(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        form = ResticBackendForm(request.POST)

        if form.is_valid():
            backend = form.save()

            attrs = globals()[backend.attrs_class]()
            attrs.backend = backend
            attrs.save()

        return redirect(
            reverse("restic:restic")
        )

class ResticBackendSaveAction(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        # Get the requested ResticBackend instance.
        try:
            backend = ResticBackend.objects.get(
                pk=self.kwargs['backend_pk']
            )
        except ResticBackend.DoesNotExist:
            raise Http404

        backend_form = ResticBackendForm(request.POST, instance=backend)
        attrs_form = globals()[backend.protocol_attrs.form_class](request.POST, instance=backend.protocol_attrs)

        if backend_form.is_valid() and attrs_form.is_valid():
            backend_form.save()
            attrs_form.save()

        return redirect(
            reverse("restic:restic")
        )

class ResticBackendDeleteAction(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        # Get the requested ResticBackend instance.
        try:
            backend = ResticBackend.objects.get(
                pk=self.kwargs['backend_pk']
            )
        except ResticBackend.DoesNotExist:
            raise Http404

        backend.delete()

        return redirect(
            reverse("restic:restic")
        )
