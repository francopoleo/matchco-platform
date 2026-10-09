from django.db import migrations


FUNCTIONS = [
    ('caixa-de-loja', 'Caixa de loja'),
    ('atendimento-de-loja', 'Atendimento de loja'),
    ('vendedor-de-loja', 'Vendedor de loja'),
    ('estoquista-de-loja', 'Estoquista de loja'),
    ('repositor-de-loja', 'Repositor de loja'),
    ('gerente-de-loja', 'Gerente de loja'),
    ('atendente-de-farmacia', 'Atendente de farmácia'),
    ('balconista-de-farmacia', 'Balconista de farmácia'),
    ('farmaceutico-responsavel-tecnico', 'Farmacêutico responsável técnico'),
    ('atendente-de-praca-de-alimentacao', 'Atendente de praça de alimentação'),
    ('auxiliar-de-cozinha', 'Auxiliar de cozinha'),
    ('cozinheiro', 'Cozinheiro'),
    ('auxiliar-de-servicos-gerais', 'Auxiliar de serviços gerais'),
]


def seed_functions(apps, schema_editor):
    Catalog = apps.get_model('recruitment', 'CanonicalCatalog')
    Term = apps.get_model('recruitment', 'CanonicalTerm')
    catalog, _ = Catalog.objects.get_or_create(
        code='market-default',
        version=1,
        defaults={
            'name': 'Funções canônicas de mercado',
            'status': 'published',
            'source': 'system_default',
        },
    )
    for code, label in FUNCTIONS:
        Term.objects.get_or_create(
            catalog=catalog,
            code=code,
            defaults={
                'term_type': 'function',
                'label': label,
                'normalized_label': label.lower(),
                'active': True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0050_alter_candidateposition_options'),
    ]

    operations = [migrations.RunPython(seed_functions, migrations.RunPython.noop)]
