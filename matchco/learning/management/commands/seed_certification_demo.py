from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django_tenants.utils import get_tenant_model, schema_context

from courses.models import Course
from learning.models import Certification, CertificationRequirement
from tenants_core.models import TenantOrganization, TenantUser


CERTIFICATIONS = {
    'bourbon-shopping': {
        'title': 'Operação segura no Bourbon Shopping',
        'slug': 'operacao-segura-bourbon-shopping',
        'description': 'Certificação demonstrativa para atendimento, conduta e operação segura nas lojas e serviços do shopping.',
        'courses': ('fundamentos-de-atendimento-ao-cliente', 'politicas-e-codigo-de-conduta'),
    },
    'drogasil-rede': {
        'title': 'Atendimento responsável Drogasil',
        'slug': 'atendimento-responsavel-drogasil',
        'description': 'Certificação demonstrativa para atendimento responsável, privacidade, qualidade e rotinas de farmácia.',
        'courses': ('drogasil-rede-boas-praticas-de-atendimento-em-farmacia', 'drogasil-rede-operacao-de-loja-e-dispensacao-responsavel'),
    },
}


class Command(BaseCommand):
    help = 'Cria certificações completas de demonstração para Bourbon e Drogasil.'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', choices=sorted(CERTIFICATIONS))

    def handle(self, *args, **options):
        tenants = [options['tenant']] if options.get('tenant') else list(CERTIFICATIONS)
        TenantModel = get_tenant_model()
        for schema_name in tenants:
            tenant = TenantModel.objects.filter(schema_name=schema_name).first()
            if not tenant:
                self.stdout.write(self.style.WARNING(f'{schema_name}: tenant não encontrado.'))
                continue
            data = CERTIFICATIONS[schema_name]
            with schema_context(schema_name):
                organization, _ = TenantOrganization.objects.get_or_create(organization_id=tenant.pk, defaults={'name': tenant.name, 'slug': tenant.slug})
                owner = TenantUser.objects.order_by('user_id').first()
                if not owner:
                    self.stdout.write(self.style.WARNING(f'{schema_name}: usuário responsável não encontrado.'))
                    continue
                certification, _ = Certification.objects.update_or_create(
                    organization=organization, slug=data['slug'],
                    defaults={'title': data['title'], 'description': data['description'], 'status': Certification.PUBLISHED, 'version': '1.0', 'validity_days': 365, 'minimum_score': 70, 'maximum_attempts': 3, 'minimum_active_seconds': 1800, 'requires_manual_approval': False, 'created_by': owner},
                )
                certification.requirements.all().delete()
                courses = Course.objects.filter(slug__in=data['courses']).order_by('slug')
                for position, course in enumerate(courses, 1):
                    CertificationRequirement.objects.create(certification=certification, course=course, position=position, required=True)
                self.stdout.write(self.style.SUCCESS(f'{schema_name}: {certification.title} · {courses.count()} requisitos'))
