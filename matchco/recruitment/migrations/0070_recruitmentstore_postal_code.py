from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0069_candidateprofile_available_from'),
    ]

    operations = [
        migrations.AddField(
            model_name='recruitmentstore',
            name='postal_code',
            field=models.CharField(blank=True, db_index=True, max_length=9),
        ),
    ]
