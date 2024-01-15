from django.apps import AppConfig

DEFAULT_CONFIG = {
    "gql_opensearch_dashboard_search_perms": ["199001"],
    "gql_opensearch_dashboard_update_perms": ["199003"],
}


class OpensearchReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opensearch_reports'

    gql_opensearch_dashboard_search_perms = None
    gql_opensearch_dashboard_update_perms = None

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
