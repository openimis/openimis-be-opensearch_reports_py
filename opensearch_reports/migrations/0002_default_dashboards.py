from django.db import migrations
from datetime import datetime
from uuid import uuid4

def add_initial_data(apps, schema_editor):
    data = [
        {'name': 'Beneficiary', 'url': 'goto/f36ce4c256637ca76cc31db315696e5a?security_tenant=private'},
        {'name': 'Invoice', 'url': 'goto/7f28c3e4677054e33090c2306c57f6d9?security_tenant=private'},
        {'name': 'Payment', 'url': 'goto/1e2d392d68907f9900f10e6289cb322f?security_tenant=private'},
        {'name': 'Grievance', 'url': 'goto/07f453c884ec6b24eaa5e44df8fee4e5?security_tenant=private'},
    ]
    User = apps.get_model('core', 'User')
    OpenSearchDashboard = apps.get_model('opensearch_reports', 'OpenSearchDashboard')

    user = User.objects.all().first()
    now = datetime.now()
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
        ('opensearch_reports', '0001_initial'),  # Update with the actual dependency
    ]

    operations = [
        migrations.RunPython(add_initial_data),
    ]
