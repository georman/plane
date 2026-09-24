# GAM addition: Terms of Service / Privacy Policy, edited in God mode > Legal.
# Empty text = the standard text in plane/license/utils/gam_legal_defaults.py.

from django.db import migrations

KEYS = [
    "GAM_LEGAL_COMPANY",
    "GAM_LEGAL_ADDRESS",
    "GAM_LEGAL_UPDATED",
    "GAM_LEGAL_TERMS_EL",
    "GAM_LEGAL_TERMS_EN",
    "GAM_LEGAL_PRIVACY_EL",
    "GAM_LEGAL_PRIVACY_EN",
]


def create_keys(apps, schema_editor):
    InstanceConfiguration = apps.get_model("license", "InstanceConfiguration")
    for key in KEYS:
        InstanceConfiguration.objects.get_or_create(
            key=key, defaults={"value": "", "category": "LEGAL", "is_encrypted": False}
        )


def remove_keys(apps, schema_editor):
    apps.get_model("license", "InstanceConfiguration").objects.filter(key__in=KEYS).delete()


class Migration(migrations.Migration):
    dependencies = [("license", "0008_gam_client_email_mode")]

    operations = [migrations.RunPython(create_keys, remove_keys)]
