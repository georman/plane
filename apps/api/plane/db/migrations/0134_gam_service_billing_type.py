# GAM addition: "monthly" vs "per job" moves from the customer to the service,
# so one customer can have both monthly and per-job services. A service whose
# prices all belonged to retainer customers becomes monthly.

from django.db import migrations, models


def copy_retainer_to_services(apps, schema_editor):
    Service = apps.get_model("db", "Service")
    for service in Service.objects.all():
        types = set(service.rates.values_list("customer__billing_type", flat=True))
        if types == {"retainer"}:
            service.billing_type = "monthly"
            service.save(update_fields=["billing_type"])


class Migration(migrations.Migration):
    dependencies = [("db", "0133_gam_state_names_greek")]

    operations = [
        migrations.AddField(
            model_name="service",
            name="billing_type",
            field=models.CharField(
                choices=[("per_job", "Per job"), ("monthly", "Monthly")], default="per_job", max_length=20
            ),
        ),
        migrations.RunPython(copy_retainer_to_services, migrations.RunPython.noop),
        migrations.RemoveField(model_name="customer", name="billing_type"),
    ]
