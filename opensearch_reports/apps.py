from django.apps import AppConfig

DEFAULT_CONFIG = {}


class OpensearchReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'opensearch_reports'

    def ready(self):
        from core.models import ModuleConfiguration

        cfg = ModuleConfiguration.get_or_default(self.name, DEFAULT_CONFIG)
        self._load_config(cfg)

    @classmethod
    def _load_config(cls, cfg):
        """
        Load all config fields that match current AppConfig class fields, all custom fields have to be loaded separately
        """
        for field in cfg:
            if hasattr(OpensearchReportsConfig, field):
                setattr(OpensearchReportsConfig, field, cfg[field])
