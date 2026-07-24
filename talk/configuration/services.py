from .models import ManagementAssignment


class ManagementAccessService:
    """Authorization for people administration and subordinate reports."""

    @staticmethod
    def can_manage_user(manager, target, role='people_admin'):
        if not getattr(manager, 'is_authenticated', False):
            return False
        if manager.is_superuser:
            return True
        target_memberships = target.memberships.filter(active=True).values(
            'organization_id', 'company_id', 'business_unit_id', 'operational_unit_id'
        )
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
