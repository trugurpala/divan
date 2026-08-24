from __future__ import annotations

import uuid

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from pusula.auth.request_context import (
    AuthConfigurationError,
    TenantAccessError,
    TokenVerificationError,
    authorize_request,
)
from pusula.domain.authorization import Action


def _error(code: str, message: str, *, status: int) -> JsonResponse:
    return JsonResponse({"ok": False, "error": {"code": code, "message": message}}, status=status)


@require_GET
def team_me(request: HttpRequest, team_id: uuid.UUID) -> JsonResponse:
    try:
        actor = authorize_request(
            request,
            team_id=team_id,
            action=Action.READ,
            required_scopes={"projects:read"},
        )
    except TokenVerificationError:
        return _error("unauthorized", "Oturum doğrulanamadı.", status=401)
    except TenantAccessError:
        return _error("forbidden", "Bu çalışma alanına erişim izniniz yok.", status=403)
    except AuthConfigurationError:
        return _error("identity_unavailable", "Kimlik servisi yapılandırılmamış.", status=503)

    return JsonResponse(
        {
            "ok": True,
            "data": {
                "subject": actor.subject,
                "team_id": str(actor.team_id),
                "role": actor.role.value,
            },
        }
    )
