from django.db import migrations


ALIASES = {
    'estoquista-de-loja': ['estoque', 'estoquista', 'reposição', 'repositor'],
    'repositor-de-loja': ['reposição', 'repositor', 'abastecimento'],
    'vendedor-de-loja': ['vendas', 'vendedor', 'vendedora'],
    'atendimento-de-loja': ['atendimento', 'atender cliente'],
    'caixa-de-loja': ['caixa', 'operador de caixa', 'operadora de caixa'],
    'caixa-de-supermercado': ['caixa', 'operador de caixa', 'operadora de caixa'],
    'balconista-de-farmacia': ['balcão', 'balconista', 'atendimento de balcão'],
}


def normalize(value):
    import unicodedata
    value = unicodedata.normalize('NFKD', value.lower())
    value = ''.join(char for char in value if not unicodedata.combining(char))
    return ' '.join(''.join(char if char.isalnum() else ' ' for char in value).split())


def seed_aliases(apps, schema_editor):
    Catalog = apps.get_model('recruitment', 'CanonicalCatalog')
    Term = apps.get_model('recruitment', 'CanonicalTerm')
    Alias = apps.get_model('recruitment', 'CanonicalTermAlias')
    catalog = Catalog.objects.filter(
        code='market-default', version=1, status='published',
    ).first()
    if not catalog:
        return
    for code, aliases in ALIASES.items():
        term = Term.objects.filter(catalog=catalog, code=code, active=True).first()
        if not term:
            continue
        for alias in aliases:
            Alias.objects.get_or_create(
                term=term,
                normalized_alias=normalize(alias),
                defaults={'alias': alias, 'source': 'system_default', 'active': True},
            )


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0052_add_retail_cashier_function'),
    ]

    operations = [migrations.RunPython(seed_aliases, migrations.RunPython.noop)]
