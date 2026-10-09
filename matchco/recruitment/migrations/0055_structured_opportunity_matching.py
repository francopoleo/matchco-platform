from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0054_expand_shopping_function_catalog'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidateprofile',
            name='availability_period',
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name='candidateprofile',
            name='preferred_work_format',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.AddField(
            model_name='position',
            name='candidate_response_hours',
            field=models.PositiveIntegerField(default=72),
        ),
        migrations.AddField(
            model_name='position',
            name='employer_decision_hours',
            field=models.PositiveIntegerField(default=120),
        ),
        migrations.AddField(
            model_name='position',
            name='invite_batch_size',
            field=models.PositiveIntegerField(default=12),
        ),
        migrations.AddField(
            model_name='position',
            name='negotiable_fields',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='position',
            name='required_days',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='position',
            name='required_experience',
            field=models.CharField(default='any', max_length=16),
        ),
        migrations.AddField(
            model_name='position',
            name='required_experience_contexts',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='position',
            name='required_period',
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name='position',
            name='requested_slots',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
