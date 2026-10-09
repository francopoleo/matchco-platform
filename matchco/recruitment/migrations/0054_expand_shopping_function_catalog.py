from django.db import migrations


FUNCTIONS = [
    ('vitrinista', 'Vitrinista'),
    ('visual-merchandising', 'Visual merchandising'),
    ('supervisor-de-loja', 'Supervisor de loja'),
    ('lider-de-loja', 'Líder de loja'),
    ('auxiliar-de-loja', 'Auxiliar de loja'),
    ('fiscal-de-loja', 'Fiscal de loja'),
    ('operador-de-caixa', 'Operador de caixa'),
    ('consultor-de-vendas', 'Consultor de vendas'),
    ('promotor-de-vendas', 'Promotor de vendas'),
    ('recepcionista', 'Recepcionista'),
    ('atendente-de-balcao', 'Atendente de balcão'),
    ('caixa-de-alimentacao', 'Caixa de alimentação'),
    ('garcom', 'Garçom / garçonete'),
    ('barista', 'Barista'),
    ('gerente-de-restaurante', 'Gerente de restaurante'),
    ('auxiliar-de-limpeza', 'Auxiliar de limpeza'),
    ('agente-de-seguranca', 'Agente de segurança'),
    ('controlador-de-acesso', 'Controlador de acesso'),
    ('operador-de-estacionamento', 'Operador de estacionamento'),
    ('manobrista', 'Manobrista'),
    ('tecnico-de-manutencao', 'Técnico de manutenção'),
    ('auxiliar-de-manutencao', 'Auxiliar de manutenção'),
]


ALIASES = {
    'vitrinista': ['vitrine', 'visual merchandising', 'vm'],
    'visual-merchandising': ['vm', 'vitrine', 'vitrinista'],
    'supervisor-de-loja': ['supervisão de loja', 'supervisor'],
    'lider-de-loja': ['líder', 'liderança de loja', 'encarregado de loja'],
    'auxiliar-de-loja': ['auxiliar de vendas', 'apoio de loja'],
    'fiscal-de-loja': ['fiscal', 'prevenção de perdas'],
    'operador-de-caixa': ['caixa', 'operadora de caixa', 'operador de caixa'],
    'consultor-de-vendas': ['consultor', 'vendas', 'vendedor'],
    'promotor-de-vendas': ['promotora', 'promotor', 'merchandising'],
    'atendente-de-balcao': ['balcão', 'atendimento de balcão'],
    'caixa-de-alimentacao': ['caixa de restaurante', 'caixa de lanchonete'],
    'garcom': ['garçon', 'garçonete', 'atendimento de mesa'],
    'auxiliar-de-limpeza': ['limpeza', 'serviços gerais'],
    'agente-de-seguranca': ['segurança', 'vigilante'],
    'controlador-de-acesso': ['portaria', 'controle de acesso'],
    'operador-de-estacionamento': ['estacionamento', 'caixa de estacionamento'],
    'tecnico-de-manutencao': ['manutenção', 'técnico'],
    'auxiliar-de-manutencao': ['manutenção', 'auxiliar técnico'],
}


def normalize(value):
    import unicodedata
    value = unicodedata.normalize('NFKD', value.lower())
    value = ''.join(char for char in value if not unicodedata.combining(char))
    return ' '.join(''.join(char if char.isalnum() else ' ' for char in value).split())


def seed_shopping_functions(apps, schema_editor):
    Catalog = apps.get_model('recruitment', 'CanonicalCatalog')
    Term = apps.get_model('recruitment', 'CanonicalTerm')
    Alias = apps.get_model('recruitment', 'CanonicalTermAlias')
    catalog = Catalog.objects.filter(
        code='market-default', version=1, status='published',
    ).first()
    if not catalog:
        return
    for code, label in FUNCTIONS:
        term, _ = Term.objects.get_or_create(
            catalog=catalog,
            code=code,
            defaults={
                'term_type': 'function',
                'label': label,
                'normalized_label': normalize(label),
                'active': True,
            },
        )
        for alias in ALIASES.get(code, []):
            Alias.objects.get_or_create(
                term=term,
                normalized_alias=normalize(alias),
                defaults={'alias': alias, 'source': 'system_default', 'active': True},
            )


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0053_seed_canonical_function_aliases'),
    ]

    operations = [migrations.RunPython(seed_shopping_functions, migrations.RunPython.noop)]
