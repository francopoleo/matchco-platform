"""Fase 1 — EntryPoint + roteamento QR canônico.

Ver SISTEMA_MATCHCO_CANONICO §3.8 e §7.
"""
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.db import IntegrityError, transaction
from django.test import TestCase, RequestFactory, override_settings
from django.utils import timezone

from recruitment.models import EntryPoint
from recruitment.domain_models import RecruitmentCompany, RecruitmentOrganization, RecruitmentStore
from recruitment.views import EntryPointResolveView, _entry_point_resolve_url


def _make_request(path='/'):
    """Request com sessão inicializada, bypass de middleware de tenant."""
    factory = RequestFactory()
    req = factory.get(path)
    req.user = AnonymousUser()
    sm = SessionMiddleware(lambda r: None)
    sm.process_request(req)
    req.session.save()
    return req


class EntryPointModelTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(
            external_id='org-1', slug='org-1', name='Org 1',
        )

    def _make(self, **kwargs):
        defaults = dict(
            organization=self.org,
            kind=EntryPoint.KIND_STORE,
            canonical_destination_url='https://match.example.com/entry/1',
        )
        defaults.update(kwargs)
        return EntryPoint.objects.create(**defaults)

    def test_can_activate_requires_https_and_tested_at(self):
        ep = self._make()
        self.assertFalse(ep.can_activate(), "PIAG: sem activation_tested_at não ativa")

        ep.activation_tested_at = timezone.now()
        ep.save()
        self.assertTrue(ep.can_activate())

    def test_can_activate_rejects_non_https(self):
        ep = self._make(
            canonical_destination_url='http://insecure.example.com/',
            activation_tested_at=timezone.now(),
        )
        self.assertFalse(ep.can_activate(), "PIAG: destino canônico deve ser HTTPS")

    def test_default_state_is_draft(self):
        ep = self._make()
        self.assertEqual(ep.state, EntryPoint.STATE_DRAFT)
        self.assertFalse(ep.is_active)

    def test_default_mode_is_match(self):
        ep = self._make()
        self.assertEqual(ep.mode, EntryPoint.MODE_MATCH)

    def test_unit_cannot_have_two_active_qr_entry_points(self):
        company = RecruitmentCompany.objects.create(organization=self.org, name='Loja')
        store = RecruitmentStore.objects.create(
            organization=self.org, company=company, name='Unidade física',
        )
        self._make(
            label='QR principal', scope_store=store,
            state=EntryPoint.STATE_ACTIVE,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._make(
                label='QR duplicado', scope_store=store,
                state=EntryPoint.STATE_ACTIVE,
            )


class EntryPointResolveViewTests(TestCase):
    def setUp(self):
        self.org = RecruitmentOrganization.objects.create(
            external_id='org-2', slug='org-2', name='Org 2',
        )
        self.view = EntryPointResolveView.as_view()

    def _active_ep(self, **kwargs):
        defaults = dict(
            organization=self.org,
            kind=EntryPoint.KIND_STORE,
            canonical_destination_url='https://match.example.com/entry/x',
            activation_tested_at=timezone.now(),
            state=EntryPoint.STATE_ACTIVE,
        )
        defaults.update(kwargs)
        return EntryPoint.objects.create(**defaults)

    def test_active_redirects_to_canonical(self):
        ep = self._active_ep()
        resp = self.view(_make_request(), entry_point_id=ep.id)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], ep.canonical_destination_url)

    @override_settings(QR_CODE_BASE_URL='https://qr.example.test/')
    def test_qr_target_uses_configured_public_base_url(self):
        ep = self._active_ep()

        target = _entry_point_resolve_url(_make_request(), ep)

        self.assertEqual(target, f'https://qr.example.test/qr/{ep.pk}/')

    def test_active_stores_context_in_session(self):
        ep = self._active_ep(mode=EntryPoint.MODE_MATCH)
        req = _make_request()
        self.view(req, entry_point_id=ep.id)
        self.assertEqual(req.session['ep_id'], str(ep.id))
        self.assertEqual(req.session['ep_mode'], EntryPoint.MODE_MATCH)
        self.assertEqual(req.session['ep_kind'], EntryPoint.KIND_STORE)

    def test_revoked_returns_410(self):
        ep = self._active_ep(state=EntryPoint.STATE_REVOKED)
        resp = self.view(_make_request(), entry_point_id=ep.id)
        self.assertEqual(resp.status_code, 410)

    def test_draft_raises_404(self):
        from django.http import Http404
        ep = self._active_ep(state=EntryPoint.STATE_DRAFT)
        with self.assertRaises(Http404):
            self.view(_make_request(), entry_point_id=ep.id)

    def test_unknown_raises_404(self):
        from django.http import Http404
        import uuid as _uuid
        with self.assertRaises(Http404):
            self.view(_make_request(), entry_point_id=_uuid.uuid4())
