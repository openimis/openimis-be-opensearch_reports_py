from core.models import MutationLog
from core.test_helpers import create_test_interactive_user
from django.test import TestCase, override_settings
from django_opensearch_dsl.registries import registry, DODConfig
from django_opensearch_dsl.documents import Document
from django_opensearch_dsl.registries import registry
from unittest.mock import patch
from unittest import skipIf
from opensearchpy import OpenSearch
from core import settings
from opensearch_reports.models import OpenSearchDashboard
from opensearch_reports.service import BaseSyncDocument


class MutationLogDocument(BaseSyncDocument):
    DASHBOARD_NAME = 'MutationLog'

    class Index:
        name = "mutation_log_index"
        auto_refresh = True

    class Django:
        model = MutationLog
        fields = ["json_content"]
        ignore_signals = False


@override_settings(task_always_eager=True, task_eager_propagates=True)
class BaseSyncDocumentTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = create_test_interactive_user(username="admin")
        registry.register_document(MutationLogDocument)
        cls.dashboard = OpenSearchDashboard(
            name=MutationLogDocument.DASHBOARD_NAME,
            synch_disabled=False,
            url='http://localhost/opensearch'
        )
        cls.dashboard.save(username=cls.user.username)

    @patch.object(Document, "bulk")
    @skipIf(not settings.OPENSEARCH_DSL_AUTOSYNC, "Skipping test because OPENSEARCH_DSL_AUTOSYNC is False")
    def test_auto_refresh_sync_enabled(self, mock_doc_bulk):
        log = MutationLog.objects.create(json_content='foobar')

        mock_doc_bulk.assert_called()

        # Ensure the correct instance is being indexed
        actions = mock_doc_bulk.call_args[0][0]  # First positional argument
        action = next(actions)
        self.assertEqual(action['_id'], log.pk)
        self.assertEqual(action['_op_type'], 'index')

        kwargs = mock_doc_bulk.call_args[1]
        self.assertTrue('refresh' in kwargs)
        self.assertTrue(kwargs['refresh'])

    @patch.object(Document, "bulk")
    def test_auto_refresh_sync_disabled(self, mock_doc_bulk):
        # Disable sync
        self.dashboard.synch_disabled = True
        self.dashboard.save(username=self.user.username)

        log = MutationLog.objects.create(json_content='foobarbaz')

        # Indexing should NOT proceed because sync is disabled
        mock_doc_bulk.assert_not_called()

    @patch.object(Document, "bulk")
    def test_bulk_update(self, mock_doc_bulk):
        log1 = MutationLog(json_content='log1')
        log2 = MutationLog(json_content='log2')
        MutationLog.objects.bulk_create([log1, log2])
        logs = MutationLog.objects.filter(json_content__contains='log')

        MutationLogDocument().update(logs, 'index')

        mock_doc_bulk.assert_called()

        actions = list(mock_doc_bulk.call_args[0][0])
        sorted_ids = sorted(action['_id'] for action in actions)
        expected_ids = sorted(logs.values_list('pk', flat=True))
        self.assertEqual(sorted_ids, expected_ids)

        kwargs = mock_doc_bulk.call_args[1]
        self.assertTrue('refresh' in kwargs)
        self.assertTrue(kwargs['refresh'])
