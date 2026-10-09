from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0009_businessunit_cadastral_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='organizationservicesubscription',
            options={'ordering': ['organization', 'company', 'service_code']},
        ),
        migrations.AddField(
            model_name='organizationservicesubscription',
            name='company',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='service_subscriptions',
                to='configuration.company',
            ),
        ),
        migrations.RemoveConstraint(
            model_name='organizationservicesubscription',
            name='uniq_org_service_subscription',
        ),
        migrations.AddConstraint(
            model_name='organizationservicesubscription',
            constraint=models.UniqueConstraint(
                condition=models.Q(('company__isnull', True)),
                fields=('organization', 'service_code'),
                name='uniq_org_default_service_subscription',
            ),
        ),
        migrations.AddConstraint(
            model_name='organizationservicesubscription',
            constraint=models.UniqueConstraint(
                condition=models.Q(('company__isnull', False)),
                fields=('organization', 'company', 'service_code'),
                name='uniq_company_service_subscription',
            ),
        ),
    ]
