from django.test import SimpleTestCase, TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone

from .models import Publication
from documents.models import Document, DocumentLink
from documents.services import create_version


class PublicationModelTests(SimpleTestCase):
    def test_publication_is_not_published_without_date(self):
        publication = Publication(status=Publication.PUBLISHED)
        self.assertFalse(publication.is_published)

    def test_publication_is_published_with_status_and_date(self):
        from django.utils import timezone

        publication = Publication(status=Publication.PUBLISHED, published_at=timezone.now())
        self.assertTrue(publication.is_published)


class PublicationDocumentRenderingTests(TestCase):
    def test_linked_document_is_rendered_on_publication_detail(self):
        user = get_user_model().objects.create_superuser(username='publication-doc-user', password='pass')
        publication = Publication.objects.create(
            kind=Publication.WIKI, title='Wiki com documento', slug='wiki-com-documento',
            body='Conteúdo', author=user, status=Publication.PUBLISHED, published_at=timezone.now(),
        )
        document = Document.objects.create(
            title='Manual relacionado', slug='manual-relacionado', status=Document.PUBLISHED, owner=user,
        )
        create_version(document, user, body='Manual vigente')
        DocumentLink.objects.create(
            document=document, content_type=ContentType.objects.get_for_model(Publication),
            object_id=publication.pk, created_by=user,
        )
        self.client.force_login(user)
        response = self.client.get(reverse('publication_detail', kwargs={'slug': publication.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Documentos relacionados')
        self.assertContains(response, 'Manual relacionado')
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from learning.models import ContentEvent

from .models import ContentQuestion, Publication


class ContentQuestionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='question-user', password='pass')
        self.user.is_superuser = True
        self.user.save(update_fields=('is_superuser',))
        self.publication = Publication.objects.create(
            kind=Publication.WIKI,
            title='Manual de teste',
            slug='manual-de-teste',
            body='Conteúdo',
            author=self.user,
            status=Publication.PUBLISHED,
            published_at=timezone.now(),
        )

    def test_private_question_creates_event_and_recommendation_flow(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('content_question'), {
            'publication_id': self.publication.pk,
            'question': 'Como aplico este procedimento?',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ContentQuestion.objects.filter(user=self.user).exists())
        self.assertTrue(ContentEvent.objects.filter(event_name=ContentEvent.QUESTION_SUBMITTED).exists())
