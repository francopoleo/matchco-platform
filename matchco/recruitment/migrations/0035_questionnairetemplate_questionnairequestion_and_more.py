from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0034_entrypoint_experience'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionnaireTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(max_length=100)),
                ('name', models.CharField(max_length=180)),
                ('description', models.TextField(blank=True)),
                ('version', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(choices=[('draft', 'Rascunho'), ('published', 'Publicado'), ('archived', 'Arquivado')], db_index=True, default='draft', max_length=12)),
                ('purpose', models.CharField(choices=[('recruitment', 'Recrutamento')], default='recruitment', max_length=24)),
                ('audience_role', models.CharField(blank=True, max_length=80)),
                ('market', models.CharField(blank=True, max_length=80)),
                ('is_default', models.BooleanField(default=False)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('entry_point', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questionnaire_templates', to='recruitment.entrypoint')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questionnaire_templates', to='recruitment.recruitmentorganization')),
                ('scope_channel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questionnaire_templates', to='recruitment.recruitmentchannel')),
                ('scope_job_function', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questionnaire_templates', to='recruitment.recruitmentjobfunction')),
                ('scope_store', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questionnaire_templates', to='recruitment.recruitmentstore')),
            ],
            options={
                'ordering': ['-is_default', '-version', 'name'],
            },
        ),
        migrations.CreateModel(
            name='QuestionnaireQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.SlugField(max_length=100)),
                ('label', models.CharField(max_length=240)),
                ('help_text', models.CharField(blank=True, max_length=300)),
                ('field_type', models.CharField(choices=[('text', 'Texto curto'), ('textarea', 'Texto longo'), ('single_choice', 'Uma opção'), ('multiple_choice', 'Várias opções'), ('boolean', 'Sim ou não'), ('number', 'Número'), ('date', 'Data'), ('file', 'Arquivo'), ('scale', 'Escala')], default='text', max_length=20)),
                ('options', models.JSONField(blank=True, default=list)),
                ('conditions', models.JSONField(blank=True, default=dict, help_text='Condição simples, por exemplo {"key": "experiencia", "equals": "sim"}.')),
                ('scoring', models.JSONField(blank=True, default=dict)),
                ('required', models.BooleanField(default=False)),
                ('order', models.PositiveIntegerField(default=0)),
                ('active', models.BooleanField(default=True)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='recruitment.questionnairetemplate')),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.AddField(
            model_name='candidateprofilesurveyresponse',
            name='questionnaire_template',
            field=models.ForeignKey(blank=True, help_text='Versão exata do questionário apresentada ao candidato.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='responses', to='recruitment.questionnairetemplate'),
        ),
        migrations.AddIndex(
            model_name='questionnairetemplate',
            index=models.Index(fields=['organization', 'status', 'purpose'], name='recruitment_organiz_4967a2_idx'),
        ),
        migrations.AddIndex(
            model_name='questionnairetemplate',
            index=models.Index(fields=['entry_point', 'status'], name='recruitment_entry_p_b020b4_idx'),
        ),
        migrations.AddConstraint(
            model_name='questionnairetemplate',
            constraint=models.UniqueConstraint(fields=('organization', 'code', 'version'), name='recruitment_questionnaire_org_code_version'),
        ),
        migrations.AddConstraint(
            model_name='questionnairequestion',
            constraint=models.UniqueConstraint(fields=('template', 'key'), name='recruitment_questionnaire_template_key'),
        ),
    ]
