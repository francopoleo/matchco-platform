"""B1 — OTP passwordless."""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

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
