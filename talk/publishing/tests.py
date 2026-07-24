from django.test import SimpleTestCase

from .models import Publication


class PublicationModelTests(SimpleTestCase):
    def test_publication_is_not_published_without_date(self):
        publication = Publication(status=Publication.PUBLISHED)
        self.assertFalse(publication.is_published)

    def test_publication_is_published_with_status_and_date(self):
        from django.utils import timezone

        publication = Publication(status=Publication.PUBLISHED, published_at=timezone.now())
        self.assertTrue(publication.is_published)
