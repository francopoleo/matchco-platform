from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ConsoleAnalyticsPageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='console-analytics-admin', password='test-pass', email='admin@example.com',
        )
        self.client.force_login(self.user)

    def test_engagement_funnel_renders_with_audience_filters(self):
        response = self.client.get(reverse('console:engagement-funnel'), {'kind': 'wiki', 'period': '30'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Funil de engajamento')

    def test_content_metrics_links_to_funnel(self):
        response = self.client.get(reverse('console:content-metrics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('console:engagement-funnel'))
