"""B1 — OTP passwordless."""
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.contrib.sessions.backends.signed_cookies import SessionStore
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse

from recruitment.models import OtpCode
from recruitment.services import (
    OtpInvalidError, OtpRateLimitError, request_otp, verify_otp,
)


class OtpTests(TestCase):
    def test_request_creates_pending(self):
        otp, code = request_otp(mobile='(11) 90000-0000')
        self.assertEqual(otp.state, OtpCode.STATE_PENDING)
        self.assertEqual(otp.mobile, '11900000000')
        self.assertEqual(len(code), 6)

    def test_verify_success(self):
        otp, code = request_otp(mobile='11900000000')
        used = verify_otp(mobile='11900000000', code=code)
        self.assertEqual(used.state, OtpCode.STATE_USED)

    def test_wrong_code_fails_and_counts(self):
        request_otp(mobile='11900000000')
        with self.assertRaises(OtpInvalidError):
            verify_otp(mobile='11900000000', code='000000')
        otp = OtpCode.objects.get()
        self.assertEqual(otp.attempts, 1)

    def test_five_wrong_attempts_locks(self):
        request_otp(mobile='11900000000')
        for _ in range(5):
            with self.assertRaises(OtpInvalidError):
                verify_otp(mobile='11900000000', code='000000')
        otp = OtpCode.objects.get()
        self.assertEqual(otp.state, OtpCode.STATE_FAILED)

    def test_rate_limit_after_3_pending(self):
        for _ in range(3):
            request_otp(mobile='11900000000')
        with self.assertRaises(OtpRateLimitError):
            request_otp(mobile='11900000000')

    def test_expired_rejected(self):
        request_otp(mobile='11900000000')
        OtpCode.objects.update(expires_at=timezone.now() - timedelta(minutes=1))
        with self.assertRaises(OtpInvalidError):
            verify_otp(mobile='11900000000', code='000000')
        otp = OtpCode.objects.get()
        self.assertEqual(otp.state, OtpCode.STATE_EXPIRED)

    def test_short_mobile_rejected(self):
        from recruitment.services import OtpError
        with self.assertRaises(OtpError):
            request_otp(mobile='1234')

    @override_settings(DEBUG=False, RATELIMIT_ENABLE=False)
    @patch('recruitment.services.request_otp')
    def test_production_otp_request_never_captures_or_renders_code(self, request_otp_mock):
        request_otp_mock.return_value = (SimpleNamespace(mobile='11900000000'), '481205')
        from recruitment.views import OtpRequestView, OtpVerifyView
        request = RequestFactory().post(reverse('recruitment_public:candidato_entrar'), {
            'mobile': '11900000000',
        })
        request.session = SessionStore()
        request.user = AnonymousUser()
        response = OtpRequestView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_dev_otps', request.session)

        verify_request = RequestFactory().get(reverse('recruitment_public:candidato_entrar_codigo'))
        verify_request.session = SessionStore()
        verify_request.session['otp_mobile'] = '11900000000'
        verify_request.session['_dev_otps'] = ['481205']
        verify_request.user = AnonymousUser()
        with patch('recruitment.views.render', return_value=HttpResponse()) as render_mock:
            response = OtpVerifyView.as_view()(verify_request)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(render_mock.call_args.args[2]['dev_hint'])

    @override_settings(DEBUG=False, RATELIMIT_ENABLE=True)
    @patch('recruitment.services.request_otp')
    def test_otp_request_is_rate_limited_by_ip(self, request_otp_mock):
        request_otp_mock.return_value = (SimpleNamespace(mobile='11900000000'), '481205')
        from django_ratelimit.exceptions import Ratelimited
        from recruitment.views import OtpRequestView
        url = reverse('recruitment_public:candidato_entrar')
        view = OtpRequestView.as_view()

        def post_from(ip):
            request = RequestFactory().post(url, {'mobile': '11900000000'}, REMOTE_ADDR=ip)
            request.session = SessionStore()
            request.user = AnonymousUser()
            return view(request)

        for _ in range(10):
            self.assertEqual(post_from('198.51.100.241').status_code, 302)
        self.assertEqual(post_from('198.51.100.242').status_code, 302)
        for _ in range(9):
            self.assertEqual(post_from('198.51.100.242').status_code, 302)
        with self.assertRaises(Ratelimited):
            post_from('198.51.100.242')
