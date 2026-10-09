from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0066_remove_formal_application_records'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='candidateprofile',
            name='visibility_vaga',
        ),
    ]
