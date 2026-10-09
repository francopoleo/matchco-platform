"""Organization/store adapter for the recruitment bounded context.

The console still supplies a legacy configuration id in the session. This
adapter translates it to recruitment-owned records and synchronizes only the
small organization directory needed by recruitment. No recruitment model has
a foreign key to ``configuration``.
"""

from ..domain_models import (
    RecruitmentChannel,
    RecruitmentCompany,
    RecruitmentJobFunction,
    RecruitmentOrganization,
    RecruitmentStore,
    RecruitmentPhysicalUnit,
)


def _legacy_models():
    """Load the compatibility source only when it is installed."""
    try:
        from configuration.models import BusinessUnit, Company, Organization
    except (ImportError, LookupError):
        return None, None, None
    return Organization, Company, BusinessUnit


def _sync_organization(legacy):
    organization, _ = RecruitmentOrganization.objects.update_or_create(
        legacy_id=legacy.pk,
        defaults={'external_id': f'configuration:{legacy.pk}', 'slug': legacy.slug,
                  'name': legacy.name, 'active': legacy.active},
    )
    return organization


def _sync_company(legacy, organization):
    # Seeds antigos podem ter criado a representação antes de preencher
    # legacy_id. Reutilize-a por organização + nome antes de criar outra;
    # isso mantém a ponte idempotente e respeita a unicidade do tenant.
    company = RecruitmentCompany.objects.filter(legacy_id=legacy.pk).first()
    if company is None:
        company = RecruitmentCompany.objects.filter(
            organization=organization, name=legacy.name,
        ).first()
    values = {
        'organization': organization, 'name': legacy.name,
        'code': getattr(legacy, 'code', '') or '',
        'active': getattr(legacy, 'active', True),
    }
    if company is None:
        company = RecruitmentCompany.objects.create(legacy_id=legacy.pk, **values)
    else:
        for field, value in values.items():
            setattr(company, field, value)
        if company.legacy_id != legacy.pk:
            company.legacy_id = legacy.pk
        company.save(update_fields=[*values.keys(), 'legacy_id'])
    return company


def _sync_channel(legacy, company):
    channel = RecruitmentChannel.objects.filter(legacy_id=legacy.pk).first()
    if channel is None:
        channel = RecruitmentChannel.objects.filter(company=company, name=legacy.name).first()
    values = {'company': company, 'name': legacy.name, 'active': getattr(legacy, 'active', True)}
    if channel is None:
        channel = RecruitmentChannel.objects.create(legacy_id=legacy.pk, **values)
    else:
        for field, value in values.items():
            setattr(channel, field, value)
        channel.legacy_id = legacy.pk
        channel.save(update_fields=[*values.keys(), 'legacy_id'])
    return channel


def _sync_store(legacy, organization=None):
    legacy_company = legacy.company
    organization = organization or _sync_organization(legacy_company.organization)
    company = _sync_company(legacy_company, organization)
    channel = _sync_channel(legacy.channel, company) if legacy.channel else None
    physical_location = getattr(legacy, 'physical_location', None)
    physical_unit = None
    if physical_location:
        physical_unit, _ = RecruitmentPhysicalUnit.objects.update_or_create(
            external_key=physical_location.external_key,
            defaults={
                'name': physical_location.name,
                'postal_code': physical_location.cep,
                'city': physical_location.city,
                'state': physical_location.state,
                'active': physical_location.active,
            },
        )
    store = RecruitmentStore.objects.filter(legacy_id=legacy.pk).first()
    if store is None:
        store = RecruitmentStore.objects.filter(
            organization=organization, company=company, name=legacy.name,
        ).first()
    values = {
        'organization': organization, 'company': company, 'channel': channel,
        'physical_unit': physical_unit,
        'name': legacy.name, 'code': getattr(legacy, 'code', '') or '',
        'active': getattr(legacy, 'active', True),
        'latitude': getattr(legacy, 'latitude', None),
        'longitude': getattr(legacy, 'longitude', None),
    }
    if store is None:
        store = RecruitmentStore.objects.create(legacy_id=legacy.pk, **values)
    else:
        for field, value in values.items():
            setattr(store, field, value)
        store.legacy_id = legacy.pk
        store.save(update_fields=[*values.keys(), 'legacy_id'])
    return store


