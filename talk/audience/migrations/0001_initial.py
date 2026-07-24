from django.db import migrations, models
import django.db.models.deletion
from django.contrib.postgres.fields import JSONField


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='AudiencePolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160)),
                ('description', models.TextField(blank=True)),
                ('match_mode', models.CharField(choices=[('all', 'All rules'), ('any', 'Any rule')], default='all', max_length=3)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ('name',)},
        ),
        migrations.CreateModel(
            name='AudienceRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dimension', models.CharField(max_length=64)),
                ('operator', models.CharField(default='in', max_length=32)),
                ('values', JSONField(default=list)),
                ('negate', models.BooleanField(default=False)),
                ('position', models.PositiveIntegerField(default=0)),
                ('policy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='audience.audiencepolicy')),
            ],
            options={'ordering': ('position', 'id')},
        ),
    ]
