from django.db import models

class ResticConfig(models.Model):
    pass

class ResticRepository(models.Model):
    password = models.CharField(max_length=256)

class ResticBackend(models.Model):
    restic = models.ForeignKey(
        ResticConfig,
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True

class SFTPBackend(ResticBackend):

    ssh_host = models.URLField()

    ssh_port = models.IntegerField()

    ssh_private_key = models.TextField()
