from django.contrib import admin

from .models import (
    CandidateProfile, Position, CandidateOnboardingTrail, PreboardingAssignment, PreboardingEvidence,
    CandidateProfileSurveyResponse,
    CandidateIdentity, CandidateConsent, CandidateAssessment,
    CandidateAccountLink,
    CanonicalCatalog, CanonicalTerm, CanonicalTermAlias, CanonicalFunctionMapping,
    CandidateCanonicalResponse, OpportunityCanonicalRequirement,
    CoverageGap, EnrichmentCampaign, EnrichmentInvite, EnrichmentResponse,
    EmploymentRecord, EmploymentEvent,
    RecruitmentAuditEvent,
    EntryPointScanEvent,
    RecruitmentPolicy,
    EntryPoint,
    OpportunityCriterion, OpportunityVersionHistory,
    Program, ProgramUnitScope, ProgramInvite, ProgramMembership, ProgramResource,
    ControlledAccessRequest, AccessApprovalEvent,
    QuestionnaireTemplate, QuestionnaireQuestion,
)


@admin.register(EntryPointScanEvent)
class EntryPointScanEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'organization', 'entry_point', 'business_unit', 'ip_address')
    list_filter = ('organization', 'entry_point', 'created_at')
    search_fields = ('user__username', 'user__email', 'entry_point__label', 'business_unit__name')
    readonly_fields = [field.name for field in EntryPointScanEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CandidateAccountLink)
class CandidateAccountLinkAdmin(admin.ModelAdmin):
    list_display = ('user', 'identity', 'status', 'verification_method', 'linked_by', 'created_at', 'revoked_at')
    list_filter = ('status', 'verification_method', 'created_at')
    search_fields = ('user__username', 'user__email', 'identity__email_normalized', 'identity__phone_normalized')
    readonly_fields = ('linked_by', 'revoked_by', 'created_at', 'revoked_at')

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.linked_by = request.user
        super().save_model(request, obj, form, change)
from .domain_models import (
    RecruitmentChannel,
    RecruitmentCompany,
    RecruitmentJobFunction,
    RecruitmentOrganization,
    RecruitmentOrganizationRelation,
    RecruitmentPlatformBinding,
    RecruitmentPhysicalUnit,
    RecruitmentStore,
)


class QuestionnaireQuestionInline(admin.TabularInline):
    model = QuestionnaireQuestion
    extra = 0
    fields = ('order', 'key', 'label', 'field_type', 'options', 'required', 'active', 'conditions')


@admin.register(QuestionnaireTemplate)
class QuestionnaireTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'code', 'version', 'status', 'source', 'market', 'audience_role', 'is_default', 'updated_at')
    list_filter = ('status', 'purpose', 'market', 'is_default', 'organization')
    search_fields = ('name', 'code', 'description', 'organization__name')
    inlines = [QuestionnaireQuestionInline]
    actions = ('clone_as_draft',)
    readonly_fields = ('published_at', 'created_at', 'updated_at')

    @admin.action(description='Criar próxima versão como rascunho')
    def clone_as_draft(self, request, queryset):
        created = 0
        for template in queryset.select_related('organization').prefetch_related('questions'):
            next_version = template.__class__.objects.filter(
                organization=template.organization, code=template.code,
            ).order_by('-version').values_list('version', flat=True).first() or 0
            draft = template.__class__.objects.create(
                organization=template.organization,
                code=template.code,
                name=template.name,
                description=template.description,
                version=next_version + 1,
                status=QuestionnaireTemplate.STATUS_DRAFT,
                purpose=template.purpose,
                audience_role=template.audience_role,
                market=template.market,
                scope_store=template.scope_store,
                scope_channel=template.scope_channel,
                scope_job_function=template.scope_job_function,
                entry_point=template.entry_point,
                is_default=False,
                source='manual_clone',
                generation_context={'cloned_from': str(template.pk)},
            )
            QuestionnaireQuestion.objects.bulk_create([
                QuestionnaireQuestion(
                    template=draft, key=question.key, label=question.label,
                    help_text=question.help_text, field_type=question.field_type,
                    options=question.options, conditions=question.conditions,
                    required=question.required,
                    order=question.order, active=question.active,
                ) for question in template.questions.all()
            ])
            created += 1
        self.message_user(request, f'{created} nova(s) versão(ões) criada(s) como rascunho.')

    def save_model(self, request, obj, form, change):
        if obj.status == QuestionnaireTemplate.STATUS_PUBLISHED and not obj.published_at:
            from django.utils import timezone
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'kind', 'status', 'access_level', 'participant_free', 'created_at')
    list_filter = ('kind', 'status', 'access_level', 'participant_free', 'organization')
    search_fields = ('name', 'sponsor_name', 'description')


