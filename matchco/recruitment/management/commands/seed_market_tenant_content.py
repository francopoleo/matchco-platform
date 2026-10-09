"""Seed a small, organization-scoped content starter for a market demo."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from django_tenants.utils import get_tenant_model, schema_context
from django.contrib.contenttypes.models import ContentType

from courses.models import Content, Course, Module, Subject, Text
from documents.models import Document, DocumentVersion
from publishing.models import Publication
from tenants_core.models import TenantOrganization, TenantUser


MARKET_CONTENT = {
    'pharma': {
        'label': 'Drogasil',
        'courses': [('Boas práticas de atendimento em farmácia', 'Atendimento responsável, comunicação clara e relacionamento seguro com clientes.'), ('Operação de loja e dispensação responsável', 'Rotinas de loja, organização, privacidade e encaminhamento responsável.')],
        'feeds': [('Comunicado de qualidade Drogasil', 'Atualização demonstrativa sobre boas práticas e registro de ocorrências.'), ('Agenda de treinamento da rede', 'Próximas capacitações para lojas e gestores.')],
        'docs': [('Política de qualidade Drogasil', 'Princípios de qualidade, rastreabilidade e segurança.'), ('Guia da loja Drogasil', 'Rotinas para atendimento, organização e comunicação responsável.')],
    },
    'manufacturer': {
        'label': 'ElectraTech',
        'courses': [('Academia de produto eletrônico', 'Conhecimento de produto, demonstração de valor e suporte ao canal.'), ('Operação de assistência técnica', 'Triagem, diagnóstico, segurança e experiência do consumidor.')],
        'feeds': [('Lançamento de produto', 'Conteúdo demonstrativo para preparar revendas e assistência técnica.'), ('Campanha de sell-out', 'Orientações de ativação para parceiros e equipes de loja.')],
        'docs': [('Manual de produto', 'Especificações, posicionamento e perguntas frequentes.'), ('Política de assistência técnica', 'Critérios de atendimento, garantia e encaminhamento.')],
    },
}


class Command(BaseCommand):
    help = 'Cria cursos, feed e documentos dentro do tenant de uma demo de mercado.'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', required=True)
        parser.add_argument('--market', required=True, choices=sorted(MARKET_CONTENT))

    def handle(self, *args, **options):
        tenant = get_tenant_model().objects.get(schema_name=options['tenant'])
        data = MARKET_CONTENT[options['market']]
        with schema_context(tenant.schema_name):
            owner = TenantUser.objects.order_by('user_id').first()
            if not owner:
                public_user = get_user_model().objects.order_by('id').first()
                if not public_user:
                    self.stdout.write(self.style.WARNING(f'{tenant.schema_name}: nenhum usuário para atribuir conteúdo.'))
                    return
                owner = TenantUser.objects.create(user_id=public_user.pk, username=public_user.username, email=public_user.email, first_name=public_user.first_name, last_name=public_user.last_name, is_active=public_user.is_active)
            organization, _ = TenantOrganization.objects.get_or_create(organization_id=tenant.pk, defaults={'name': tenant.name, 'slug': tenant.slug})
            subject, _ = Subject.objects.get_or_create(slug=f"{tenant.schema_name}-academy", defaults={'title': f"{data['label']} · Academia"})
            text_type = ContentType.objects.get_for_model(Text)
            for course_title, overview in data['courses']:
                course, _ = Course.objects.get_or_create(slug=f"{tenant.schema_name}-{slugify(course_title)}", defaults={'title': course_title, 'overview': overview, 'state': 'published', 'owner': owner, 'author': owner, 'organization': organization, 'subject': subject})
                course.overview = overview; course.state = 'published'; course.organization = organization; course.subject = subject; course.save(update_fields=['overview', 'state', 'organization', 'subject'])
                module, _ = Module.objects.get_or_create(course=course, title='Trilha principal', defaults={'description': overview, 'order': 1})
                text, _ = Text.objects.get_or_create(owner=owner, title=f'{course.title} · Trilha principal', defaults={'content': f'<h2>{course_title}</h2><p>{overview}</p><p>Conteúdo demonstrativo organizado por audiência e função.</p>'})
                Content.objects.get_or_create(module=module, content_type=text_type, object_id=text.pk, defaults={'order': 1})
            for title, body in data['feeds']:
                Publication.objects.get_or_create(slug=f"{tenant.schema_name}-{slugify(title)}", defaults={'kind': Publication.FEED, 'organization': organization, 'title': title, 'excerpt': body, 'body': f'<p>{body}</p>', 'author': owner, 'status': Publication.PUBLISHED, 'published_at': timezone.now()})
            for title, description in data['docs']:
                doc, _ = Document.objects.get_or_create(slug=f"{tenant.schema_name}-{slugify(title)}", defaults={'organization': organization, 'owner': owner, 'title': title, 'description': description, 'status': Document.PUBLISHED, 'published_at': timezone.now()})
                version, _ = DocumentVersion.objects.get_or_create(document=doc, version_number=1, defaults={'body': f'<h2>{title}</h2><p>{description}</p>', 'created_by': owner, 'effective_at': timezone.now()})
                if doc.current_version_id != version.pk:
                    doc.current_version = version; doc.save(update_fields=['current_version', 'updated_at'])
        self.stdout.write(self.style.SUCCESS(f'{tenant.schema_name}: conteúdo {data["label"]} criado.'))
