from __future__ import annotations

from django.db import connection
from django.http import JsonResponse


def health(_request):
    return JsonResponse({"ok": True, "service": "pusula-control-api"})


def ready(_request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"ok": False, "ready": False}, status=503)
    return JsonResponse({"ok": True, "ready": True})
