from django.db import migrations
import datetime
from uuid import uuid4
def add_initial_data(apps, schema_editor):
    data = [
        {'name': 'DataUpdates', 'url': 'goto/752b75eda88e2a379a4c23e28fd4b339?security_tenant=global'},
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
        ('opensearch_reports', '0005_add_opensearch_rights'),  # Update with the actual dependency
    ]

    operations = [
        migrations.RunPython(add_initial_data),
    ]
