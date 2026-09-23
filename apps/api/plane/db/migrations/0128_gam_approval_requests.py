# GAM addition: client approval by email.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0127_gam_issue_recurrences'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApprovalRequest',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Modified At')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Deleted At')),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('recipient_email', models.CharField(max_length=255)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('response', models.CharField(blank=True, choices=[('approved', 'Approved'), ('changes', 'Changes requested')], max_length=20, null=True)),
                ('note', models.TextField(blank=True)),
                ('reminder_count', models.PositiveIntegerField(default=0)),
                ('last_reminder_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Last Modified By')),
                ('issue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gam_approval_requests', to='db.issue')),
                ('requested_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gam_approval_requests', to=settings.AUTH_USER_MODEL)),
                ('state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gam_approval_requests', to='db.state')),
            ],
            options={
                'verbose_name': 'Approval Request',
                'verbose_name_plural': 'Approval Requests',
                'db_table': 'gam_approval_requests',
                'ordering': ('-created_at',),
            },
        ),
    ]
