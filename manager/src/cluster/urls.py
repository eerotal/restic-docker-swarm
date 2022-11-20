from django.urls import path

from .views import *

app_name = 'cluster'
urlpatterns = [
    path('', ClusterView.as_view(), name='cluster'),
    path('service/<str:service_id>', ServiceView.as_view(), name='service'),
    path('service/<str:service_id>/config/create', BackupConfigCreateAction.as_view(), name='create_backup_config'),
    path('service/<str:service_id>/config/save', BackupConfigSaveAction.as_view(), name='save_backup_config'),
    path('service/<str:service_id>/config/delete', BackupConfigDeleteAction.as_view(), name='delete_backup_config'),
    path('service/<str:service_id>/repository/create', ResticRepositoryCreateAction.as_view(), name='create_restic_repository'),
    path('service/<str:service_id>/repository/<int:repo_pk>/save', ResticRepositorySaveAction.as_view(), name='save_restic_repository'),
    path('service/<str:service_id>/repository/<int:repo_pk>/delete', ResticRepositoryDeleteAction.as_view(), name='delete_restic_repository')
]
