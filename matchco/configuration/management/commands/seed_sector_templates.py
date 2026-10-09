from django.core.management.base import BaseCommand

from configuration.models import SectorTemplate


TEMPLATES = {
    'shopping': {
        'name': 'Shopping e território',
        'description': 'Lojas, operações terceirizadas, treinamento e comunicação do território.',
        'defaults': {'entry_template': 'shopping', 'roles': ['store_manager', 'salesperson', 'candidate'], 'purposes': ['recruitment', 'training', 'communication']},
    },
    'manufacturer': {
        'name': 'Fabricante e marca',
        'description': 'Fábrica, canais, distribuidores, revendas e varejo.',
        'defaults': {'entry_template': 'manufacturer', 'roles': ['manufacturer', 'distributor', 'reseller', 'technician', 'salesperson'], 'purposes': ['recruitment', 'training', 'certification', 'communication', 'partner_access']},
    },
    'pharma': {
        'name': 'Farmacêutica e ciências da vida',
        'description': 'Fábrica, representantes, distribuidores, farmácias e hospitais.',
        'defaults': {'entry_template': 'manufacturer', 'roles': ['manufacturer', 'distributor', 'reseller', 'technician', 'salesperson'], 'purposes': ['training', 'certification', 'communication', 'partner_access']},
    },
    'hospital': {
        'name': 'Hospital e rede clínica',
        'description': 'Unidades, departamentos, equipes clínicas e farmácia hospitalar.',
        'defaults': {'entry_template': 'hospital', 'roles': ['technician', 'it_manager', 'candidate'], 'purposes': ['recruitment', 'training', 'certification', 'communication']},
    },
    'retail': {
        'name': 'Varejo e rede de lojas',
        'description': 'Rede multiunidade com alto volume e operação distribuída.',
        'defaults': {'entry_template': 'retail', 'roles': ['retail_network', 'store_manager', 'salesperson', 'candidate'], 'purposes': ['recruitment', 'training', 'communication']},
    },
    'logistics': {
        'name': 'Logística e distribuição',
        'description': 'Centros de distribuição, transporte, hubs e parceiros.',
        'defaults': {'entry_template': 'distributor', 'roles': ['distributor', 'technician', 'candidate'], 'purposes': ['recruitment', 'training', 'certification', 'communication']},
    },
    'general': {
        'name': 'Empresa e organização geral',
        'description': 'Base neutra para adaptar qualquer organização.',
        'defaults': {'entry_template': 'generic', 'roles': ['candidate'], 'purposes': ['recruitment', 'training', 'communication']},
    },
}


class Command(BaseCommand):
    help = 'Cria ou atualiza presets de onboarding por mercado.'

    def handle(self, *args, **options):
        for code, data in TEMPLATES.items():
            SectorTemplate.objects.update_or_create(code=code, defaults=data)
        self.stdout.write(self.style.SUCCESS(f'{len(TEMPLATES)} templates setoriais disponíveis.'))
