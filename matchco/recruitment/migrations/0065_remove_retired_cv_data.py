from django.db import migrations


def remove_retired_cv_data(apps, schema_editor):
    EntryPoint = apps.get_model('recruitment', 'EntryPoint')
    Position = apps.get_model('recruitment', 'Position')
    CandidateApplication = apps.get_model('recruitment', 'CandidateApplication')
    CandidateConsent = apps.get_model('recruitment', 'CandidateConsent')
    CandidateProfile = apps.get_model('recruitment', 'CandidateProfile')

    legacy_positions = Position.objects.filter(mode__in=['vaga', 'hybrid'])
    candidate_ids = list(
        CandidateApplication.objects.filter(position__in=legacy_positions)
        .values_list('candidate_id', flat=True)
        .distinct()
    )
    CandidateApplication.objects.filter(position__in=legacy_positions).delete()
    legacy_positions.delete()
    EntryPoint.objects.filter(mode__in=['vaga', 'hybrid']).delete()
    CandidateConsent.objects.filter(purpose='visibility_vaga').delete()
    CandidateProfile.objects.filter(pk__in=candidate_ids).update(visibility_vaga=False)


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0064_alter_entrypoint_mode_alter_position_mode'),
    ]

    operations = [
        migrations.RunPython(remove_retired_cv_data, migrations.RunPython.noop),
    ]
