from django.db import models
from core import models as core_models


class OpenSearchDashboard(core_models.HistoryBusinessModel):
    @classmethod
    def get_rights(cls, action):
        """
        The rights governing an action on an OpenSearch dashboard.

        Redeclares nothing: the rights table is
        `opensearch_reports.apps.DJANGO_PERMS`, by entity then by action, and
        `configured_perms` reads the *configured* value there - the one
        ModuleConfiguration may have overridden - and not the declared default.

        The import is done inside the method and not at module import: the `_perms`
        attributes only hold their value after `ready()`, and a snapshot taken at
        import would capture the placeholder - hence an empty list, which
        `has_perms` grants to everybody.

        Returns None for an undeclared action, so that the caller fails closed.
        """
        from opensearch_reports.apps import configured_perms

        return configured_perms("openSearchDashboard", action)

    name = models.CharField(max_length=255, null=False)
    url = models.CharField(max_length=255, null=False)
    synch_disabled = models.BooleanField(default=False)
