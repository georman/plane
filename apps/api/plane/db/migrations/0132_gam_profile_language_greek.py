# GAM: the interface is Greek by default. Accounts created before Greek was
# added still carry the old "en" default (nobody chose it), so move them to Greek.

from django.db import migrations, models


def to_greek(apps, schema_editor):
    apps.get_model("db", "Profile").objects.filter(language="en").update(language="el")


class Migration(migrations.Migration):

    dependencies = [
        ("db", "0131_gam_billing_statements"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="language",
            field=models.CharField(default="el", max_length=255),
        ),
        migrations.RunPython(to_greek, migrations.RunPython.noop),
    ]