def _sync_job_function(legacy, organization=None):
    legacy_company = legacy.company
    organization = organization or _sync_organization(legacy_company.organization)
    company = _sync_company(legacy_company, organization)
    function = RecruitmentJobFunction.objects.filter(legacy_id=legacy.pk).first()
    if function is None:
        function = RecruitmentJobFunction.objects.filter(
            organization=organization, company=company, name=legacy.name,
        ).first()
    values = {
        'organization': organization, 'company': company, 'name': legacy.name,
        'active': getattr(legacy, 'active', True),
    }
    if function is None:
        function = RecruitmentJobFunction.objects.create(legacy_id=legacy.pk, **values)
    else:
        for field, value in values.items():
            setattr(function, field, value)
        function.legacy_id = legacy.pk
        function.save(update_fields=[*values.keys(), 'legacy_id'])
    function.channels.set([_sync_channel(channel, company) for channel in legacy.channels.all()])
    return function


def find_organization(*, slug=None, pk=None):
    LegacyOrganization, _, _ = _legacy_models()
    legacy = None
    if LegacyOrganization and pk:
        legacy = LegacyOrganization.objects.filter(pk=pk).first()
    elif LegacyOrganization and slug:
        legacy = LegacyOrganization.objects.filter(slug=slug).first()
    if legacy:
        return _sync_organization(legacy)
    qs = RecruitmentOrganization.objects.all()
    return qs.filter(slug=slug).first() if slug else qs.filter(legacy_id=pk).first() if pk else None


def active_organizations():
    LegacyOrganization, _, _ = _legacy_models()
    if LegacyOrganization:
        for legacy in LegacyOrganization.objects.filter(active=True).order_by('name'):
            _sync_organization(legacy)
    return RecruitmentOrganization.objects.filter(active=True).order_by('name')


def find_store(*, store_id, organization=None):
    _, _, LegacyStore = _legacy_models()
    if not LegacyStore:
        return RecruitmentStore.objects.filter(legacy_id=store_id).first()
    legacy_qs = LegacyStore.objects.filter(pk=store_id)
    if organization is not None and getattr(organization, 'legacy_id', None):
        legacy_qs = legacy_qs.filter(company__organization_id=organization.legacy_id)
    legacy = legacy_qs.select_related('company', 'channel').first()
    return _sync_store(legacy, organization) if legacy else RecruitmentStore.objects.filter(legacy_id=store_id).first()


def stores_for_organization(organization):
    _, _, LegacyStore = _legacy_models()
    legacy_id = getattr(organization, 'legacy_id', None)
    if legacy_id and LegacyStore:
        for legacy in LegacyStore.objects.filter(company__organization_id=legacy_id).select_related('company', 'channel'):
            _sync_store(legacy, organization)
    return RecruitmentStore.objects.filter(organization=organization, active=True).order_by('name')


def job_functions_for_store(store):
    _, _, LegacyStore = _legacy_models()
    if store.legacy_id and LegacyStore:
        legacy = LegacyStore.objects.filter(pk=store.legacy_id).select_related('company').first()
        if legacy:
            for legacy_function in legacy.company.job_functions.filter(active=True):
                _sync_job_function(legacy_function, store.organization)
    qs = RecruitmentJobFunction.objects.filter(company=store.company, active=True)
    return qs.filter(channels=store.channel).distinct() if store.channel else qs


def job_functions_for_organization(organization):
    _, LegacyCompany, _ = _legacy_models()
    legacy_id = getattr(organization, 'legacy_id', None)
    if legacy_id and LegacyCompany:
        legacy_company = LegacyCompany.objects.filter(organization_id=legacy_id).first()
        if legacy_company:
            for legacy_function in legacy_company.job_functions.filter(active=True):
                _sync_job_function(legacy_function, organization)
    return RecruitmentJobFunction.objects.filter(organization=organization, active=True)


def employee_store_for_request(request, organization):
    try:
        membership = request.user.memberships.filter(
            organization_id=getattr(organization, 'legacy_id', None),
            active=True,
        ).order_by('-is_primary', '-created_at').first()
    except AttributeError:
        return None
    if not membership or not membership.business_unit_id:
        return None
    return find_store(store_id=membership.business_unit_id, organization=organization)


def has_recruitment_access(request, organization, *, write=False):
    """Check organization and store scope without leaking tenant records."""
    if getattr(request.user, 'is_superuser', False):
        return True
    legacy_id = getattr(organization, 'legacy_id', None)
    if not legacy_id:
        return False
    try:
        memberships = request.user.memberships.filter(organization_id=legacy_id, active=True)
    except AttributeError:
        return False
    membership = memberships.order_by('-is_primary', '-created_at').first()
    if not membership:
        return False
    if membership.role in {'owner', 'admin'}:
        return True
    if write and membership.role not in {'member'}:
        return False
    return True
