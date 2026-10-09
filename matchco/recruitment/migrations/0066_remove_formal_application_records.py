from django.db import migrations


def remove_formal_application_records(apps, schema_editor):
    CandidateApplication = apps.get_model('recruitment', 'CandidateApplication')
    CandidateApplication.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0065_remove_retired_cv_data'),
    ]

    operations = [
        migrations.RunPython(remove_formal_application_records, migrations.RunPython.noop),
    ]
