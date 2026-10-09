from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0006_sectortemplate_organization_brand_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationServiceSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_code', models.CharField(choices=[('content', 'Content'), ('talk', 'Talk'), ('training', 'Training'), ('certification', 'Certification'), ('recruitment', 'Recruitment Match'), ('campaigns', 'Campaigns and surveys'), ('operations', 'Operations'), ('partners', 'Partners'), ('analytics', 'Analytics')], max_length=32)),
                ('status', models.CharField(choices=[('active', 'Active'), ('suspended', 'Suspended'), ('expired', 'Expired')], default='active', max_length=16)),
                ('plan_code', models.CharField(blank=True, default='', max_length=80)),
                ('starts_at', models.DateTimeField(blank=True, null=True)),
                ('ends_at', models.DateTimeField(blank=True, null=True)),
                ('configuration', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_subscriptions', to='configuration.organization')),
            ],
            options={
                'ordering': ['organization', 'service_code'],
            },
        ),
        migrations.AddConstraint(
            model_name='organizationservicesubscription',
            constraint=models.UniqueConstraint(fields=('organization', 'service_code'), name='uniq_org_service_subscription'),
        ),
    ]
