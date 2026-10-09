from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

from courses.models import Content, Course, Module, Subject, Text, Video
from configuration.models import (
    Organization, Company, BusinessUnit, OperationalUnit, BusinessChannel,
    JobFunction, Membership,
)


class Command(BaseCommand):
    help = 'Create repeatable demo courses with modules and learning content.'

    def handle(self, *args, **options):
        User = get_user_model()
        owner = User.objects.filter(is_superuser=True).first() or User.objects.order_by('id').first()
        if owner is None:
            self.stderr.write('No user exists to own the demo courses.')
            return

        organization, _ = Organization.objects.get_or_create(slug='matchco-learning', defaults={'name': 'MatchCo Learning'})
        company, _ = Company.objects.get_or_create(organization=organization, name='Demo Enterprise')
        business_unit, _ = BusinessUnit.objects.get_or_create(company=company, name='Learning Operations')
        operational_unit, _ = OperationalUnit.objects.get_or_create(
            business_unit=business_unit, name='Learning Campus'
        )
        channel, _ = BusinessChannel.objects.get_or_create(company=company, name='Corporate')
        function, _ = JobFunction.objects.get_or_create(company=company, name='Learner')
        function.channels.add(channel)
        membership, _ = Membership.objects.get_or_create(
            user=owner, organization=organization, company=company,
            business_unit=business_unit, operational_unit=operational_unit,
            defaults={'is_primary': True},
        )
        if not membership.is_primary or not membership.active:
            membership.is_primary = True
            membership.active = True
            membership.save(update_fields=['is_primary', 'active'])
        membership.channels.add(channel)
        membership.functions.add(function)

        subjects = {
            slug: Subject.objects.get_or_create(slug=slug, defaults={'title': title})[0]
            for slug, title in {
                'networking': 'Networking',
                'cloud': 'Cloud & Infrastructure',
                'security': 'Cybersecurity',
            }.items()
        }
        courses = [
            ('demo-network-fundamentals', 'Network Fundamentals', 'networking', 'Aprenda os fundamentos de redes, endereçamento IP, protocolos e troubleshooting para construir uma base sólida.', 'images/Redes.max-800x600.jpg', 40),
            ('demo-cloud-foundations', 'Cloud Foundations', 'cloud', 'Entenda os principais conceitos de cloud computing, arquitetura, serviços gerenciados e boas práticas de operação.', 'images/nuvem-computacao.width-800.jpg', 50),
            ('demo-cybersecurity-basics', 'Cybersecurity Basics', 'security', 'Conheça os fundamentos de segurança, riscos comuns e ações práticas para proteger ambientes digitais.', 'images/Protecao-ransomware.2e16d0ba.fill-800x450.jpg', 45),
        ]
        text_type = ContentType.objects.get_for_model(Text)
        video_type = ContentType.objects.get_for_model(Video)
        for slug, title, subject_slug, overview, banner, points in courses:
            course, _ = Course.objects.update_or_create(
                slug=slug,
                defaults={
                    'title': title,
                    'type': 'course',
                    'state': 'published',
                    'published_date': timezone.now(),
                    'banner': banner,
                    'author': owner,
                    'owner': owner,
                    'organization': organization,
                    'subject': subjects[subject_slug],
                    'overview': overview,
                    'points_per_completation': points,
                },
            )
            modules = [
                ('01', 'Getting started', 'Conheça os conceitos essenciais e prepare seu ambiente de estudo.'),
                ('02', 'Core concepts', 'Organize os conceitos principais em uma sequência prática.'),
                ('03', 'Practice lab', 'Aplique o conhecimento em cenários próximos da rotina.'),
            ]
            for index, (code, module_title, description) in enumerate(modules):
                module, _ = Module.objects.get_or_create(course=course, title=module_title, defaults={'description': description, 'order': index})
                module.description = description
                module.order = index
                module.save(update_fields=['description', 'order'])
                text, _ = Text.objects.get_or_create(owner=owner, title=f'{title} · {module_title}', defaults={'content': f'{description}\n\nEste conteúdo faz parte do curso demonstrativo {title}.'})
                content, _ = Content.objects.get_or_create(module=module, content_type=text_type, object_id=text.pk, defaults={'order': 0})
                text.content_type = content
                text.save(update_fields=['content_type'])
                video, _ = Video.objects.get_or_create(owner=owner, title=f'{title} · Lab {code}', defaults={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'content': 'Vídeo demonstrativo para apoiar a prática deste módulo.'})
                Content.objects.get_or_create(module=module, content_type=video_type, object_id=video.pk, defaults={'order': 1})
            self.stdout.write(self.style.SUCCESS(f'Course ready: {course.title}'))
