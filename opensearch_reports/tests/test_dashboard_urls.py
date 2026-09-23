from importlib import import_module

from core.test_helpers import create_test_interactive_user
from django.apps import apps
from django.test import TestCase

from opensearch_reports.models import OpenSearchDashboard

# A link a deployment added itself: same shape, not in the seeded set.
OWN_HASH = 'goto/0123456789abcdef0123456789abcdef'
retarget = import_module(
    'opensearch_reports.migrations.0008_dashboard_urls_global_tenant'
)


class SeededDashboardTenantTest(TestCase):
    """The shipped dashboards are imported into the Global tenant, so every
    seeded link must name it: a private link resolves to the viewer's own,
    empty tenant once multitenancy is on."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = create_test_interactive_user(username='Admin')

    def _dashboard(self, name, url):
        dashboard = OpenSearchDashboard(name=name, url=url)
        dashboard.save(username=self.user.username)
        return dashboard

    def test_no_dashboard_links_to_the_private_tenant(self):
        seeded = OpenSearchDashboard.objects.filter(url__startswith='goto/')
        # Migration 0002 seeds nothing unless a user already exists when it
        # runs, and over an empty table the assertion below holds vacuously.
        self.assertTrue(seeded.exists())

        private = seeded.filter(url__endswith=retarget.PRIVATE)

        self.assertEqual(list(private.values_list('name', flat=True)), [])

    def test_seeded_link_is_retargeted_and_a_deployment_link_is_not(self):
        seeded = self._dashboard(
            'Seeded', retarget.SEEDED_PRIVATE[0] + retarget.PRIVATE
        )
        own = self._dashboard('Ours', OWN_HASH + retarget.PRIVATE)

        retarget.to_global(apps, None)
        seeded.refresh_from_db()
        own.refresh_from_db()

        self.assertEqual(
            seeded.url, retarget.SEEDED_PRIVATE[0] + retarget.GLOBAL
        )
        self.assertEqual(own.url, OWN_HASH + retarget.PRIVATE)

    def test_reverse_restores_the_seeded_link_only(self):
        seeded = self._dashboard(
            'Seeded', retarget.SEEDED_PRIVATE[1] + retarget.GLOBAL
        )
        own = self._dashboard('Ours', OWN_HASH + retarget.GLOBAL)

        retarget.to_private(apps, None)
        seeded.refresh_from_db()
        own.refresh_from_db()

        self.assertEqual(
            seeded.url, retarget.SEEDED_PRIVATE[1] + retarget.PRIVATE
        )
        self.assertEqual(own.url, OWN_HASH + retarget.GLOBAL)
