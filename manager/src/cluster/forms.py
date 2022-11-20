from django import forms

from restic.models import BackupConfig, ResticRepository

class BackupConfigForm(forms.ModelForm):
    class Meta:
        model = BackupConfig
        fields = ['schedule', 'pre_hook', 'post_hook']

class ResticRepositoryForm(forms.ModelForm):
    class Meta:
        model = ResticRepository
        fields = ['name', 'location', 'resticbackend']
