from django.urls import path

from .views import *

app_name = 'restic'
urlpatterns = [
    path('', ResticView.as_view(), name='restic'),
    path('restic/backend/create', ResticBackendCreateAction.as_view(), name='create_restic_backend'),
    path('restic/backend/<int:backend_pk>/save', ResticBackendSaveAction.as_view(), name='save_restic_backend'),
    path('restic/backend/<int:backend_pk>/delete', ResticBackendDeleteAction.as_view(), name='delete_restic_backend'),
]
