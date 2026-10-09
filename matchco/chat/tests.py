from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import TalkInteraction


class TalkInteractionTests(TestCase):
    def test_only_minimal_talk_metadata_is_persisted(self):
        user = get_user_model().objects.create_user(
            username='talk-user', email='talk@example.com', password='secret',
        )
        event = TalkInteraction.objects.create(
            user=user, platform_organization_id=42,
            room_key='course-7', message_length=18,
        )

        self.assertEqual(event.message_length, 18)
        self.assertFalse(hasattr(event, 'message'))

# Create your tests here.
