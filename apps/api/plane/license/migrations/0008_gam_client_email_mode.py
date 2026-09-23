# GAM addition: client emails start in test mode.

from django.db import migrations

KEYS = {"GAM_CLIENT_EMAILS": "test", "GAM_TEST_EMAIL": "info@gam.gr"}


def create_keys(apps, schema_editor):
    InstanceConfiguration = apps.get_model("license", "InstanceConfiguration")
    for key, default in KEYS.items():
        InstanceConfiguration.objects.get_or_create(
            key=key, defaults={"value": default, "category": "BRANDING", "is_encrypted": False}
        )


def remove_keys(apps, schema_editor):
    apps.get_model("license", "InstanceConfiguration").objects.filter(key__in=KEYS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("license", "0007_gam_brand_configuration"),
    ]

    operations = [migrations.RunPython(create_keys, remove_keys)]
