from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, schema_context

from courses.models import Course, Module, Text, Video
from publishing.models import Publication
from documents.services import sync_media_usage


CONTENT_SOURCES = (
    (Publication, 'body', 'author'),
    (Course, 'overview', 'owner'),
    (Module, 'description', 'owner'),
    (Text, 'content', 'owner'),
    (Video, 'content', 'owner'),
)


class Command(BaseCommand):
    help = 'Reconstrói os vínculos entre mídias protegidas e Feed, Wiki e cursos existentes.'

    def handle(self, *args, **options):
        contents = usages = 0
        for tenant in get_tenant_model().objects.exclude(schema_name='public'):
            with schema_context(tenant.schema_name):
                for model, field_name, actor_field in CONTENT_SOURCES:
                    for obj in model.objects.all().iterator():
                        actor = getattr(obj, actor_field, None)
                        usages += sync_media_usage(obj, getattr(obj, field_name, '') or '', actor=actor, field_name=field_name)
                        contents += 1
        self.stdout.write(self.style.SUCCESS(f'{contents} conteúdo(s) verificado(s); {usages} vínculo(s) reconstruído(s).'))
