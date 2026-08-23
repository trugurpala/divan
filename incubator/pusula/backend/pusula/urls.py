from django.urls import path

from pusula.system_views import health, ready

urlpatterns = [
    path("health", health, name="health"),
    path("ready", ready, name="ready"),
]
