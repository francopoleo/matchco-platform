from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('documents', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='MediaAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=220)),
                ('kind', models.CharField(choices=[('image', 'Imagem'), ('video', 'Vídeo'), ('file', 'Arquivo')], default='image', max_length=12)),
                ('file', models.FileField(blank=True, upload_to='media-library/')),
                ('external_url', models.URLField(blank=True)),
                ('alt_text', models.CharField(blank=True, max_length=220)),
                ('description', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='media_assets', to='tenants_core.tenantorganization')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='owned_media_assets', to='tenants_core.tenantuser')),
            ],
            options={'ordering': ('-updated_at', '-created_at')},
        ),
    ]
