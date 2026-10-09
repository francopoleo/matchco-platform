from django.db import migrations


def retire_cv_flow(apps, schema_editor):
    EntryPoint = apps.get_model('recruitment', 'EntryPoint')
    Position = apps.get_model('recruitment', 'Position')

    EntryPoint.objects.filter(
        mode__in=['vaga', 'hybrid'],
        state__in=['draft', 'tested', 'active'],
    ).update(state='revoked')
    Position.objects.filter(
        mode__in=['vaga', 'hybrid'],
        state__in=['structured', 'activated', 'circulated'],
    ).update(state='closed')


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0062_position_benefits_position_employment_type'),
    ]

    operations = [
        migrations.RunPython(retire_cv_flow, migrations.RunPython.noop),
    ]