@admin.register(ProgramMembership)
class ProgramMembershipAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'program', 'role', 'state', 'active', 'consented_at', 'revoked_at')
    list_filter = ('role', 'state', 'active', 'program')
    search_fields = ('user_id', 'program__name')


@admin.register(ProgramUnitScope)
class ProgramUnitScopeAdmin(admin.ModelAdmin):
    list_display = ('business_unit', 'program', 'contract_label', 'active', 'starts_at', 'ends_at')
    list_filter = ('active', 'program')
    search_fields = ('business_unit__name', 'program__name', 'contract_label')


@admin.register(ProgramInvite)
class ProgramInviteAdmin(admin.ModelAdmin):
    list_display = ('email', 'program', 'role', 'state', 'expires_at', 'accepted_at')
    list_filter = ('state', 'role', 'program')
    search_fields = ('email', 'token', 'program__name')


@admin.register(ControlledAccessRequest)
class ControlledAccessRequestAdmin(admin.ModelAdmin):
    list_display = ('organization', 'company', 'request_type', 'program', 'business_unit', 'user_id', 'required_level', 'state', 'approved_by', 'approved_at')
    list_filter = ('request_type', 'required_level', 'state', 'organization')
    search_fields = ('organization__name', 'program__name', 'business_unit__name', 'user_id')
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'revoked_at')
    actions = ('approve_selected', 'revoke_selected')

    @admin.action(description='Aprovar e ativar acesso selecionado')
    def approve_selected(self, request, queryset):
        from .services import AccessApprovalError, approve_controlled_access
        count = 0
        for access_request in queryset:
            try:
                approve_controlled_access(access_request=access_request, actor=request.user, reason='Aprovado no console administrativo')
                count += 1
            except AccessApprovalError as exc:
                self.message_user(request, f'{access_request.pk}: {exc}', level='ERROR')
        self.message_user(request, f'{count} solicitação(ões) ativada(s).')

    @admin.action(description='Revogar acesso selecionado')
    def revoke_selected(self, request, queryset):
        from .services import AccessApprovalError, revoke_controlled_access
        count = 0
        for access_request in queryset:
            try:
                revoke_controlled_access(access_request=access_request, actor=request.user, reason='Revogado no console administrativo')
                count += 1
            except AccessApprovalError as exc:
                self.message_user(request, f'{access_request.pk}: {exc}', level='ERROR')
        self.message_user(request, f'{count} solicitação(ões) revogada(s).')


@admin.register(AccessApprovalEvent)
class AccessApprovalEventAdmin(admin.ModelAdmin):
    list_display = ('request', 'action', 'level', 'actor', 'created_at')
    list_filter = ('action', 'level')
    search_fields = ('request__organization__name', 'reason')
    readonly_fields = ('request', 'action', 'level', 'actor', 'reason', 'scope_snapshot', 'created_at')


@admin.register(PreboardingAssignment)
class PreboardingAssignmentAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'tag', 'state', 'organization', 'company', 'business_unit', 'program', 'position', 'requires_approved_access')
    list_filter = ('tag', 'state', 'requires_approved_access', 'organization')
    search_fields = ('candidate__email', 'candidate__first_name', 'position__title', 'program__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PreboardingEvidence)
class PreboardingEvidenceAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'evidence_type', 'evidence_key', 'provider', 'completed_at', 'valid_until')
    list_filter = ('evidence_type', 'provider')
    search_fields = ('evidence_key', 'provider', 'assignment__candidate__email')
    readonly_fields = ('created_at',)


