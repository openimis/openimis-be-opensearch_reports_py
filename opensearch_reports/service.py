import logging

from django_opensearch_dsl import Document

from core.services import BaseService
from core.signals import register_service_signal
from opensearch_reports.models import OpenSearchDashboard
from opensearch_reports.validations import OpenSearchDashboardValidation

logger = logging.getLogger(__name__)


class OpenSearchDashboardService(BaseService):

    @register_service_signal('opensearch_dashboard_service.update')
    def update(self, obj_data):
        return super().update(obj_data)

    OBJECT_TYPE = OpenSearchDashboard

    def __init__(self, user, validation_class=OpenSearchDashboardValidation):
        super().__init__(user, validation_class)


class BaseSyncDocument(Document):
    """
    Base document class that controls synchronization based on the 'synch_disabled' flag.
    All OpenSearch document classes should inherit from this class.
    DASHBOARD_NAME - connecting document with dashboard
    """
    DASHBOARD_NAME = None

    def is_sync_disabled(self):
        try:
            dashboard = OpenSearchDashboard.objects.get(name=self.DASHBOARD_NAME)
            return dashboard.synch_disabled
        except OpenSearchDashboard.DoesNotExist:
            # If no dashboard entry, assume sync is enabled
            return False

    def update(self, thing, action, *args, refresh=None, using=None, **kwargs):
        """
        Override the update method to control synchronization dynamically.
        """
        if not self.is_sync_disabled():
            # Proceed with normal update if sync is not disabled
            return super().update(thing, action, *args, refresh=refresh, using=using, **kwargs)
        else:
            # Log and skip syncing if disabled
            logger.info(f"Sync is disabled for index '{self._index._name}'")
            return None

    def bulk(self, actions, using=None, **kwargs):
        """
        Override the bulk method to control batch synchronization dynamically.
        """
        if not self.is_sync_disabled():
            return super().bulk(actions, using=using, **kwargs)
        else:
            # Log and skip bulk syncing if disabled
            logger.info(f"Bulk sync is disabled for index '{self._index._name}'")
            return None
