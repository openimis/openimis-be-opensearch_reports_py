from django.db import models
from core import models as core_models


class OpenSearchDashboard(core_models.HistoryBusinessModel):
    name = models.CharField(max_length=255, null=False)
    url = models.CharField(max_length=255, null=False)
    synch_disabled = models.BooleanField(default=False)
