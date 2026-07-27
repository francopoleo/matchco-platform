"""
Create modules and content for courses.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from courses.models import Course, Module, Content, Question, Answer, Quiz, Text, Video

User = get_user_model()

class Command(BaseCommand):
    help = 'Create modules and content for all courses'

    def handle(self, *args, **options):
        courses = Course.objects.filter(state='published')
        admin_user = User.objects.filter(is_staff=True).first()

        if not admin_user:
            self.stdout.write(self.style.ERROR('❌ Nenhum usuário admin encontrado!'))
            return

        text_content_type = ContentType.objects.get_for_model(Text)

        for idx, course in enumerate(courses):
            # Create 2-3 modules per course
            num_modules = 2 if idx % 3 == 0 else 3

            for mod_num in range(1, num_modules + 1):
                module, created = Module.objects.get_or_create(
                    course=course,
                    order=mod_num,
                    defaults={
                        'title': f'Módulo {mod_num}: {course.title.split()[0]}',
                        'description': f'Conteúdo prático do módulo {mod_num} de {course.title}',
                    }
                )

                if created:
                    # Create 2 text items per module
                    for text_num in range(1, 3):
                        text_item, _ = Text.objects.get_or_create(
                            owner=admin_user,
                            title=f'Aula {text_num}: {module.title}',
                        )

                        # Create Content reference
                        content, _ = Content.objects.get_or_create(
                            module=module,
                            content_type=text_content_type,
                            object_id=text_item.id,
                            order=text_num,
                        )

            self.stdout.write(f'✅ {num_modules} módulos criados para: {course.title}')

        self.stdout.write(self.style.SUCCESS(f'\n✨ Módulos criados para {courses.count()} cursos!'))
