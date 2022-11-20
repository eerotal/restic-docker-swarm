from typing import Optional

from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from cluster.models import DockerService


class ResticBackend(models.Model):
    PROTOCOL_SFTP = 'SFTP'
    PROTOCOL_REST = 'REST'
    PROTOCOL_AMAZON_S3 = 'AMAZON_S3'
    PROTOCOL_MINIO = 'MINIO'
    PROTOCOL_WASABI = 'WASABI'
    PROTOCOL_ALIBABA_OSS = 'ALIBABA_OSS'
    PROTOCOL_OPENSTACK_SWIFT = 'OPENSTACK_SWIFT'
    PROTOCOL_BACKBLAZE_B2 = 'BACKBLAZE_B2'
    PROTOCOL_AZURE_BLOB = 'AZURE_BLOB'
    PROTOCOL_GOOGLE_CLOUD = 'GOOGLE_CLOUD'
    PROTOCOL_RCLONE = 'RCLONE'

    PROTOCOL_CHOICES = [
        (PROTOCOL_SFTP, 'Secure File Transfer Protocol (SFTP)')
    ]

    name = models.CharField(max_length=256, blank=False)
    protocol = models.CharField(max_length=50, choices=PROTOCOL_CHOICES, blank=False)

    @property
    def attrs_class(self) -> str:
        if self.protocol == self.PROTOCOL_SFTP:
            return "SFTPAttributeSet"
        else:
            return None

    def __str__(self):
        return self.name


class SFTPAttributeSet(models.Model):
    username = models.CharField(max_length=1024, blank=False)
    hostname = models.CharField(max_length=1024, blank=False)
    port = models.PositiveIntegerField(default=22, null=False, blank=False)
    backend = models.OneToOneField(
        ResticBackend,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="protocol_attrs"
    )

    @property
    def form_class(self) -> str:
        return "SFTPAttributeSetForm"


class BackupConfig(models.Model):
    service = models.OneToOneField(DockerService, on_delete=models.CASCADE, blank=False, null=False)
    schedule = models.CharField(max_length=50, blank=False, default="0 0 * * *")
    pre_hook = models.CharField(max_length=1024, blank=True)
    post_hook = models.CharField(max_length=1024, blank=True)


class ResticRepository(models.Model):
    name = models.CharField(max_length=100, blank=False, unique=True)
    location = models.CharField(max_length=1024, blank=False)
    resticbackend = models.ForeignKey(ResticBackend, on_delete=models.CASCADE, blank=False, null=False)
    backupconfig = models.ForeignKey(BackupConfig, on_delete=models.SET_NULL, blank=False, null=True)
