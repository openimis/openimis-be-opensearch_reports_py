import logging

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