@admin.register(CoverageGap)
class CoverageGapAdmin(admin.ModelAdmin):
    list_display = ('position', 'organization', 'eligible_count', 'interested_count', 'minimum_eligible', 'minimum_interested', 'state', 'last_evaluated_at')
    list_filter = ('state', 'organization')
    search_fields = ('position__title', 'organization__name')
    readonly_fields = ('eligible_count', 'interested_count', 'last_evaluated_at', 'created_at', 'updated_at')
    actions = ('evaluate_selected',)

    @admin.action(description='Recalcular cobertura sem ranking')
    def evaluate_selected(self, request, queryset):
        from .services import evaluate_coverage_gap
        for gap in queryset:
            evaluate_coverage_gap(coverage_gap=gap)
        self.message_user(request, f'{queryset.count()} cobertura(s) recalculada(s).')


@admin.register(EnrichmentCampaign)
class EnrichmentCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'coverage_gap', 'position', 'status', 'starts_at', 'ends_at')
    list_filter = ('status', 'organization')
    search_fields = ('name', 'organization__name', 'position__title')
    actions = ('activate_selected', 'pause_selected', 'close_selected')

    def _change_status(self, request, queryset, status, label):
        from .services import change_enrichment_campaign_status
        for campaign in queryset:
            change_enrichment_campaign_status(campaign=campaign, status=status)
        self.message_user(request, f'{queryset.count()} campanha(s) {label}.')

    @admin.action(description='Ativar campanha')
    def activate_selected(self, request, queryset):
        from .models import EnrichmentCampaign
        self._change_status(request, queryset, EnrichmentCampaign.STATUS_ACTIVE, 'ativada(s)')

    @admin.action(description='Pausar campanha')
    def pause_selected(self, request, queryset):
        from .models import EnrichmentCampaign
        self._change_status(request, queryset, EnrichmentCampaign.STATUS_PAUSED, 'pausada(s)')

    @admin.action(description='Encerrar campanha')
    def close_selected(self, request, queryset):
        from .models import EnrichmentCampaign
        self._change_status(request, queryset, EnrichmentCampaign.STATUS_CLOSED, 'encerrada(s)')


@admin.register(EnrichmentInvite)
class EnrichmentInviteAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'candidate', 'state', 'expires_at', 'responded_at')
    list_filter = ('state', 'campaign')
    search_fields = ('candidate__email', 'campaign__name')
    readonly_fields = ('token', 'created_at', 'started_at', 'responded_at', 'declined_at')


@admin.register(EnrichmentResponse)
class EnrichmentResponseAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'candidate', 'questionnaire_template', 'questionnaire_version', 'consented_at', 'created_at')
    list_filter = ('campaign', 'questionnaire_template')
    search_fields = ('candidate__email', 'campaign__name')
    readonly_fields = ('created_at',)


@admin.register(CanonicalCatalog)
class CanonicalCatalogAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'version', 'status', 'source', 'published_at')
    list_filter = ('status', 'source')
    search_fields = ('code', 'name')


@admin.register(CanonicalTerm)
class CanonicalTermAdmin(admin.ModelAdmin):
    list_display = ('label', 'term_type', 'catalog', 'code', 'active')
    list_filter = ('term_type', 'active', 'catalog')
    search_fields = ('label', 'code', 'normalized_label')
    readonly_fields = ('normalized_label',)


@admin.register(CanonicalTermAlias)
class CanonicalTermAliasAdmin(admin.ModelAdmin):
    list_display = ('alias', 'term', 'source', 'active')
    list_filter = ('source', 'active')
    search_fields = ('alias', 'normalized_alias', 'term__label')
    readonly_fields = ('normalized_alias',)


@admin.register(CanonicalFunctionMapping)
class CanonicalFunctionMappingAdmin(admin.ModelAdmin):
    list_display = ('term', 'job_function', 'business_unit', 'local_label', 'organization', 'source', 'active')
    list_filter = ('source', 'active', 'organization', 'business_unit')
    search_fields = ('term__label', 'job_function__name', 'local_label', 'organization__name', 'business_unit__name')


@admin.register(CandidateCanonicalResponse)
class CandidateCanonicalResponseAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'term', 'scope', 'purpose', 'origin', 'catalog_version', 'valid_until', 'revoked_at')
    list_filter = ('scope', 'purpose', 'origin', 'term__catalog')
    search_fields = ('candidate__email', 'candidate__first_name', 'term__label', 'source_reference')
    readonly_fields = ('created_at',)


