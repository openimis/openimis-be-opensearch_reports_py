from django.apps import AppConfig

from core.rights_declaration import RightsDeclaration

MODULE_NAME = 'opensearch_reports'

# Rights, by entity then by action. The module exposes only a read and an update of
# the dashboard: no creation and no deletion on the GraphQL side, dashboards being laid
# down by migration or by the upload command. 199002 and 199004 therefore stay free in
# the module's block.
DJANGO_PERMS = {
    "openSearchDashboard": {
        "query": ("opensearch_reports.view_opensearchdashboard", 199001),
        "update": ("opensearch_reports.change_opensearchdashboard", 199003),
    },
}

_PERM_CFG = {
    "gql_opensearch_dashboard_search_perms": ("openSearchDashboard", "query"),
    "gql_opensearch_dashboard_update_perms": ("openSearchDashboard", "update"),
}

RIGHTS = RightsDeclaration(MODULE_NAME, DJANGO_PERMS, _PERM_CFG)

perms = RIGHTS.perms
django_perms = RIGHTS.django_perm_names
configured_perms = RIGHTS.configured
require = RIGHTS.require


DEFAULT_CONFIG = {
}


class OpensearchReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = MODULE_NAME

    # Rights: constants, no longer overridable. They go neither through DEFAULT_CFG
    # nor through ready(): `ModuleConfiguration.get_or_default` now ignores any
    # `_perms` key stored in the database.
    # `search` carries the read: the key name is the deployed one, read by
    # `views.opensearch_auth_check` (the nginx auth_request) as much as by the resolver.
    gql_opensearch_dashboard_search_perms = RIGHTS.perms("openSearchDashboard", "query")
    gql_opensearch_dashboard_update_perms = RIGHTS.perms("openSearchDashboard", "update")

    def ready(self):
        from core.models import ModuleConfiguration

        cfg = ModuleConfiguration.get_or_default(self.name, DEFAULT_CONFIG)
        self.__load_config(cfg)

    @classmethod
    def __load_config(cls, cfg):
        """
        Load all config fields that match current AppConfig class fields, all custom fields have to be loaded separately
        """
        for field in cfg:
            if hasattr(OpensearchReportsConfig, field):
                setattr(OpensearchReportsConfig, field, cfg[field])
