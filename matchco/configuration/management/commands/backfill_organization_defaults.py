from django.core.management.base import BaseCommand

from configuration.models import Organization


class Command(BaseCommand):
    help = 'Preenche mercado e template padrão dos tenants legados sem substituir branding customizado.'

    MARKET_BY_SLUG = {
        'bourbon-shopping': Organization.MARKET_SHOPPING,
        'shopping-xyz': Organization.MARKET_SHOPPING,
        'hospital-abc': Organization.MARKET_HOSPITAL,
        'seguradora-xyz': Organization.MARKET_PHARMA,
    }

    TEMPLATE_BY_MARKET = {
        Organization.MARKET_SHOPPING: 'shopping',
        Organization.MARKET_HOSPITAL: 'hospital',
        Organization.MARKET_PHARMA: 'manufacturer',
    }

    def handle(self, *args, **options):
        updated = 0
        for organization in Organization.objects.filter(active=True).order_by('slug'):
            market = self.MARKET_BY_SLUG.get(organization.slug, organization.market)
            template = self.TEMPLATE_BY_MARKET.get(market, organization.default_entry_template or 'generic')
            changes = []
            if organization.market == Organization.MARKET_GENERAL and market != Organization.MARKET_GENERAL:
                organization.market = market
                changes.append('market')
            if not organization.default_entry_template or organization.default_entry_template == 'generic':
                organization.default_entry_template = template
                changes.append('default_entry_template')
            if changes:
                organization.save(update_fields=changes)
                updated += 1
                self.stdout.write(f'{organization.slug}: {", ".join(changes)}')
        self.stdout.write(self.style.SUCCESS(f'{updated} organizações atualizadas.'))
