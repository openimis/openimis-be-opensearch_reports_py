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
    """
    DASHBOARD_NAME = None

    def is_sync_disabled(self):
        try:
            dashboard = OpenSearchDashboard.objects.get(name=self.DASHBOARD_NAME)
            print(dashboard)
            return dashboard.synch_disabled
        except OpenSearchDashboard.DoesNotExist:
            # If no dashboard entry, assume sync is enabled
            return False

    def save(self, **kwargs):
        if not self.is_sync_disabled():
            super().save(**kwargs)  # Proceed with syncing
        else:
            print(f"Sync is disabled for index '{self._index._name}'")
            logger.warning(f"Sync is disabled for index '{self._index._name}'")

    def delete(self, **kwargs):
        if not self.is_sync_disabled():
            super().delete(**kwargs)  # Proceed with deletion
        else:
            print(f"Sync is disabled for index '{self._index._name}'")
            logger.warning(f"Sync is disabled for index '{self._index._name}'")
