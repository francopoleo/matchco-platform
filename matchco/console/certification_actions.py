from django.utils.translation import gettext_lazy as gettext_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View

from learning.models import Certification, CertificationAward, CertificationRequirement
from .views import ManagerRequiredMixin, active_organization_queryset


class CertificationAwardRevokeView(ManagerRequiredMixin, View):
    def post(self, request, pk, award_pk):
        certification = get_object_or_404(active_organization_queryset(request, Certification.objects.all(), 'organization_id'), pk=pk)
        award = get_object_or_404(CertificationAward, pk=award_pk, certification=certification)
        award.revoked_at = timezone.now()
        metadata = dict(award.metadata or {})
        metadata['revoked_by_user_id'] = request.user.pk
        award.metadata = metadata
        award.save(update_fields=('revoked_at', 'metadata'))
        messages.success(request, gettext_lazy('Certificação revogada e registrada no histórico.'))
        return redirect('console:certification-detail', pk=certification.pk)


class CertificationRenewView(ManagerRequiredMixin, View):
    """Create a new immutable certification version, preserving the old one."""
    def post(self, request, pk):
        current = get_object_or_404(active_organization_queryset(request, Certification.objects.all(), 'organization_id'), pk=pk)
        try:
            major, minor = current.version.split('.', 1)
            version = f'{major}.{int(minor) + 1}'
        except (ValueError, AttributeError):
            version = f'{current.version}.1'
        renewed = Certification.objects.create(
            organization=current.organization, company=current.company,
            title=current.title, slug=f'{current.slug}-{version.replace(".", "-")}',
            description=current.description, status=Certification.DRAFT, version=version,
            validity_days=current.validity_days, minimum_score=current.minimum_score,
            maximum_attempts=current.maximum_attempts, minimum_active_seconds=current.minimum_active_seconds,
            requires_manual_approval=current.requires_manual_approval, starts_at=current.starts_at,
            ends_at=current.ends_at, created_by=getattr(current, 'created_by'),
        )
        for requirement in current.requirements.all():
            CertificationRequirement.objects.create(
                certification=renewed, course=requirement.course, quiz=requirement.quiz,
                position=requirement.position, required=requirement.required, minimum_score=requirement.minimum_score,
            )
        messages.success(request, f'Nova versão {version} criada como rascunho.')
        return redirect('console:certification-edit', pk=renewed.pk)
