# GAM addition: white-label brand settings.

from django.db import migrations

BRAND_KEYS = {
    "GAM_BRAND_NAME": "GAM",
    "GAM_SUPPORT_EMAIL": "info@gam.gr",
    "GAM_BRAND_WEBSITE": "",
    "GAM_BRAND_LOGO": "",
}


def create_brand_keys(apps, schema_editor):
    InstanceConfiguration = apps.get_model("license", "InstanceConfiguration")
    for key, default in BRAND_KEYS.items():
        InstanceConfiguration.objects.get_or_create(
            key=key, defaults={"value": default, "category": "BRANDING", "is_encrypted": False}
        )


def remove_brand_keys(apps, schema_editor):
    apps.get_model("license", "InstanceConfiguration").objects.filter(key__in=BRAND_KEYS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("license", "0006_instance_is_current_version_deprecated"),
    ]

    operations = [migrations.RunPython(create_brand_keys, remove_brand_keys)]
