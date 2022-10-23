from django.urls import path

from .views import *

app_name = 'cluster'
urlpatterns = [
    path('', ClusterView.as_view(), name="cluster"),
    path('service/<str:service_id>', ServiceView.as_view(), name="service")
]
