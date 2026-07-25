import json

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.core import mail
from django.db.models import Sum
from django.urls import reverse

from .models import ContentEvent, PointLedger, UserNotificationPreference
from configuration.models import Company, Membership, Organization, Partner, PartnerMembership, WebhookDelivery, WebhookSubscription
from .services import track_event
from .services import calculate_progress


class ProgressCalculationTests(SimpleTestCase):
    def test_empty_course_has_zero_progress(self):
        self.assertEqual(calculate_progress(0, 0), 0)

    def test_progress_is_percentage(self):
        self.assertEqual(calculate_progress(4, 1), 25)

    def test_progress_never_exceeds_one_hundred(self):
        self.assertEqual(calculate_progress(2, 3), 100)


class OperationalActionEventTests(TestCase):
    def test_action_event_is_recorded(self):
        user = get_user_model().objects.create_user(username='action-user', password='pass')
        self.client.force_login(user)
        response = self.client.post(
            reverse('learning-action-event'),
            data=json.dumps({'action_type': 'checklist_completed', 'reference': 'CASE-42'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ContentEvent.objects.filter(user=user, event_name=ContentEvent.ACTION_COMPLETED).exists())
        self.assertEqual(PointLedger.objects.filter(user=user).aggregate(total=Sum('points'))['total'], 20)


class MobileAndAnalyticsApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='mobile-admin', password='pass', email='mobile@example.com',
        )
        self.client.force_login(self.user)

    def test_mobile_sync_returns_contract(self):
        response = self.client.get('/api/mobile/sync/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('documents', response.json())
        self.assertIn('sync_complete_at', response.json())

    def test_pwa_service_worker_is_available_at_root_scope(self):
        response = self.client.get('/service-worker.js')
        self.assertEqual(response.status_code, 200)
        self.assertIn('CACHE_NAME', response.content.decode())

    def test_mobile_events_accept_empty_batch(self):
        response = self.client.post('/api/mobile/events/', data=json.dumps({'events': []}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['accepted'], 0)

    def test_engagement_api_requires_manager_and_returns_aggregate(self):
        response = self.client.get(reverse('learning_api:analytics-engagement'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('by_event', response.json())

    def test_gamification_summary_returns_points_and_badges(self):
        response = self.client.get(reverse('learning_api:gamification-summary'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('points', response.json())

    def test_leaderboard_is_scoped_to_selected_organization(self):
        first = get_user_model().objects.create_user(username='leader-first', password='pass')
        second = get_user_model().objects.create_user(username='leader-second', password='pass')
        organization = Organization.objects.create(name='Leaderboard Tenant', slug='leaderboard-tenant')
        company = Company.objects.create(organization=organization, name='Leaderboard Company')
        Membership.objects.create(user=first, organization=organization, company=company, active=True)
        Membership.objects.create(user=second, organization=organization, company=company, active=True)
        PointLedger.objects.create(user=first, organization=organization, points=40, reason='test')
        PointLedger.objects.create(user=second, organization=organization, points=10, reason='test')
        response = self.client.get(reverse('learning_api:gamification-leaderboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['display_name'] for item in response.json()['entries']], ['leader-first', 'leader-second'])

    def test_api_key_uses_its_tenant_without_browser_session(self):
        organization = Organization.objects.create(name='Credential Tenant', slug='credential-tenant')
        other = Organization.objects.create(name='Other Tenant', slug='other-tenant')
        company = Company.objects.create(organization=organization, name='Credential Company')
        Membership.objects.create(user=self.user, organization=organization, company=company, active=True)
        from configuration.models import IntegrationCredential
        credential, raw_key = IntegrationCredential.issue(
            organization=organization, name='tenant key', created_by=self.user,
            scopes=['gamification:read'],
        )
        PointLedger.objects.create(user=self.user, organization=organization, points=30, reason='tenant')
        PointLedger.objects.create(user=self.user, organization=other, points=90, reason='other')
        self.client.logout()
        response = self.client.get(reverse('learning_api:gamification-leaderboard'), HTTP_X_TALK_API_KEY=raw_key)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['organization_id'], organization.pk)
        self.assertEqual(response.json()['current_user']['points'], 30)

    def test_api_key_cannot_read_document_from_another_tenant(self):
        from configuration.models import IntegrationCredential
        from documents.models import Document
        from documents.services import create_version
        organization = Organization.objects.create(name='Document Tenant', slug='document-tenant')
        other = Organization.objects.create(name='Hidden Document Tenant', slug='hidden-document-tenant')
        credential, raw_key = IntegrationCredential.issue(
            organization=organization, name='documents key', created_by=self.user,
            scopes=['documents:read'],
        )
        visible = Document.objects.create(title='Visible', slug='visible-api-document', organization=organization, status=Document.PUBLISHED, owner=self.user)
        hidden = Document.objects.create(title='Hidden', slug='hidden-api-document', organization=other, status=Document.PUBLISHED, owner=self.user)
        create_version(visible, self.user, body='visible')
        create_version(hidden, self.user, body='hidden')
        self.client.logout()
        response = self.client.get(reverse('learning_api:document-detail', kwargs={'pk': hidden.pk}), HTTP_X_TALK_API_KEY=raw_key)
        self.assertEqual(response.status_code, 404)

    def test_document_api_updates_metadata_and_archives_without_deleting_history(self):
        from configuration.models import IntegrationCredential
        from documents.models import Document
        from documents.services import create_version
        organization = Organization.objects.create(name='Document Write Tenant', slug='document-write-tenant')
        credential, raw_key = IntegrationCredential.issue(
            organization=organization, name='documents writer', created_by=self.user,
            scopes=['documents:read', 'documents:write'],
        )
        document = Document.objects.create(title='Antes', slug='document-write-api', organization=organization, status=Document.PUBLISHED, owner=self.user)
        version = create_version(document, self.user, body='histórico')
        self.client.logout()
        response = self.client.patch(
            reverse('learning_api:document-detail', kwargs={'pk': document.pk}),
            data=json.dumps({'title': 'Depois'}), content_type='application/json', HTTP_X_TALK_API_KEY=raw_key,
        )
        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        self.assertEqual(document.title, 'Depois')
        archived = self.client.delete(
            reverse('learning_api:document-detail', kwargs={'pk': document.pk}), HTTP_X_TALK_API_KEY=raw_key,
        )
        self.assertEqual(archived.status_code, 204)
        document.refresh_from_db()
        self.assertEqual(document.status, Document.ARCHIVED)
        self.assertTrue(document.versions.filter(pk=version.pk).exists())

    def test_manager_can_issue_key_and_use_it_on_documents_api(self):
        organization = Organization.objects.create(name='API Tenant', slug='api-tenant')
        session = self.client.session
        session['selected_organization_id'] = organization.pk
        session.save()
        response = self.client.post(
            reverse('learning_api:integration-credentials'),
            data=json.dumps({'name': 'ERP read only', 'scopes': ['documents:read']}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        raw_key = response.json()['key']
        api_response = self.client.get('/api/v1/documents/', HTTP_X_TALK_API_KEY=raw_key)
        self.assertEqual(api_response.status_code, 200)
        self.assertEqual(self.client.get('/api/v1/analytics/engagement/', HTTP_X_TALK_API_KEY=raw_key).status_code, 403)
        rotated = self.client.post(reverse('learning_api:integration-credential-rotate', kwargs={'pk': response.json()['id']}))
        self.assertEqual(rotated.status_code, 200)
        self.assertIn(self.client.get('/api/v1/documents/', HTTP_X_TALK_API_KEY=raw_key).status_code, (401, 403))

    def test_domain_events_enqueue_selected_webhooks(self):
        organization = Organization.objects.create(name='Webhook Tenant', slug='webhook-tenant')
        WebhookSubscription.objects.create(
            organization=organization, name='ERP', endpoint='https://example.com/hooks', events=['session_started'], created_by=self.user,
        )
        track_event(self.user, ContentEvent.SESSION_STARTED, organization=organization)
        self.assertTrue(WebhookDelivery.objects.filter(event_type=ContentEvent.SESSION_STARTED).exists())

    def test_notification_email_uses_text_and_html_templates(self):
        from .services import create_notification
        UserNotificationPreference.objects.create(user=self.user, email=True)
        notification = create_notification(
            self.user, title='Atualização importante', message='Leia o novo procedimento.',
            url='/documents/procedimento/', priority='important', dedupe_key='email-template-test',
        )
        self.assertIsNotNone(notification)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Atualização importante', mail.outbox[0].body)
        self.assertTrue(any(part[1] == 'text/html' for part in mail.outbox[0].alternatives))

    def test_partner_portal_is_scoped_to_the_authenticated_membership(self):
        organization = Organization.objects.create(name='Partner Tenant', slug='partner-tenant')
        partner = Partner.objects.create(organization=organization, name='Rede Parceira')
        PartnerMembership.objects.create(partner=partner, user=self.user, role=PartnerMembership.VIEWER)
        response = self.client.get(reverse('learning_api:partner-me'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['partners'][0]['name'], 'Rede Parceira')
        self.assertEqual(self.client.get('/partner/').status_code, 200)
