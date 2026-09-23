# GAM addition: per-service checklist steps, created as sub-items of a work item.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0125_gam_customer_service_billing'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceTemplateItem',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Modified At')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Deleted At')),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('sequence', models.FloatField(default=65535)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Last Modified By')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='template_items', to='db.service')),
            ],
            options={
                'verbose_name': 'Service Template Item',
                'verbose_name_plural': 'Service Template Items',
                'db_table': 'gam_service_template_items',
                'ordering': ('sequence', 'created_at'),
            },
        ),
    ]
