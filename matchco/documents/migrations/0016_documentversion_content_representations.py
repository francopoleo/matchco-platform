from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0015_mediaasset_audience_policy_mediaasset_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentversion',
            name='source_type',
            field=models.CharField(choices=[('upload', 'Arquivo anexado'), ('rich_text', 'Conteúdo criado no sistema'), ('generated', 'PDF gerado pelo sistema'), ('external', 'Link externo')], default='upload', max_length=12),
        ),
        migrations.AddField(
            model_name='documentversion',
            name='external_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='documentversion',
            name='generated_pdf',
            field=models.FileField(blank=True, upload_to='documents/generated/'),
        ),
        migrations.AddField(
            model_name='documentversion',
            name='thumbnail_file',
            field=models.ImageField(blank=True, upload_to='documents/previews/'),
        ),
        migrations.AddField(
            model_name='documentversion',
            name='generated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='documentversion',
            name='generated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generated_document_pdfs', to='tenants_core.tenantuser'),
        ),
    ]
