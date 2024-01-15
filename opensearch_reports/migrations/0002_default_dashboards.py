from django.db import migrations
from core.models import User
from opensearch_reports.models import OpenSearchDashboard


def add_initial_data(apps, schema_editor):
    data = [
        {'name': 'Beneficiary', 'url': 'goto/f36ce4c256637ca76cc31db315696e5a?security_tenant=private'},
        {'name': 'Invoice', 'url': 'goto/7f28c3e4677054e33090c2306c57f6d9?security_tenant=private'},
        {'name': 'Payment', 'url': 'goto/1e2d392d68907f9900f10e6289cb322f?security_tenant=private'},
        {'name': 'Grievance', 'url': 'goto/07f453c884ec6b24eaa5e44df8fee4e5?security_tenant=private'},
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
        ('opensearch_reports', '0001_initial'),  # Update with the actual dependency
    ]

    operations = [
        migrations.RunPython(add_initial_data),
    ]
