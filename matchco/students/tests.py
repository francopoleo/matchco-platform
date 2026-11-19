from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import Course, Module, Subject
from documents.models import Document, DocumentLink
from documents.services import create_version

class StudentDocumentRenderingTests(TestCase):
    def test_linked_course_document_is_rendered_on_student_course_page(self):
        user = get_user_model().objects.create_superuser(username='student-doc-user', password='pass')
        subject = Subject.objects.create(title='Operações', slug='operacoes')
        course = Course.objects.create(
            title='Curso com documento', slug='curso-com-documento', subject=subject,
            overview='Descrição', state='published', published_date=timezone.now(), owner=user, author=user,
        )
        Module.objects.create(course=course, title='Módulo 1')
        document = Document.objects.create(
            title='Procedimento do curso', slug='procedimento-do-curso', status=Document.PUBLISHED, owner=user,
        )
        create_version(document, user, body='Procedimento vigente')
        DocumentLink.objects.create(
            document=document, content_type=ContentType.objects.get_for_model(Course),
            object_id=course.pk, created_by=user,
        )
        self.client.force_login(user)
        response = self.client.get(reverse('app:student_course_detail', kwargs={'pk': course.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Documentos do curso')
        self.assertContains(response, 'Procedimento do curso')
