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

    def test_sidebar_labels_follow_english_and_spanish_preferences(self):
        from matchco.core.menu import GROUPS, MENU_ITEMS

        labels = {str(item['label']): item['label'] for item in MENU_ITEMS}
        with translation.override('en'):
            self.assertEqual(str(GROUPS['structure']), 'Organization and structure')
            self.assertEqual(str(labels['Notificações']), 'Notifications')
            self.assertEqual(str(labels['Portas de entrada e QR Codes']), 'Entry points and QR codes')
            self.assertEqual(translation.gettext('Voltar ao site'), 'Back to website')

        with translation.override('es'):
            self.assertEqual(str(GROUPS['structure']), 'Organización y estructura')
            self.assertEqual(str(labels['Notificações']), 'Notificaciones')
            self.assertEqual(str(labels['Portas de entrada e QR Codes']), 'Puntos de entrada y códigos QR')
            self.assertEqual(translation.gettext('Voltar ao site'), 'Volver al sitio web')

    def test_language_names_are_translated_to_the_current_interface_language(self):
        with translation.override('pt-br'):
            self.assertEqual(translation.get_language_info('en')['name_translated'], 'Inglês')
            self.assertEqual(translation.get_language_info('es')['name_translated'], 'Espanhol')

    def test_language_selector_itself_follows_the_active_language(self):
        from django.template import Context, loader

        template = loader.get_template('ui/components/language_selector.html')
        for language, expected in (
            ('pt-br', ('Idioma', 'Aplicar', 'Inglês', 'Espanhol')),
            ('en', ('Language', 'Apply', 'English', 'Spanish')),
            ('es', ('Idioma', 'Aplicar', 'Inglés', 'Español')),
        ):
            with self.subTest(language=language), translation.override(language):
                rendered = template.template.render(Context({'compact': True, 'selector_id': 'test-language'}))
                for label in expected:
                    self.assertIn(label, rendered)

        with translation.override('pt-br'):
            public_selector = template.template.render(Context({'quiet': True, 'selector_id': 'public-language'}))
            self.assertIn('text-xs text-slate-500', public_selector)
            self.assertIn('name="language"', public_selector)
            self.assertNotIn('bg-brand', public_selector)

    def test_public_language_switch_uses_inline_codes_without_apply(self):
        from django.template import Context, loader

        request = RequestFactory().get('/console/')
        rendered = loader.get_template('ui/components/public_language_switch.html').template.render(
            Context({'request': request})
        )
        self.assertIn('>PT</button>', rendered)
        self.assertIn('>EN</button>', rendered)
        self.assertIn('>ES</button>', rendered)
        self.assertNotIn('Apply', rendered)
        self.assertIn('value="pt-br"', rendered)
        self.assertIn('value="en"', rendered)
        self.assertIn('value="es"', rendered)

    def test_public_access_page_places_language_switch_in_its_header(self):
        from django.template import Context, loader

        request = RequestFactory().get('/matchco/acessos/')
        template = loader.get_template('recruitment/match/access.html').template
        html = template.render(Context({'request': request}))
        header_start = html.index('<header')
        header_end = html.index('</header>', header_start)
        switch_position = html.index('class="mc-public-language-switch"')
        self.assertLess(header_start, switch_position)
        self.assertLess(switch_position, header_end)
        self.assertIn('>PT</button>', html)
        self.assertIn('>EN</button>', html)
        self.assertIn('>ES</button>', html)
        self.assertNotIn('>APLICAR</button>', html)
