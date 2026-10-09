import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not await self._has_controlled_access():
            await self.close(code=4403)
            return
        self.id = self.scope['url_route']['kwargs']['course_id']
        self.room_group_name = 'chat_%s' % self.id
        # join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        # accept connection
        await self.accept()

    @database_sync_to_async
    def _has_controlled_access(self):
        """Talk only opens after a manager-approved active membership."""
        if not getattr(self.user, 'is_authenticated', False):
            return False
        active_org = getattr(self.user, '_active_organization_id', None)
        try:
            from configuration.models import Membership
            memberships = Membership.objects.filter(user=self.user, active=True)
            if active_org:
                memberships = memberships.filter(organization_id=active_org)
            if memberships.exists():
                return True
        except Exception:
            pass
        from recruitment.models import ControlledAccessRequest
        requests = ControlledAccessRequest.objects.filter(
            user_id=self.user.pk,
            state=ControlledAccessRequest.STATE_ACTIVE,
        )
        if active_org:
            from recruitment.domain_models import RecruitmentPlatformBinding
            requests = requests.filter(
                organization__platform_bindings__platform_organization_id=active_org,
                organization__platform_bindings__active=True,
            )
        return requests.exists()

    async def disconnect(self, close_code):
        # leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        now = timezone.now()

        await self._record_talk_interaction(len(message or ''))

        # send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': self.user.username,
                'datetime': now.isoformat(),
            }
        )

    @database_sync_to_async
    def _record_talk_interaction(self, message_length):
        """Persist metadata and emit a consent-gated MatchCo signal."""
        from .models import TalkInteraction
        if not getattr(self.user, 'is_authenticated', False):
            return
        organization_id = getattr(self.user, '_active_organization_id', None)
        if not organization_id:
            return
        event = TalkInteraction.objects.create(
            user=self.user,
            platform_organization_id=organization_id,
            room_key=str(self.id),
            message_length=message_length,
        )
        from recruitment.domain_models import RecruitmentPlatformBinding
        binding = RecruitmentPlatformBinding.objects.filter(
            platform_organization_id=organization_id, active=True,
        ).select_related('recruitment_organization').first()
        if not binding:
            return
        from recruitment.models import CandidateProfile
        from recruitment.integrations.signals import on_talk_interaction
        profile = CandidateProfile.objects.filter(
            email__iexact=getattr(self.user, 'email', ''),
            organization=binding.recruitment_organization,
        ).first()
        if not profile:
            return
        try:
            from courses.models import Course
            course = Course.objects.filter(pk=self.id).values_list('title', flat=True).first()
            course_title = course or 'Talk'
            topic_name = f'Talk: {course_title}'
        except Exception:
            topic_name = 'Talk'
        from recruitment.services import resolve_platform_context
        on_talk_interaction(
            candidate_id=profile.pk,
            topic_key=f'course-{self.id}:{event.topic_key}',
            topic_name=topic_name,
            message_length=message_length,
            platform_context=resolve_platform_context(
                organization=binding.recruitment_organization,
            ),
        )

    # receive message from room group
    async def chat_message(self, event):
        # send message to WebSocket
        await self.send(text_data=json.dumps(event))
