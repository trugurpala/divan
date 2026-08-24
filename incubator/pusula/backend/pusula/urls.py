from django.urls import path

from pusula.api_views import team_me
from pusula.system_views import health, ready

urlpatterns = [
    path("health", health, name="health"),
    path("ready", ready, name="ready"),
    path("api/teams/<uuid:team_id>/me", team_me, name="team-me"),
]
