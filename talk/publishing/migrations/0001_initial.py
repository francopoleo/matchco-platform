from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('audience', '0001_initial'),
    ]
    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
                ('slug', models.SlugField(max_length=90, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('wiki', 'Wiki'), ('feed', 'Feed')], max_length=8)),
                ('title', models.CharField(max_length=220)),
                ('slug', models.SlugField(max_length=240, unique=True)),
                ('excerpt', models.TextField(blank=True)),
                ('body', models.TextField()),
                ('image', models.ImageField(blank=True, upload_to='publishing/images/')),
                ('video_url', models.URLField(blank=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published')], default='draft', max_length=12)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('points_per_view', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('audience_policy', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='audience.audiencepolicy')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='publications', to=settings.AUTH_USER_MODEL)),
                ('tags', models.ManyToManyField(blank=True, related_name='publications', to='publishing.tag')),
            ],
            options={'ordering': ('-published_at', '-created_at')},
        ),
    ]