@admin.register(OpportunityCanonicalRequirement)
class OpportunityCanonicalRequirementAdmin(admin.ModelAdmin):
    list_display = ('position', 'term', 'requirement', 'source', 'active')
    list_filter = ('requirement', 'source', 'active')
    search_fields = ('position__title', 'term__label')


@admin.register(ProgramResource)
class ProgramResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'program', 'resource_type', 'required', 'url')
    list_filter = ('resource_type', 'required', 'program')
    search_fields = ('title', 'external_id', 'url')


@admin.register(RecruitmentOrganization)
class RecruitmentOrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'active', 'legacy_id')
    list_filter = ('active',)
    search_fields = ('name', 'slug', 'external_id')


@admin.register(RecruitmentOrganizationRelation)
class RecruitmentOrganizationRelationAdmin(admin.ModelAdmin):
    list_display = ('organization', 'related_organization', 'relation_type', 'active')
    list_filter = ('relation_type', 'active')
    search_fields = ('organization__name', 'related_organization__name')


@admin.register(RecruitmentPhysicalUnit)
class RecruitmentPhysicalUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'external_key', 'city', 'state', 'active')
    list_filter = ('active', 'state')
    search_fields = ('name', 'external_key', 'city')


@admin.register(RecruitmentPlatformBinding)
class RecruitmentPlatformBindingAdmin(admin.ModelAdmin):
    list_display = ('recruitment_organization', 'platform_organization_id', 'capabilities', 'active')
    list_filter = ('active',)
    search_fields = ('recruitment_organization__name', 'platform_organization_id')


@admin.register(RecruitmentCompany)
class RecruitmentCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'active', 'legacy_id')
    list_filter = ('active', 'organization')
    search_fields = ('name', 'code')


@admin.register(RecruitmentStore)
class RecruitmentStoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'organization', 'physical_unit', 'active', 'legacy_id')
    list_filter = ('active', 'organization', 'company')
    search_fields = ('name', 'code')
    fieldsets = (
        (None, {'fields': ('organization', 'company', 'channel', 'physical_unit', 'name', 'code', 'active', 'latitude', 'longitude')}),
        ('Prazos da distribuição (em branco usa a empresa)', {'fields': (
            'candidate_response_hours_override', 'employer_decision_hours_override',
            'invite_batch_size_override', 'round_wait_hours_override',
        )}),
    )


@admin.register(RecruitmentChannel)
class RecruitmentChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'active', 'legacy_id')
    list_filter = ('active', 'company')
    search_fields = ('name',)


@admin.register(RecruitmentJobFunction)
class RecruitmentJobFunctionAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'organization', 'active', 'legacy_id')
    list_filter = ('active', 'organization', 'company')
    search_fields = ('name',)


@admin.register(CandidateIdentity)
class CandidateIdentityAdmin(admin.ModelAdmin):
    list_display = ('email_normalized', 'pool_opt_in', 'verified_at', 'created_at')
    list_filter = ('pool_opt_in', 'verified_at')
    search_fields = ('email_normalized', 'phone_normalized')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CandidateConsent)
class CandidateConsentAdmin(admin.ModelAdmin):
    list_display = ('identity', 'organization', 'purpose', 'granted', 'policy_version', 'granted_at', 'revoked_at')
    list_filter = ('purpose', 'granted', 'organization')
    search_fields = ('identity__email_normalized',)
    readonly_fields = ('granted_at',)


@admin.register(CandidateAssessment)
class CandidateAssessmentAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'provider', 'title_snapshot', 'status', 'score', 'created_at')
    list_filter = ('provider', 'status')
    search_fields = ('candidate__email', 'external_id', 'title_snapshot')


@admin.register(EmploymentRecord)
class EmploymentRecordAdmin(admin.ModelAdmin):
    list_display = ('identity', 'organization', 'position_title', 'status', 'started_at', 'ended_at')
    list_filter = ('status', 'employment_type', 'organization')
    search_fields = ('identity__email_normalized', 'corporate_email', 'position_title')


