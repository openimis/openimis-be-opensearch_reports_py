import logging

from core.jwt_authentication import JWTAuthentication
from django.http import HttpResponse
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny

from opensearch_reports.apps import DEFAULT_CONFIG, OpensearchReportsConfig

logger = logging.getLogger(__name__)


def _has_rights(user, rights):
    """Deny when nothing is configured: has_perms returns True for an empty list."""
    if not rights:
        return False
    return user.has_perms(rights)


def _module_rights():
    """Every right this module declares, as the cluster's mapping keys them.

    Read off the loaded config rather than the defaults, so a deployment that
    overrides a code keeps the forwarded identity and the check below in step.
    """
    return {
        int(right)
        for field in DEFAULT_CONFIG
        if field.endswith("_perms")
        for right in getattr(OpensearchReportsConfig, field) or []
    }


def _forwarded_rights(user):
    """The caller's rights among this module's, sorted, as strings.

    An administrator is given the full set rather than the intersection: the
    check below passes them on the superuser flag alone, and a technical
    account carries no rights of its own, so intersecting would send them on
    to Dashboards with an empty identity and nothing granted there. A
    technical account without that flag gets an empty header, correctly.
    """
    module_rights = _module_rights()
    if user.is_imis_admin:
        held = module_rights
    else:
        held = module_rights.intersection(user.rights)
    return [str(right) for right in sorted(held)]


@api_view(["GET", "HEAD"])
@authentication_classes([JWTAuthentication])
@permission_classes([AllowAny])
def opensearch_auth_check(request):
    """Authorize Dashboards access for the current user, for nginx auth_request.

    Runs once per Dashboards request, so it stays a database rights lookup with
    no outbound calls. Credentials arrive as the openIMIS JWT cookie.

    nginx consumes the status - 200 authorized, 403 authenticated but not
    allowed, 401 no usable credential, which it turns into a login redirect -
    and, on the 200 only, the identity headers it forwards to the cluster.
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

    response = HttpResponse(status=200)
    response["X-Auth-User"] = request.user.username
    response["X-Auth-Rights"] = ",".join(_forwarded_rights(request.user))
    return response
