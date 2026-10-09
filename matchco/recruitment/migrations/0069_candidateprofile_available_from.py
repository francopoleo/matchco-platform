from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0068_alter_candidateconsent_purpose_alter_entrypoint_mode_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidateprofile',
            name='available_from',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
    ]
