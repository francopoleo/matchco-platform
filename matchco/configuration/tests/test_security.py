from django.test import RequestFactory, SimpleTestCase, override_settings

from configuration.security import client_ip


class TrustedProxyIPTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(MATCHCO_TRUSTED_PROXY_CIDRS=())
    def test_untrusted_peer_cannot_spoof_forwarded_ip(self):
        request = self.factory.get(
            '/', REMOTE_ADDR='198.51.100.20',
            HTTP_X_FORWARDED_FOR='203.0.113.90',
        )
        self.assertEqual(client_ip(request), '198.51.100.20')

    @override_settings(MATCHCO_TRUSTED_PROXY_CIDRS=('10.0.0.0/8',))
    def test_trusted_proxy_chain_is_resolved_from_right_to_left(self):
        request = self.factory.get(
            '/', REMOTE_ADDR='10.0.0.9',
            HTTP_X_FORWARDED_FOR='203.0.113.5, 10.0.0.3',
        )
        self.assertEqual(client_ip(request), '203.0.113.5')

    @override_settings(MATCHCO_TRUSTED_PROXY_CIDRS=('10.0.0.0/8',))
    def test_malformed_or_oversized_forwarded_chain_falls_back_to_peer(self):
        for header in ('203.0.113.5, invalid', 'x' * 1025):
            with self.subTest(header=header[:20]):
                request = self.factory.get(
                    '/', REMOTE_ADDR='10.0.0.9', HTTP_X_FORWARDED_FOR=header,
                )
                self.assertEqual(client_ip(request), '10.0.0.9')

    def test_invalid_remote_never_promotes_the_forwarded_header(self):
        request = self.factory.get(
            '/', REMOTE_ADDR='', HTTP_X_FORWARDED_FOR='203.0.113.5',
        )
        self.assertEqual(client_ip(request), '0.0.0.0')
