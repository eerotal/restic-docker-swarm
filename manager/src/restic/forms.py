from django import forms

from .models import *


class ResticBackendForm(forms.ModelForm):
    class Meta:
        model = ResticBackend
        fields = ['name', 'protocol']


class SFTPAttributeSetForm(forms.ModelForm):
    class Meta:
        model = SFTPAttributeSet
        fields = ['username', 'hostname', 'port']
