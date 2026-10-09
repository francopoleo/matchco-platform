from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import connection, transaction
from django.core.management.sql import sql_flush
from django.core.management.color import no_style
from django.utils import timezone
from django.utils.text import slugify
from django_tenants.utils import schema_context

from configuration.models import Organization, Domain, Membership
from tenants_core.models import TenantUser, TenantOrganization
from courses.models import Subject, Course, Module, Content, Text, Quiz
from publishing.models import Publication
from documents.models import Document
from audience.models import AudiencePolicy, AudienceRule
from learning.models import ContentTrail, TrailStep
from gamification.models import GamificationSettings


class Command(BaseCommand):
    help = 'Compatibilidade histórica: limpe dados usando reset_matchco_development.'

    ORGS = (
        ('bourbon-shopping', 'Bourbon Shopping'),
        ('shopping-xyz', 'Shopping XYZ'),
        ('hospital-abc', 'Hospital ABC'),
        ('seguradora-xyz', 'Seguradora XYZ'),
    )

    def add_arguments(self, parser):
        parser.add_argument('--reset-only', action='store_true')
        parser.add_argument('--yes', action='store_true')
        parser.add_argument('--admin-password', default='admin')

    def handle(self, *args, **options):
        if not options['yes']:
            raise CommandError('Operação destrutiva. Execute com --yes.')
        if not options['reset_only']:
            raise CommandError(
                'Seed misto desativado. Use reset_matchco_development --yes '
                '--seed-recruitment --seed-content.'
            )
        self.reset()
        self.stdout.write(self.style.SUCCESS('Schemas de conteúdo e usuários limpos.'))

    def reset(self):
        orgs = list(Organization.objects.filter(is_public=False))
        for org in orgs:
            with schema_context(org.schema_name):
                connection.ops.execute_sql_flush(
                    sql_flush(no_style(), connection, reset_sequences=True, allow_cascade=True)
                )
        # Keep tenant rows/schemas so django-tenants can continue routing them.
        # User relations span shared and tenant apps; ORM cascades can try to
        # inspect tenant-only tables while the connection is on public.
        # PostgreSQL cascade clears the shared dependency graph safely.
        with connection.cursor() as cursor:
            cursor.execute('TRUNCATE TABLE %s CASCADE' % connection.ops.quote_name(get_user_model()._meta.db_table))
        # Domains are routing configuration, not demo content. Keep them so
        # reset does not make localhost or the development host return 404.
        for org in orgs:
            org.active = False
            org.save(update_fields=['active'])

    @transaction.atomic
    def seed(self, password):
        User = get_user_model()
        admin, _ = User.objects.update_or_create(
            username='admin',
            defaults={'email': 'admin@matchco.local', 'is_staff': True, 'is_superuser': True, 'is_active': True},
        )
        admin.set_password(password)
        admin.save()
        for slug, name in self.ORGS:
            org = Organization.objects.filter(slug=slug).first()
            if not org:
                raise CommandError(f'Organização {slug} não existe; crie o schema antes do seed.')
            org.name, org.active, org.is_public = name, True, False
            org.save(update_fields=['name', 'active', 'is_public'])
            Membership.objects.update_or_create(user=admin, organization=org, defaults={'role': 'admin', 'active': True, 'is_primary': slug == 'bourbon-shopping'})
            with schema_context(org.schema_name):
                tenant_org, _ = TenantOrganization.objects.update_or_create(
                    organization_id=org.id, defaults={'name': name, 'slug': slug}
                )
                tenant_user, _ = TenantUser.objects.update_or_create(
                    user_id=admin.id, defaults={'username': admin.username, 'email': admin.email, 'is_active': True}
                )
                GamificationSettings.objects.update_or_create(
                    pk=1,
                    defaults={
                        'description': f'Configuração demo - {name}',
                        'ap_course_enrollment': True,
                        'dp_course_enrollment': 5,
                        'ap_course_completation': True,
                        'dp_course_completation': 100,
                        'ap_passed_tests': True,
                        'dp_passed_tests': 25,
                    },
                )
                subject, _ = Subject.objects.get_or_create(title='Integração e Compliance', defaults={'slug': f'{slug}-compliance'})
                for index, title in enumerate(('Boas práticas e segurança', 'Atendimento e operação'), 1):
                    course, _ = Course.objects.update_or_create(
                        slug=f'{slug}-course-{index}',
                        defaults={'title': title, 'type': 'course', 'state': 'published', 'published_date': timezone.now(), 'overview': f'Conteúdo de teste para {name}.', 'owner': tenant_user, 'author': tenant_user, 'organization': tenant_org, 'subject': subject},
                    )
                    module, _ = Module.objects.get_or_create(course=course, title='Módulo inicial', defaults={'description': 'Módulo demonstrativo'})
                    text, _ = Text.objects.get_or_create(owner=tenant_user, title=f'{title} - introdução', defaults={'content': 'Conteúdo demonstrativo do ambiente de testes.'})
                    ct = ContentType.objects.get_for_model(Text)
                    Content.objects.get_or_create(module=module, content_type=ct, object_id=text.id)
                    quiz, _ = Quiz.objects.get_or_create(owner=tenant_user, title=f'{title} - avaliação', organization=tenant_org, defaults={'required_score_to_pass': 70, 'overview': 'Avaliação demonstrativa.'})
                    Content.objects.get_or_create(module=module, content_type=ContentType.objects.get_for_model(Quiz), object_id=quiz.id)
                policy, _ = AudiencePolicy.objects.get_or_create(name=f'{name} - todos', organization=tenant_org, defaults={'active': True})
                AudienceRule.objects.get_or_create(policy=policy, dimension=AudienceRule.TENANT, values=[str(org.id)])
                Publication.objects.get_or_create(slug=f'{slug}-feed-1', defaults={'kind': Publication.FEED, 'organization': tenant_org, 'title': f'Comunicado {name}', 'body': 'Publicação demonstrativa.', 'author': tenant_user, 'status': Publication.PUBLISHED, 'published_at': timezone.now(), 'audience_policy': policy})
                Document.objects.get_or_create(slug=f'{slug}-manual-1', defaults={'organization': tenant_org, 'title': f'Manual {name}', 'code': f'{slug.upper()}-001', 'description': 'Documento demonstrativo.', 'owner': tenant_user, 'status': Document.PUBLISHED, 'published_at': timezone.now(), 'audience_policy': policy})
                trail, _ = ContentTrail.objects.get_or_create(slug=f'{slug}-trail-1', defaults={'organization': tenant_org, 'title': f'Trilha {name}', 'objective': 'Trilha demonstrativa.', 'status': ContentTrail.PUBLISHED, 'owner': tenant_user, 'audience_policy': policy})
                trail.steps.get_or_create(position=1, title='Concluir o curso', content_type=ContentType.objects.get_for_model(Course), object_id=course.id)
