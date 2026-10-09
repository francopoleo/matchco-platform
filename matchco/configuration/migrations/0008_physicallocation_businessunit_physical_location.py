from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0007_organization_service_subscription'),
    ]

    operations = [
        migrations.CreateModel(
            name='PhysicalLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_key', models.CharField(max_length=160, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('cep', models.CharField(blank=True, max_length=9)),
                ('city', models.CharField(blank=True, max_length=120)),
                ('state', models.CharField(blank=True, max_length=2)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ('name', 'id')},
        ),
        migrations.AddField(
            model_name='businessunit',
            name='physical_location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='business_unit_contexts', to='configuration.physicallocation'),
        ),
    ]