@admin.register(EmploymentEvent)
class EmploymentEventAdmin(admin.ModelAdmin):
    list_display = ('employment', 'event_type', 'created_at')
    list_filter = ('event_type',)
    readonly_fields = ('employment', 'event_type', 'metadata', 'created_at')


@admin.register(RecruitmentAuditEvent)
class RecruitmentAuditEventAdmin(admin.ModelAdmin):
    list_display = ('action', 'identity', 'organization', 'actor', 'object_type', 'created_at')
    list_filter = ('action', 'organization', 'object_type')
    search_fields = ('identity__email_normalized', 'object_id')
    readonly_fields = ('actor', 'identity', 'organization', 'action', 'object_type', 'object_id', 'ip_address', 'metadata', 'created_at')


@admin.register(RecruitmentPolicy)
class RecruitmentPolicyAdmin(admin.ModelAdmin):
    list_display = (
        'organization', 'first_alert_hours', 'priority_window_hours',
        'shopping_pool_after_hours', 'external_pool_after_hours',
        'policy_version', 'active',
    )
    list_filter = ('active',)
    search_fields = ('organization__name',)
    fieldsets = (
        (None, {'fields': ('organization', 'active', 'policy_version')}),
        ('Prazos padrão', {'fields': (
            'candidate_response_hours', 'employer_decision_hours',
            'invite_batch_size', 'round_wait_hours',
        )}),
        ('Distribuição territorial legada', {'fields': (
            'first_alert_hours', 'priority_window_hours',
            'shopping_pool_after_hours', 'external_pool_after_hours',
        )}),
    )


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'organization', 'city', 'status', 'created_at')
    list_filter = ('organization', 'status', 'city', 'state')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'cep')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'city', 'active', 'created_at')
    list_filter = ('organization', 'active', 'city', 'state')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CandidateOnboardingTrail)
class CandidateOnboardingTrailAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'status', 'survey_completed', 'created_at')
    list_filter = ('status', 'survey_completed', 'organization')
    search_fields = ('candidate__first_name', 'candidate__last_name', 'candidate__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CandidateProfileSurveyResponse)
class CandidateProfileSurveyResponseAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'organization')
    list_filter = ('organization',)
    search_fields = ('candidate__first_name', 'candidate__last_name', 'candidate__email')
    readonly_fields = ('candidate', 'organization')


