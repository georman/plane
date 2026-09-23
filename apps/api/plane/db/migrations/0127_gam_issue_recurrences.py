# GAM addition: repeating work items.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0126_gam_service_template_items'),
    ]

    operations = [
        migrations.CreateModel(
            name='IssueRecurrence',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Modified At')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Deleted At')),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('frequency', models.CharField(choices=[('weekly', 'Every week'), ('monthly', 'Every month'), ('yearly', 'Every year')], max_length=20)),
                ('next_run_date', models.DateField()),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Last Modified By')),
                ('issue', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='gam_recurrence', to='db.issue')),
            ],
            options={
                'verbose_name': 'Issue Recurrence',
                'verbose_name_plural': 'Issue Recurrences',
                'db_table': 'gam_issue_recurrences',
            },
        ),
    ]
