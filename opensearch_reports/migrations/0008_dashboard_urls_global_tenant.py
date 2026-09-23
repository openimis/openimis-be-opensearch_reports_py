from django.db import migrations
from django.db.models import Value
from django.db.models.functions import Replace

PRIVATE = '?security_tenant=private'
GLOBAL = '?security_tenant=global'

# The four dashboards 0002 seeded with the private tenant. Matched by hash in
# both directions so that links a deployment added itself are never rewritten.
SEEDED_PRIVATE = (
    'goto/f36ce4c256637ca76cc31db315696e5a',
    'goto/7f28c3e4677054e33090c2306c57f6d9',
    'goto/1e2d392d68907f9900f10e6289cb322f',
    'goto/07f453c884ec6b24eaa5e44df8fee4e5',
)


def _retarget(apps, old, new):
    OpenSearchDashboard = apps.get_model(
        'opensearch_reports', 'OpenSearchDashboard'
    )
    OpenSearchDashboard.objects.filter(
        url__in=[hash_ + old for hash_ in SEEDED_PRIVATE]
    ).update(url=Replace('url', Value(old), Value(new)))


def to_global(apps, schema_editor):
    """The shipped dashboards live in the Global tenant, not each user's own.

    Inert while multitenancy is off. Once it is on, a private link resolves to
    the viewer's own, empty tenant and the dashboard is not found for anyone;
    the import command sends no tenant header, so the saved objects land in
    the preferred tenant, which is Global.
    """
    _retarget(apps, PRIVATE, GLOBAL)


def to_private(apps, schema_editor):
    _retarget(apps, GLOBAL, PRIVATE)


class Migration(migrations.Migration):
    dependencies = [
        ('opensearch_reports',
         '0007_historicalopensearchdashboard_synch_disabled_and_more'),
    ]

    operations = [
        migrations.RunPython(to_global, to_private),
    ]
