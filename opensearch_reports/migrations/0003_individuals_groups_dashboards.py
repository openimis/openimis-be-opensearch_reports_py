from django.db import migrations
from core.models import User
from opensearch_reports.models import OpenSearchDashboard


def add_initial_data(apps, schema_editor):
    data = [
        {'name': 'Individual', 'url': 'goto/8dbcd2fbd40419520645c41f02d8f4e9?security_tenant=global'},
        {'name': 'Group', 'url': 'goto/2668304c9e04912fc67e7cd34eff7e4c?security_tenant=global'},
    ]

    user = User.objects.all().first()

    if user:
        for item in data:
            osd = OpenSearchDashboard(
                name=item['name'],
                url=item['url']
            )
            osd.save(username=user.username)


class Migration(migrations.Migration):

    dependencies = [
        ('opensearch_reports', '0002_default_dashboards'),  # Update with the actual dependency
    ]

    operations = [
        migrations.RunPython(add_initial_data),
    ]
