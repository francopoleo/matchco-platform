from dataclasses import dataclass

from .models import AudienceRule



@dataclass(frozen=True)
class EligibilityDecision:
    allowed: bool
    code: str
    reason: str
    policy_id: int | None = None


class EligibilityService:
    """Centralized audience evaluator for the enterprise hierarchy."""

    @staticmethod
    def _content_organization_id(content):
        content_organization_id = getattr(content, 'organization_id', None)
        if content_organization_id is None:
            module = getattr(content, 'module', None)
            content_organization_id = getattr(getattr(module, 'course', None), 'organization_id', None)
        return content_organization_id

    @staticmethod
    def _has_management_override(user, organization_id=None):
        """Allow system and tenant managers to inspect selected-org content."""
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return True
        if not getattr(user, 'is_authenticated', False):
            return False
        groups = getattr(user, 'groups', None)
        if groups is not None and groups.filter(name__in=('content_manager', 'audience_manager')).exists():
            return True
        if not getattr(user, 'pk', None):
            return False
        if not organization_id:
            return False
        from configuration.models import ManagementAssignment, Membership
        return (
            ManagementAssignment.objects.filter(
                user=user, organization_id=organization_id, active=True,
                role__in=('people_admin', 'report_viewer', 'audience_manager'),
            ).exists()
            or Membership.objects.filter(
                user=user, organization_id=organization_id, active=True,
                role__in=('owner', 'admin'),
            ).exists()
        )

    def can_view(self, user, content):
        if not getattr(user, 'is_authenticated', False):
            return EligibilityDecision(False, 'authentication_required', 'Authentication is required.')
        if not getattr(content, 'is_published', True):
            return EligibilityDecision(False, 'content_unpublished', 'Content is not published.')
        active = getattr(user, '_active_organization_id', None)
        content_organization_id = self._content_organization_id(content)
        if self._has_management_override(user, active):
            if active is not None and content_organization_id and int(content_organization_id) != int(active):
                return EligibilityDecision(False, 'organization_mismatch', 'Content is outside the active organization.')
            return EligibilityDecision(True, 'management_access', 'Management users can inspect selected organization content.', getattr(getattr(content, 'audience_policy', None), 'id', None))

        policy = getattr(content, 'audience_policy', None)
        if policy is None:
            module = getattr(content, 'module', None)
            course = getattr(module, 'course', None)
            policy = getattr(course, 'audience_policy', None)
        membership_query = user.memberships.filter(active=True)
        active_organization_id = getattr(user, '_active_organization_id', None)
        if active_organization_id:
            membership_query = membership_query.filter(organization_id=active_organization_id)
        memberships = list(membership_query.prefetch_related('channels', 'functions'))
        if not memberships:
            return EligibilityDecision(False, 'membership_required', 'An active organization membership is required.')
        if content_organization_id and not any(
            membership.organization_id == content_organization_id for membership in memberships
        ):
            return EligibilityDecision(False, 'organization_mismatch', 'The user is outside the content organization.')
        if policy is None or not policy.active:
            return EligibilityDecision(True, 'organization_content', 'Content is available to active members.', getattr(policy, 'id', None))

        policy_organization_id = getattr(policy, 'organization_id', None)
        if policy_organization_id and not any(m.organization_id == policy_organization_id for m in memberships):
            return EligibilityDecision(False, 'organization_mismatch', 'The user is outside the policy organization.', policy.id)
        rules = list(policy.rules.all())
        if not rules:
            return EligibilityDecision(True, 'empty_policy', 'The policy has no restrictions.', policy.id)

        results = [self._rule_matches(memberships, rule, user) for rule in rules]
        allowed = all(results) if policy.match_mode == policy.ALL else any(results)
        return EligibilityDecision(
            allowed,
            'audience_match' if allowed else 'audience_mismatch',
            'Audience policy evaluated.',
            getattr(policy, 'id', None),
        )

    def can_view_with_recruitment_context(self, user, content, context):
        """Evaluate content only inside an approved recruitment projection.

        The projection selects the platform organization; this method still
        delegates the final decision to Membership and Audience rules.
        """
        platform_ids = {
            int(value) for value in (context or {}).get('platform_organization_ids', [])
        }
        active = getattr(user, '_active_organization_id', None)
        if active is not None and int(active) not in platform_ids:
            return EligibilityDecision(
                False,
                'recruitment_context_mismatch',
                'The active organization is outside the recruitment context.',
            )
        return self.can_view(user, content)

    def _rule_matches(self, memberships, rule, user=None):
        expected = {str(value) for value in rule.values}
        values = set()
        for membership in memberships:
            if rule.dimension == 'organization':
                values.add(str(membership.organization_id))
            elif rule.dimension == 'company':
                values.add(str(membership.company_id))
            elif rule.dimension == 'business_unit':
                if membership.business_unit_id:
                    values.add(str(membership.business_unit_id))
            elif rule.dimension == 'operational_unit':
                if membership.operational_unit_id:
                    values.add(str(membership.operational_unit_id))
            elif rule.dimension == 'channel':
                values.update(str(item.pk) for item in membership.channels.all())
            elif rule.dimension == 'function':
                values.update(str(item.pk) for item in membership.functions.all())
            elif rule.dimension == 'program' and user is not None:
                from recruitment.models import ProgramMembership
                values.update(
                    str(item.program_id)
                    for item in ProgramMembership.objects.filter(user_id=user.pk, active=True)
                )
            elif rule.dimension == 'person_type':
                if membership.person_type_id:
                    values.add(str(membership.person_type_id))
            elif rule.dimension == 'membership_role':
                values.add(str(membership.role))
        matched = bool(values.intersection(expected))
        return not matched if rule.negate else matched


