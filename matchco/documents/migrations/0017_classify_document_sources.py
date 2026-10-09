from django.db import migrations


def classify_existing_versions(apps, schema_editor):
    DocumentVersion = apps.get_model('documents', 'DocumentVersion')
    DocumentVersion.objects.filter(file='', body__gt='').update(source_type='rich_text')


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0016_documentversion_content_representations'),
    ]

    operations = [migrations.RunPython(classify_existing_versions, migrations.RunPython.noop)]
