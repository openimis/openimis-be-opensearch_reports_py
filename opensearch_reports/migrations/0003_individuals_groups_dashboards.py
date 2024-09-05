from django.db import migrations
import datetime
from uuid import uuid4
def add_initial_data(apps, schema_editor):
    data = [
        {'name': 'Individual', 'url': 'goto/8dbcd2fbd40419520645c41f02d8f4e9?security_tenant=global'},
        {'name': 'Group', 'url': 'goto/2668304c9e04912fc67e7cd34eff7e4c?security_tenant=global'},
    ]
    OpenSearchDashboard = apps.get_model('opensearch_reports', 'OpenSearchDashboard')
    User = apps.get_model('core', 'User')
    user = User.objects.all().first()
    now = datetime.datetime.now()
    if user:
        for item in data:
            osd = OpenSearchDashboard(
                id=uuid4(),
                name=item['name'],
                url=item['url'],
                user_created=user,
                user_updated=user,
                date_created=now,
                date_updated=now,
                date_valid_from=now
            )
            osd.save()


class Migration(migrations.Migration):

    dependencies = [
        ('opensearch_reports', '0002_default_dashboards'),  # Update with the actual dependency
    ]

    operations = [
        migrations.RunPython(add_initial_data),
    ]
