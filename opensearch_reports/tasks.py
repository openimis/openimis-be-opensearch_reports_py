import logging

from celery import shared_task
from django.apps import apps
from django_opensearch_dsl.registries import registry

logger = logging.getLogger(__name__)


@shared_task
def index_opensearch_bulk(app_label, model_name, actions, using=None, **kwargs):
    for doc in _get_documents(app_label, model_name):
        doc.bulk(iter(actions), using=using, from_celery=True, **kwargs)


def _get_documents(app_label, model_name):
    Model = apps.get_model(app_label, model_name)
    document_classes = registry._models[Model]
    if not document_classes:
        logger.warning(f"No OpenSearch document found for model: {model_name} in app: {app_label}")
        return

    for doc_class in document_classes:
        yield doc_class()
