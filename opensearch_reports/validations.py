from core.validation import BaseModelValidation
from opensearch_reports.models import OpenSearchDashboard


class OpenSearchDashboardValidation(BaseModelValidation):
    OBJECT_TYPE = OpenSearchDashboard
