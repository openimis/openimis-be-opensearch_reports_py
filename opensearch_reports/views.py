import logging

from core.jwt_authentication import JWTAuthentication
from django.http import HttpResponse
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny

from opensearch_reports.apps import OpensearchReportsConfig

logger = logging.getLogger(__name__)


def _has_rights(user, rights):
    """Deny when nothing is configured: has_perms returns True for an empty list."""
    if not rights:
        return False
    return user.has_perms(rights)


@api_view(["GET", "HEAD"])
@authentication_classes([JWTAuthentication])
@permission_classes([AllowAny])
def opensearch_auth_check(request):
    """Authorize Dashboards access for the current user, for nginx auth_request.

    Runs once per Dashboards request, so it stays a database rights lookup with
    no outbound calls. Credentials arrive as the openIMIS JWT cookie.

    Only the status is consumed: 200 authorized, 403 authenticated but not
    allowed, 401 no usable credential - which nginx turns into a login redirect.
    Authentication is checked here rather than through IsAuthenticated so that
    every unauthenticated path answers 401, a valid cookie for a removed user
    included.
    """
    if not request.user or not request.user.is_authenticated:
        return HttpResponse(status=401)

    rights = OpensearchReportsConfig.gql_opensearch_dashboard_search_perms
    if not _has_rights(request.user, rights):
        logger.debug(
            "Dashboards access denied for %s: missing right(s) %s",
            request.user.username,
            rights,
        )
        return HttpResponse(status=403)

    return HttpResponse(status=200)
