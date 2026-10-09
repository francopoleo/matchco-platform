from django.utils import timezone

from .models import Company, ManagementAssignment, OrganizationServiceSubscription


def service_enabled(organization, service_code, company=None):
    """Return whether a service is active, honoring a company override.

    The organization subscription is the default. When a company is supplied,
    its explicit subscription wins; an inactive override therefore suspends a
    service even if the organization default remains active.
    """
    organization_id = getattr(organization, 'pk', organization)
    if not organization_id:
        return False
    company_id = getattr(company, 'pk', company)
    if company_id:
        company_organization_id = getattr(company, 'organization_id', None)
        if company_organization_id is None:
            company_organization_id = Company.objects.filter(pk=company_id).values_list(
                'organization_id', flat=True,
            ).first()
        if company_organization_id != organization_id:
            return False
    subscription = None
    if company_id:
        subscription = OrganizationServiceSubscription.objects.filter(
            organization_id=organization_id,
            company_id=company_id,
            service_code=service_code,
        ).first()
    if subscription is None:
        subscription = OrganizationServiceSubscription.objects.filter(
            organization_id=organization_id,
            company__isnull=True,
            service_code=service_code,
        ).first()
    if subscription is None or subscription.status != OrganizationServiceSubscription.STATUS_ACTIVE:
        return False
    now = timezone.now()
    return not (
        subscription.starts_at and subscription.starts_at > now
        or subscription.ends_at and subscription.ends_at <= now
    )


class ManagementAccessService:
    """Authorization for people administration and subordinate reports."""

    ADMIN_MEMBERSHIP_ROLES = ('owner', 'admin')

    @classmethod
    def _can_manage_from_membership(cls, manager, target_memberships):
        """Allow organization admins to manage users in their active scope.

        ManagementAssignment remains the mechanism for delegated managers. A
        membership with an owner/admin role is the canonical organization-level
        permission, so it must not require a second, easy-to-miss assignment.
        A company-scoped admin is limited to that company; an organization-wide
        admin (no company) can manage every company in the organization.
        """
        manager_memberships = manager.memberships.filter(
            active=True,
            role__in=cls.ADMIN_MEMBERSHIP_ROLES,
        ).values('organization_id', 'company_id')
        for manager_membership in manager_memberships:
            for target_membership in target_memberships:
                if manager_membership['organization_id'] != target_membership['organization_id']:
                    continue
                if (
                    manager_membership['company_id']
                    and manager_membership['company_id'] != target_membership['company_id']
                ):
                    continue
                return True
        return False

    @staticmethod
    def can_manage_user(manager, target, role='people_admin'):
        if not getattr(manager, 'is_authenticated', False):
            return False
        if manager.is_superuser:
            return True
        target_memberships = target.memberships.filter(active=True).values(
            'organization_id', 'company_id', 'business_unit_id', 'operational_unit_id'
        )
        if ManagementAccessService._can_manage_from_membership(manager, target_memberships):
            return True
        assignments = ManagementAssignment.objects.filter(user=manager, role=role, active=True)
        for assignment in assignments:
            for membership in target_memberships:
                if assignment.organization_id != membership['organization_id']:
                    continue
                if assignment.company_id and assignment.company_id != membership['company_id']:
                    continue
                if assignment.business_unit_id and assignment.business_unit_id != membership['business_unit_id']:
                    continue
                if assignment.operational_unit_id and assignment.operational_unit_id != membership['operational_unit_id']:
                    continue
                return True
        return False

    @staticmethod
    def can_view_reports(manager, organization_id=None, company_id=None):
        if manager.is_superuser:
            return True
        assignments = ManagementAssignment.objects.filter(user=manager, role__in=('report_viewer', 'people_admin'), active=True)
        if organization_id:
            assignments = assignments.filter(organization_id=organization_id)
        if company_id:
            assignments = assignments.filter(company_id=company_id)
        return assignments.exists()


management_access = ManagementAccessService()
