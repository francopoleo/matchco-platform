from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import translation
from django.views.i18n import set_language


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


class LanguageSelectionTests(SimpleTestCase):
    def tearDown(self):
        translation.deactivate_all()

    def test_language_endpoint_sets_the_selected_language_cookie(self):
        request = RequestFactory().post(
            reverse('set_language'),
            {'language': 'en', 'next': '/'},
            HTTP_HOST='localhost',
        )

        response = set_language(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, 'en')

    def test_locale_middleware_activates_the_saved_language(self):
        from matchco.middleware import DefaultPortugueseLocaleMiddleware

        request = RequestFactory().get('/', HTTP_COOKIE=f'{settings.LANGUAGE_COOKIE_NAME}=en')
        DefaultPortugueseLocaleMiddleware(lambda request: None).process_request(request)

        self.assertEqual(translation.get_language(), 'en')

    def test_browser_language_does_not_override_the_portuguese_default(self):
        from matchco.middleware import DefaultPortugueseLocaleMiddleware

        request = RequestFactory().get('/', HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')
        DefaultPortugueseLocaleMiddleware(lambda request: None).process_request(request)

        self.assertEqual(translation.get_language(), 'pt-br')

    def test_brazilian_portuguese_is_the_default_and_uses_brazilian_wording(self):
        translation.activate('pt-br')

        self.assertEqual(settings.LANGUAGE_CODE, 'pt-br')
        self.assertEqual(dict(settings.LANGUAGES)['pt-br'], 'Português (Brasil)')
        self.assertEqual(translation.gettext('Settings'), 'Configurações')
        self.assertEqual(translation.gettext('Users'), 'Usuários')
        self.assertEqual(translation.gettext('Content Management'), 'Gestão de conteúdo')
