from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenants_core', '0001_initial'),
        ('documents', '0017_classify_document_sources'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='company',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='documents',
                to='tenants_core.tenantcompany',
            ),
        ),
    ]
