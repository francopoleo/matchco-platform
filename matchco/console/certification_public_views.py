from django.shortcuts import render
from django.views.generic import View
from django_tenants.utils import get_tenant_model, schema_context

from learning.models import CertificationAward


class CertificationVerificationView(View):
    """Public verification without exposing the holder's personal data."""
    template_name = 'public/certification_verify.html'

    def get(self, request, code):
        result = None
        for tenant in get_tenant_model().objects.exclude(schema_name='public'):
            with schema_context(tenant.schema_name):
                award = CertificationAward.objects.select_related('certification').filter(verification_code=code).first()
                if award:
                    result = {
                        'valid': award.is_valid,
                        'title': award.certification.title,
                        'organization': award.certification.organization.name,
                        'version': award.version,
                        'issued_at': award.issued_at,
                        'expires_at': award.expires_at,
                    }
                    break
        return render(request, self.template_name, {'result': result, 'code': code})
