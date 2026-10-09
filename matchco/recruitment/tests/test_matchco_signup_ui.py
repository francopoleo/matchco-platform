"""A1 — MatchcoSignupForm (Perfil de 6 campos + gate 18+ + consent granular)."""
from datetime import date, timedelta
from django.test import TestCase

from recruitment.forms import MatchcoSignupForm
from recruitment.models import CanonicalCatalog, CanonicalTerm


def _valid_data(**over):
    d = {
        'first_name': 'Ana', 'last_name': 'Silva',
        'mobile': '11900000000', 'email': 'a@ex.com',
        'birth_date': (date.today() - timedelta(days=365 * 25)).isoformat(),
        'where_neighborhoods': 'Pinheiros',
        'when_days': ['mon', 'tue'],
        'when_period': 'morning',
        'what_function_terms': [],
        'interest_mode': 'want',
        'experience': 'some',
        'experience_contexts': ['clothing'],
        'work_format': 'ambos',
        'can_start': date.today().isoformat(),
        'consent_store': True,
        'consent_transactional': True,
        'accept_privacy': True,
    }
    d.update(over)
    return d


class MatchcoSignupFormTests(TestCase):
    def setUp(self):
        catalog = CanonicalCatalog.objects.create(
            code='test-market', name='Test market', version=1,
            status=CanonicalCatalog.STATUS_PUBLISHED,
        )
        self.function = CanonicalTerm.objects.create(
            catalog=catalog, term_type=CanonicalTerm.TYPE_FUNCTION,
            code='test-caixa', label='Caixa de loja',
        )

    def test_valid_form_passes(self):
        f = MatchcoSignupForm(data=_valid_data(what_function_terms=[str(self.function.pk)]))
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data['interest_mode'], 'want')
        self.assertEqual(f.cleaned_data['experience_contexts'], ['clothing'])

    def test_under_18_rejected(self):
        f = MatchcoSignupForm(data=_valid_data(
            birth_date=(date.today() - timedelta(days=365 * 10)).isoformat(),
        ))
        self.assertFalse(f.is_valid())
        self.assertIn('birth_date', f.errors)

    def test_at_least_one_circulation_scope_required(self):
        data = _valid_data()
        data.pop('consent_store')
        f = MatchcoSignupForm(data=data)
        self.assertFalse(f.is_valid())
        self.assertIn('__all__', f.errors)

    def test_privacy_acceptance_mandatory(self):
        data = _valid_data()
        data.pop('accept_privacy')
        f = MatchcoSignupForm(data=data)
        self.assertFalse(f.is_valid())

    def test_transactional_consent_mandatory(self):
        data = _valid_data()
        data.pop('consent_transactional')
        f = MatchcoSignupForm(data=data)
        self.assertFalse(f.is_valid())
