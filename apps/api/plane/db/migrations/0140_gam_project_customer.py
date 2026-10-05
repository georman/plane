# GAM: link a project to the customer its work is done for

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0139_gam_customer_portal'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='customer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='projects',
                to='db.customer',
            ),
        ),
    ]
