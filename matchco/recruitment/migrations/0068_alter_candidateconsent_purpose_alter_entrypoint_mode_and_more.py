from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0067_remove_cv_visibility_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidateconsent',
            name='purpose',
            field=models.CharField(choices=[
                ('circulation_store', 'Circular para a loja escaneada'),
                ('circulation_network', 'Circular para a rede'),
                ('circulation_shopping', 'Circular para o shopping'),
                ('circulation_radius', 'Circular por raio geográfico'),
                ('visibility_match', 'Aparecer na Porta Match'),
                ('integration_courses', 'Sinais de Cursos no Perfil'),
                ('integration_wiki', 'Consumo de Wiki registrado'),
                ('integration_tests', 'Testes propostos por lojista'),
                ('integration_certifications', 'Certificações no Perfil'),
                ('integration_talk', 'Sinais de Talk no Perfil'),
                ('transactional_messaging', 'Mensagens transacionais'),
            ], max_length=40),
        ),
        migrations.AlterField(
            model_name='entrypoint',
            name='mode',
            field=models.CharField(
                choices=[('match', 'Porta Match (MatchCo)')],
                default='match', max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='position',
            name='mode',
            field=models.CharField(
                choices=[('match', 'Porta Match')],
                db_index=True, default='match', max_length=10,
            ),
        ),
    ]
