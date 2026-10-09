from django.db import migrations


def add_supermarket_cashier(apps, schema_editor):
    Catalog = apps.get_model('recruitment', 'CanonicalCatalog')
    Term = apps.get_model('recruitment', 'CanonicalTerm')
    catalog = Catalog.objects.filter(
        code='market-default',
        version=1,
        status='published',
    ).first()
    if not catalog:
        return
    Term.objects.get_or_create(
        catalog=catalog,
        code='caixa-de-supermercado',
        defaults={
            'term_type': 'function',
            'label': 'Caixa de supermercado',
            'normalized_label': 'caixa de supermercado',
            'active': True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0051_seed_match_canonical_functions'),
    ]

    operations = [migrations.RunPython(add_supermarket_cashier, migrations.RunPython.noop)]