eligibility = EligibilityService()


def estimate_policy_reach(policy, organization_id=None):
    """Return an aggregate impact estimate using the canonical audience rules."""
    from configuration.models import Membership

    memberships = Membership.objects.filter(active=True)
    if organization_id:
        memberships = memberships.filter(organization_id=organization_id)
    if policy and policy.organization_id:
        memberships = memberships.filter(organization_id=policy.organization_id)
    memberships = memberships.prefetch_related('channels', 'functions')
    if not policy or not policy.active or not policy.rules.exists():
        matched = list(memberships)
    else:
        rules = list(policy.rules.all())

        def rule_matches(membership, rule):
            if rule.dimension == AudienceRule.TENANT:
                values = {str(membership.organization_id)}
            elif rule.dimension == AudienceRule.COMPANY:
                values = {str(membership.company_id)}
            elif rule.dimension == AudienceRule.BUSINESS_UNIT:
                values = {str(membership.business_unit_id)} if membership.business_unit_id else set()
            elif rule.dimension == AudienceRule.OPERATIONAL_UNIT:
                values = {str(membership.operational_unit_id)} if membership.operational_unit_id else set()
            elif rule.dimension == AudienceRule.CHANNEL:
                values = {str(channel.pk) for channel in membership.channels.all()}
            elif rule.dimension == AudienceRule.PROGRAM:
                from recruitment.models import ProgramMembership
                values = {
                    str(item.program_id)
                    for item in ProgramMembership.objects.filter(
                        user_id=membership.user_id, active=True,
                    )
                }
            elif rule.dimension == AudienceRule.PERSON_TYPE:
                values = {str(membership.person_type_id)} if membership.person_type_id else set()
            elif rule.dimension == AudienceRule.MEMBERSHIP_ROLE:
                values = {str(membership.role)}
            else:
                values = {str(function.pk) for function in membership.functions.all()}
            result = bool(values.intersection(str(value) for value in rule.values))
            return not result if rule.negate else result

        matched = [
            membership for membership in memberships
            if (all(rule_matches(membership, rule) for rule in rules) if policy.match_mode == policy.ALL else any(rule_matches(membership, rule) for rule in rules))
        ]
    return {
        'users': len({membership.user_id for membership in matched}),
        'companies': len({membership.company_id for membership in matched if membership.company_id}),
        'memberships': len(matched),
    }
