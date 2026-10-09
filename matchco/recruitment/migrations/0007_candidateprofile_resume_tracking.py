from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('recruitment', '0006_add_flexible_scoring_system')]

    operations = [
        migrations.AddField(model_name='candidateprofile', name='resume_text', field=models.TextField(blank=True, help_text='Plain-text resume pasted by the candidate for search and summarization.', verbose_name='Resume text')),
        migrations.AddField(model_name='candidateprofile', name='qr_id', field=models.CharField(blank=True, db_index=True, max_length=120, verbose_name='QR identifier')),
        migrations.AddField(model_name='candidateprofile', name='utm_source', field=models.CharField(blank=True, max_length=120, verbose_name='Campaign source')),
        migrations.AddField(model_name='candidateprofile', name='utm_medium', field=models.CharField(blank=True, max_length=120, verbose_name='Campaign medium')),
        migrations.AddField(model_name='candidateprofile', name='utm_campaign', field=models.CharField(blank=True, max_length=160, verbose_name='Campaign')),
    ]
