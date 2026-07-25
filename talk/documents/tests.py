from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

from publishing.models import Publication

from .models import Document, DocumentPermission
from .services import can_download, can_view, create_version
from learning.models import NotificationRule, UserNotification


class DocumentVersionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='document-owner', password='test-pass')

    def test_published_document_version_announces_in_feed(self):
        document = Document.objects.create(
            title='Procedimento de segurança',
            slug='procedimento-seguranca',
            status=Document.PUBLISHED,
            owner=self.user,
        )
        version = create_version(document, self.user, body='Conteúdo vigente', change_summary='Publicação inicial')
        self.assertEqual(document.versions.count(), 1)
        self.assertEqual(document.current_version_id, version.pk)
        self.assertTrue(Publication.objects.filter(slug='procedimento-seguranca-v1').exists())

    def test_second_version_preserves_history_and_announces_update(self):
        document = Document.objects.create(
            title='Manual operacional', slug='manual-operacional', status=Document.PUBLISHED, owner=self.user,
        )
        first = create_version(document, self.user, body='v1')
        second = create_version(document, self.user, body='v2', change_summary='Atualização de fluxo')
        first.refresh_from_db()
        self.assertEqual(second.version_number, 2)
        self.assertIsNotNone(first.superseded_at)
        self.assertTrue(Publication.objects.filter(slug='manual-operacional-v2').exists())

    def test_explicit_permission_controls_download(self):
        document = Document.objects.create(title='Acesso restrito', slug='acesso-restrito', status=Document.PUBLISHED, owner=self.user)
        create_version(document, self.user, body='Conteúdo privado')
        viewer = get_user_model().objects.create_user(username='viewer', password='test-pass')
        DocumentPermission.objects.create(document=document, user=viewer, can_view=True, can_download=False)
        self.assertTrue(can_view(viewer, document))
        self.assertFalse(can_download(viewer, document))

    def test_notification_rule_is_applied_when_document_is_published(self):
        NotificationRule.objects.create(
            name='Avisar publicação de procedimento',
            trigger_type=NotificationRule.DOCUMENT_PUBLISHED,
            condition={'category': 'procedure'},
            action={'title': 'Novo procedimento', 'priority': UserNotification.CRITICAL},
            created_by=self.user,
        )
        document = Document.objects.create(
            title='Procedimento com regra', slug='procedimento-com-regra', category='procedure',
            status=Document.PUBLISHED, owner=self.user,
        )
        create_version(document, self.user, body='Conteúdo', change_summary='Publicação inicial')
        self.assertTrue(UserNotification.objects.filter(user=self.user, title='Novo procedimento').exists())

    def test_expired_current_version_is_not_available(self):
        document = Document.objects.create(
            title='Documento vencido', slug='documento-vencido', status=Document.PUBLISHED, owner=self.user,
        )
        create_version(document, self.user, body='Conteúdo', expires_at=timezone.now() - timedelta(minutes=1))
        document.refresh_from_db()
        self.assertTrue(document.is_expired)
        self.assertFalse(document.is_available)

    def test_upload_extension_is_validated(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        document = Document.objects.create(title='Arquivo', slug='arquivo', owner=self.user)
        upload = SimpleUploadedFile('script.exe', b'bad')
        with self.assertRaises(ValidationError):
            create_version(document, self.user, file=upload)
