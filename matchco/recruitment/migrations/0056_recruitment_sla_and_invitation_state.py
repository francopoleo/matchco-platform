from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0055_structured_opportunity_matching'),
    ]

    operations = [
        migrations.AddField(model_name='recruitmentpolicy', name='candidate_response_hours', field=models.PositiveIntegerField(default=72)),
        migrations.AddField(model_name='recruitmentpolicy', name='employer_decision_hours', field=models.PositiveIntegerField(default=120)),
        migrations.AddField(model_name='recruitmentpolicy', name='invite_batch_size', field=models.PositiveIntegerField(default=12)),
        migrations.AddField(model_name='recruitmentpolicy', name='round_wait_hours', field=models.PositiveIntegerField(default=24)),
        migrations.AddField(model_name='recruitmentstore', name='candidate_response_hours_override', field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name='recruitmentstore', name='employer_decision_hours_override', field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name='recruitmentstore', name='invite_batch_size_override', field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name='recruitmentstore', name='round_wait_hours_override', field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name='relation', name='employer_decision_expires_at', field=models.DateTimeField(blank=True, db_index=True, null=True)),
        migrations.AddField(model_name='relation', name='negotiation_fields', field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name='relation', name='negotiation_proposal', field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name='relation', name='negotiation_state', field=models.CharField(default='none', max_length=16)),
        migrations.AddField(model_name='relation', name='notice_expired_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='relation', name='notice_expires_at', field=models.DateTimeField(blank=True, db_index=True, null=True)),
    ]
