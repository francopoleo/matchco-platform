from django.db import migrations, models


def empty_identity_emails_to_null(apps, schema_editor):
    CandidateIdentity = apps.get_model('recruitment', 'CandidateIdentity')
    CandidateIdentity.objects.filter(email_normalized='').update(email_normalized=None)


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0059_remove_canonicalfunctionmapping_unique_canonical_function_mapping_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidateidentity',
            name='email_normalized',
            field=models.EmailField(blank=True, db_index=True, max_length=254, null=True, unique=True),
        ),
        migrations.RunPython(empty_identity_emails_to_null, migrations.RunPython.noop),
    ]
