# GAM addition: Greek names for the job pipeline states, in every project
# that uses the pipeline (has a "New request" state). Other projects, like
# the onboarding demo, are left alone.

from django.db import migrations

NAMES = {
    "New request": "Νέο αίτημα",
    "Quotation": "Προσφορά",
    "Approved": "Εγκρίθηκε",
    "In progress": "Σε εξέλιξη",
    "Internal review": "Εσωτερικός έλεγχος",
    "Client approval": "Έγκριση πελάτη",
    "Corrections": "Διορθώσεις",
    "Ready for delivery": "Έτοιμο για παράδοση",
    "Delivered": "Παραδόθηκε",
    "Invoiced": "Τιμολογήθηκε",
    "Cancelled": "Ακυρώθηκε",
}


def rename(apps, names):
    State = apps.get_model("db", "State")
    first = next(iter(names))
    project_ids = list(State.objects.filter(name=first, deleted_at__isnull=True).values_list("project_id", flat=True))
    for old, new in names.items():
        for state in State.objects.filter(project_id__in=project_ids, name=old, deleted_at__isnull=True):
            if not State.objects.filter(project_id=state.project_id, name=new, deleted_at__isnull=True).exists():
                state.name = new
                state.save(update_fields=["name"])


def to_greek(apps, schema_editor):
    rename(apps, NAMES)


def to_english(apps, schema_editor):
    rename(apps, {v: k for k, v in NAMES.items()})


class Migration(migrations.Migration):
    dependencies = [("db", "0132_gam_profile_language_greek")]

    operations = [migrations.RunPython(to_greek, to_english)]
