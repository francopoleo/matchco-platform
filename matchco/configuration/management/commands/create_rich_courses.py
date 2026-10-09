"""
Create rich course content with images for all organizations.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.base import ContentFile
from pathlib import Path
import os
import unicodedata

from configuration.models import Organization
from courses.models import Course, Subject

class Command(BaseCommand):
    help = 'Create rich courses with images for all organizations'

    def get_image_files(self):
        """Get available image files from media/images and media/demo_assets"""
        images = {}
        media_path = Path('/Users/franco/Dev/matchco/matchco/media')

        # Get images from media/images
        if (media_path / 'images').exists():
            images['general'] = list((media_path / 'images').glob('*.jpg')) + list((media_path / 'images').glob('*.png'))

        # Get demo assets
        demo_assets = media_path / 'demo_assets'
        if demo_assets.exists():
            images['hospital'] = list((demo_assets / 'hospital').glob('*.png')) if (demo_assets / 'hospital').exists() else []
            images['insurance'] = list((demo_assets / 'insurance').glob('*.png')) if (demo_assets / 'insurance').exists() else []

        return images

    def handle(self, *args, **options):
        images = self.get_image_files()

        courses_config = {
            'hospital-demo': [
                {
                    'title': 'Segurança do Paciente Avançada',
                    'overview': 'Treinamento abrangente em segurança do paciente com casos reais',
                    'subject': 'Safety',
                },
                {
                    'title': 'Compliance HIPAA Completo',
                    'overview': 'Guia completo de conformidade HIPAA para profissionais de saúde',
                    'subject': 'Compliance',
                },
                {
                    'title': 'Atendimento Humanizado',
                    'overview': 'Técnicas de atendimento humanizado e empatia com pacientes',
                    'subject': 'Customer Service',
                },
                {
                    'title': 'Procedimentos de Emergência',
                    'overview': 'Protocolos e respostas rápidas para emergências médicas',
                    'subject': 'Safety',
                },
                {
                    'title': 'Equipamentos Médicos Modernos',
                    'overview': 'Treinamento prático em equipamentos médicos de última geração',
                    'subject': 'Product Training',
                },
            ],
            'seguradora-demo': [
                {
                    'title': 'Processamento de Sinistros Eficiente',
                    'overview': 'Metodologias modernas para agilizar processamento de sinistros',
                    'subject': 'Operations',
                },
                {
                    'title': 'Produtos de Seguro Completos',
                    'overview': 'Catálogo completo de produtos seguros com exemplos práticos',
                    'subject': 'Product Training',
                },
                {
                    'title': 'Conformidade Regulatória Seguros',
                    'overview': 'Legislação e conformidade para setor de seguros',
                    'subject': 'Compliance',
                },
                {
                    'title': 'Venda Consultiva',
                    'overview': 'Técnicas avançadas de venda consultiva e negociação',
                    'subject': 'Customer Service',
                },
                {
                    'title': 'Gestão de Risco',
                    'overview': 'Identificação e gestão de riscos em operações de seguros',
                    'subject': 'Safety',
                },
            ],
            'escola-demo': [
                {
                    'title': 'Ferramentas Digitais para Educadores',
                    'overview': 'Plataformas e ferramentas para educação digital moderna',
                    'subject': 'Product Training',
                },
                {
                    'title': 'Metodologias de Ensino Ativo',
                    'overview': 'Técnicas de aprendizagem ativa e engajamento estudantil',
                    'subject': 'Operations',
                },
                {
                    'title': 'Inclusão e Acessibilidade',
                    'overview': 'Garantindo educação inclusiva e acessível para todos',
                    'subject': 'Compliance',
                },
                {
                    'title': 'Avaliação Formativa',
                    'overview': 'Métodos modernos de avaliação e feedback estudantil',
                    'subject': 'Operations',
                },
            ],
            'manufatura-xyz': [
                {
                    'title': 'Segurança Industrial Completa',
                    'overview': 'Protocolo abrangente de segurança para ambientes industriais',
                    'subject': 'Safety',
                },
                {
                    'title': 'Operação de Máquinas CNC',
                    'overview': 'Treinamento prático em máquinas de controle numérico',
                    'subject': 'Product Training',
                },
                {
                    'title': 'Controle de Qualidade Six Sigma',
                    'overview': 'Métodos Six Sigma para controle de qualidade zero defeitos',
                    'subject': 'Operations',
                },
                {
                    'title': 'Manutenção Preventiva',
                    'overview': 'Programas de manutenção preventiva para máquinas',
                    'subject': 'Operations',
                },
                {
                    'title': 'Liderança na Fábrica',
                    'overview': 'Desenvolvimento de habilidades de liderança na produção',
                    'subject': 'Safety',
                },
            ],
            'retail-800': [
                {
                    'title': 'Atendimento ao Cliente Excelente',
                    'overview': 'Padrões de atendimento para 800 lojas com consistência',
                    'subject': 'Customer Service',
                },
                {
                    'title': 'Técnicas de Vendas Modernas',
                    'overview': 'Estratégias de venda consultiva e aumento de ticket médio',
                    'subject': 'Operations',
                },
                {
                    'title': 'Gestão de Estoque e Logística',
                    'overview': 'Otimização de estoque e logística para varejo',
                    'subject': 'Operations',
                },
                {
                    'title': 'Marca e Experiência do Cliente',
                    'overview': 'Criando experiências memoráveis alinhadas à marca',
                    'subject': 'Customer Service',
                },
                {
                    'title': 'Segurança e Compliance Retail',
                    'overview': 'Políticas de segurança e compliance para lojas',
                    'subject': 'Compliance',
                },
            ],
            'fintech-rapido': [
                {
                    'title': 'Segurança em Fintech',
                    'overview': 'Protocolos de segurança críticos para produtos fintech',
                    'subject': 'Safety',
                },
                {
                    'title': 'Conformidade Regulatória Fintech',
                    'overview': 'Navegando o landscape regulatório fintech complexo',
                    'subject': 'Compliance',
                },
                {
                    'title': 'Desenvolvimento de Produto',
                    'overview': 'Metodologias ágil para desenvolvimento de produtos fintech',
                    'subject': 'Product Training',
                },
                {
                    'title': 'Experiência do Usuário Fintech',
                    'overview': 'Design de UX/UI para aplicações fintech',
                    'subject': 'Operations',
                },
                {
                    'title': 'Fraude e Prevenção',
                    'overview': 'Detecção e prevenção de fraude em transações',
                    'subject': 'Safety',
                },
            ],
            'farmalab-biotech': [
                {
                    'title': 'Treinamento de Representante Médico',
                    'overview': 'Certificação completa para representantes de venda médica',
                    'subject': 'Product Training',
                },
                {
                    'title': 'Produtos Farmacêuticos Portfolio',
                    'overview': 'Conhecimento detalhado de toda a linha de produtos',
                    'subject': 'Product Training',
                },
                {
                    'title': 'Farmacovigilância e Segurança',
                    'overview': 'Protocolos de farmacovigilância e segurança de medicamentos',
                    'subject': 'Safety',
                },
                {
                    'title': 'Conformidade Regulatória FDA',
                    'overview': 'Entendendo e aplicando regulações FDA',
                    'subject': 'Compliance',
                },
                {
                    'title': 'Venda Consultiva Médica',
                    'overview': 'Técnicas de venda consultiva para médicos e hospitais',
                    'subject': 'Customer Service',
                },
                {
                    'title': 'Dados Clínicos e Ensaios',
                    'overview': 'Interpretando dados clínicos de ensaios farmacêuticos',
                    'subject': 'Product Training',
                },
            ],
        }

        for org_slug, org in [(o.slug, o) for o in Organization.objects.filter(is_public=False)]:
            courses = courses_config.get(org_slug, [])

            for idx, course_config in enumerate(courses):
                subject_title = course_config['subject']
                subject = Subject.objects.filter(title=subject_title).first()
                if not subject:
                    subject = Subject.objects.first()

                # Get image
                image_content = None
                if org_slug == 'hospital-demo' and images.get('hospital'):
                    img_path = images['hospital'][idx % len(images['hospital'])]
                elif org_slug == 'seguradora-demo' and images.get('insurance'):
                    img_path = images['insurance'][idx % len(images['insurance'])]
                elif images.get('general'):
                    img_path = images['general'][idx % len(images['general'])]
                else:
                    img_path = None

                if img_path and os.path.exists(img_path):
                    with open(img_path, 'rb') as f:
                        image_content = ContentFile(f.read(), name=img_path.name)

                # Create proper slug with ASCII characters only
                slug = slugify(f"{course_config['title']}-{org_slug}")

                course, created = Course.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'title': course_config['title'],
                        'overview': course_config['overview'],
                        'organization': org,
                        'subject': subject,
                        'state': 'published',
                        'type': 'course',
                        'published_date': timezone.now(),
                        'banner': image_content if image_content else None,
                    }
                )

                if created:
                    self.stdout.write(f'✅ Created: {course.title} ({org.name})')
                else:
                    self.stdout.write(f'⏭️  Exists: {course.title} ({org.name})')

            self.stdout.write(self.style.SUCCESS(f'✅ Cursos criados para {org.name}'))

        self.stdout.write(self.style.SUCCESS('\n✨ Rich courses created!'))