@admin.register(EntryPoint)
class EntryPointAdmin(admin.ModelAdmin):
    list_display = ("label", "kind", "mode", "state", "organization", "scope_store", "created_at")
    list_filter = ("kind", "mode", "state", "organization")
    search_fields = ("label", "canonical_destination_url", "scope_shopping_id", "scope_network_id")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("id", "organization", "label", "kind", "mode", "state")}),
        ("Escopo territorial", {"fields": ("scope_store", "scope_shopping_id", "scope_network_id")}),
        ("Geo", {"fields": ("geo_lat", "geo_lng", "geo_radius_m")}),
        ("PIAG — Integridade", {"fields": ("canonical_destination_url", "tamper_evidence_hash", "activation_tested_at")}),
        ("Responsabilidade", {"fields": ("managed_by",)}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    actions = ["mark_active", "mark_compromised", "mark_revoked"]

    def mark_active(self, request, queryset):
        for ep in queryset:
            if ep.can_activate():
                ep.state = EntryPoint.STATE_ACTIVE
                ep.save(update_fields=["state", "updated_at"])
        self.message_user(request, "EntryPoints elegíveis marcados como ACTIVE.")
    mark_active.short_description = "Ativar (PIAG mínimo)"

    def mark_compromised(self, request, queryset):
        queryset.update(state=EntryPoint.STATE_COMPROMISED)
    mark_compromised.short_description = "Marcar como COMPROMISED"

    def mark_revoked(self, request, queryset):
        queryset.update(state=EntryPoint.STATE_REVOKED)
    mark_revoked.short_description = "Revogar"


class OpportunityCriterionInline(admin.TabularInline):
    model = OpportunityCriterion
    extra = 1
    fields = ('label', 'weight', 'order')


@admin.register(OpportunityCriterion)
class OpportunityCriterionAdmin(admin.ModelAdmin):
    list_display = ('label', 'weight', 'opportunity', 'order')
    list_filter = ('weight',)
    search_fields = ('label',)


@admin.register(OpportunityVersionHistory)
class OpportunityVersionHistoryAdmin(admin.ModelAdmin):
    list_display = ('opportunity', 'from_version', 'to_version', 'created_at', 'triggered_by')
    list_filter = ('to_version',)
    search_fields = ('opportunity__title',)
    readonly_fields = ('opportunity', 'from_version', 'to_version', 'changed_fields', 'triggered_by', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


from .models import Relation, RelationTransitionEvent


class RelationTransitionEventInline(admin.TabularInline):
    model = RelationTransitionEvent
    extra = 0
    readonly_fields = ('from_state', 'to_state', 'actor', 'actor_type', 'authority_scope', 'metadata', 'occurred_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Relation)
class RelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'candidate', 'opportunity', 'opportunity_version', 'state', 'created_at')
    list_filter = ('state', 'opportunity_version')
    search_fields = ('candidate__email', 'opportunity__title')
    readonly_fields = (
        'id', 'candidate', 'opportunity', 'opportunity_version',
        'notice_delivered_at', 'person_interested_at', 'employer_interest_view_at',
        'employer_interested_at', 'no_employer_interest_at', 'matched_at',
        'contact_enabled_at', 'response_created_at', 'closed_at', 'declined_at',
        'created_at', 'updated_at',
    )
    inlines = [RelationTransitionEventInline]


@admin.register(RelationTransitionEvent)
class RelationTransitionEventAdmin(admin.ModelAdmin):
    list_display = ('relation', 'from_state', 'to_state', 'actor_type', 'authority_scope', 'occurred_at')
    list_filter = ('to_state', 'actor_type', 'authority_scope')
    search_fields = ('relation__candidate__email',)
    readonly_fields = ('relation', 'from_state', 'to_state', 'actor', 'actor_type', 'authority_scope', 'metadata', 'occurred_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


from .models import EmployerActor, Ledger


@admin.register(EmployerActor)
class EmployerActorAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'business_unit', 'active', 'human_verified_at')
    list_filter = ('active', 'organization')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'actor_type', 'authority_scope', 'occurred_at', 'actor')
    list_filter = ('event_type', 'actor_type', 'authority_scope')
    search_fields = ('event_type', 'actor__username', 'metadata')
    readonly_fields = ('event_id', 'event_type', 'actor', 'actor_type', 'authority_scope',
                       'relation', 'opportunity', 'opportunity_version', 'candidate', 'entry_point',
                       'policy_version', 'ip_address', 'user_agent', 'metadata', 'occurred_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


from .models import ContactChannel


@admin.register(ContactChannel)
class ContactChannelAdmin(admin.ModelAdmin):
    list_display = ('relation', 'candidate_mobile', 'released_to_actor', 'released_at')
    readonly_fields = ('id', 'relation', 'candidate_mobile', 'employer_contact_name',
                       'employer_mobile', 'employer_email', 'released_to_actor', 'released_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


from .models import RightsCase


@admin.register(RightsCase)
class RightsCaseAdmin(admin.ModelAdmin):
    list_display = ('case_ref', 'request_type', 'verification_state', 'action_state', 'requester_email', 'received_at')
    list_filter = ('request_type', 'verification_state', 'action_state')
    search_fields = ('case_ref', 'requester_email', 'identity__email_normalized')
    readonly_fields = ('case_ref', 'received_at')


from .models import Response as MatchcoResponse


@admin.register(MatchcoResponse)
class MatchcoResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'relation', 'response_class', 'created_by', 'created_at')
    list_filter = ('response_class',)
    readonly_fields = ('id', 'relation', 'response_class', 'note', 'created_by', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


from .models import ProfileSignal


@admin.register(ProfileSignal)
class ProfileSignalAdmin(admin.ModelAdmin):
    list_display = ('profile', 'key', 'freshness_class', 'origin', 'confirmed_at', 'expires_at')
    list_filter = ('freshness_class', 'origin')
    search_fields = ('profile__email', 'key', 'label')
    readonly_fields = ('id', 'expires_at')
