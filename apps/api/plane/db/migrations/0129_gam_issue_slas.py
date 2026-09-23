# GAM addition: first-response SLA.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0128_gam_approval_requests'),
    ]

    operations = [
        migrations.CreateModel(
            name='IssueSLA',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Modified At')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Deleted At')),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('priority', models.CharField(max_length=30)),
                ('started_at', models.DateTimeField()),
                ('due_at', models.DateTimeField()),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('warned_at', models.DateTimeField(blank=True, null=True)),
                ('breached_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Last Modified By')),
                ('issue', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='gam_sla', to='db.issue')),
            ],
            options={
                'verbose_name': 'Issue SLA',
                'verbose_name_plural': 'Issue SLAs',
                'db_table': 'gam_issue_slas',
            },
        ),
    ]
