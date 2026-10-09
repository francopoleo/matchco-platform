from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0008_physicallocation_businessunit_physical_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessunit', name='trade_name',
            field=models.CharField(blank=True, max_length=160, verbose_name='Nome comercial'),
        ),
        migrations.AddField(
            model_name='businessunit', name='external_reference',
            field=models.CharField(blank=True, max_length=120, verbose_name='Referência externa'),
        ),
        migrations.AddField(
            model_name='businessunit', name='unit_kind',
            field=models.CharField(choices=[('store', 'Loja'), ('kiosk', 'Quiosque'), ('service', 'Serviço'), ('distribution', 'Centro de distribuição'), ('factory', 'Fábrica'), ('office', 'Escritório'), ('partner', 'Unidade parceira'), ('other', 'Outro')], default='store', max_length=20, verbose_name='Tipo de unidade'),
        ),
        migrations.AddField(
            model_name='businessunit', name='location_type',
            field=models.CharField(choices=[('street', 'Rua / endereço próprio'), ('shopping', 'Shopping / empreendimento'), ('corporate', 'Edifício corporativo'), ('industrial', 'Área industrial'), ('remote', 'Sem endereço público')], default='street', max_length=20, verbose_name='Tipo de localização'),
        ),
        migrations.AddField(
            model_name='businessunit', name='shopping_name',
            field=models.CharField(blank=True, max_length=160, verbose_name='Shopping / empreendimento'),
        ),
        migrations.AddField(
            model_name='businessunit', name='address_number',
            field=models.CharField(blank=True, max_length=20, verbose_name='Número'),
        ),
        migrations.AddField(
            model_name='businessunit', name='address_complement',
            field=models.CharField(blank=True, max_length=120, verbose_name='Complemento'),
        ),
        migrations.AddField(
            model_name='businessunit', name='neighborhood',
            field=models.CharField(blank=True, max_length=120, verbose_name='Bairro'),
        ),
        migrations.AddField(
            model_name='businessunit', name='contact_name',
            field=models.CharField(blank=True, max_length=160, verbose_name='Responsável operacional'),
        ),
        migrations.AddField(
            model_name='businessunit', name='website',
            field=models.URLField(blank=True, verbose_name='Website'),
        ),
        migrations.AddField(
            model_name='businessunit', name='tax_id',
            field=models.CharField(blank=True, max_length=18, verbose_name='CNPJ da unidade'),
        ),
        migrations.AddField(
            model_name='businessunit', name='state_registration',
            field=models.CharField(blank=True, max_length=30, verbose_name='Inscrição estadual'),
        ),
        migrations.AddField(
            model_name='businessunit', name='opening_hours',
            field=models.JSONField(blank=True, default=dict, verbose_name='Horário de funcionamento'),
        ),
    ]
