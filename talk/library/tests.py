from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .models import ContentItem


class ContentItemValidationTests(SimpleTestCase):
    def test_text_requires_body(self):
        item = ContentItem(kind=ContentItem.TEXT)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_video_requires_url(self):
        item = ContentItem(kind=ContentItem.VIDEO)
        with self.assertRaises(ValidationError):
            item.full_clean()
