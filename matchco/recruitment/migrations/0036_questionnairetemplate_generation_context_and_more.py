from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0035_questionnairetemplate_questionnairequestion_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnairetemplate',
            name='generation_context',
            field=models.JSONField(blank=True, default=dict, help_text='Brief estruturado que originou um rascunho assistido.'),
        ),
        migrations.AddField(
            model_name='questionnairetemplate',
            name='source',
            field=models.CharField(default='manual', help_text='manual, seed ou ai_draft; usado para auditoria da configuração.', max_length=24),
        ),
    ]
