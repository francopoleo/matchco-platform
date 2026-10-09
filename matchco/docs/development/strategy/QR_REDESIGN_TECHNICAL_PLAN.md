# MatchCo QR/Recruitment Flow Redesign — Technical Plan

**Date:** 2026-10-07 | **Author:** Claude Code

> **SUPERSEDED — 2026-10-09.** Este rascunho propõe QR compartilhado por
> organização, seleção de loja pelo candidato e jornadas `vaga`/`hybrid` que
> foram rejeitadas. Não é fonte de implementação. A regra vigente é um QR Match
> por unidade, formulário de alto giro sem CV, origem privada e circulação
> definida por consentimento territorial explícito. Consulte
> `MATCHCO_VALIDATION_PLAN.md` e `MATCHCO_MASTER_PLAN.md`.

---

## Executive Summary

This plan redesigns the current **single-store QR model** into a **unified multi-store QR system** with **customizable signup forms per store**. 

**Current state:** 1 QR per store (N QRs for N stores, each with fixed generic form)
**Proposed state:** 1 QR per organization (shared), store-specific form customization, optional job application flow

**Key outcomes:**
- Operational simplicity: Print one QR instead of many
- Better UX: Candidates choose store at scan time
- Flexibility: Each store defines its own required fields/questions
- Audit trail: Track answers per store + entry point

---

## Part 1: Data Architecture

### Current State (Baseline)

**EntryPoint Model** (`recruitment.models.EntryPoint`):
- 1 QR per store: `scope_store` FK → single `BusinessUnit`
- `kind = 'store'` implies one-to-one relationship
- `mode` (match/vaga/hybrid) is per-QR
- No questionnaire linkage to entry points

**CandidateProfile Model**:
- `preferred_store` FK (optional) — where candidate applied
- `qr_id` CharField — stores EntryPoint UUID
- Generic fields only: name, email, phone, bio, experience_years
- No per-store custom fields

**QuestionnaireTemplate** (already exists):
- Has `scope_store` FK for store-specific templates
- Has `entry_point` FK for EP-specific templates
- Versioned (`version` field)
- `QuestionnaireQuestion` children with question definitions

**Current Gap:** No model to define "which questions should this store display to candidates"

---

### New Data Models

#### 1. **StoreSignupConfiguration** (NEW)

Configures signup form customization per BusinessUnit. Answers: "What questions/fields should we ask candidates for this store?"

```python
class StoreSignupConfiguration(models.Model):
    """
    Configures customizable signup form for each store.
    Links store → questionnaire template + required fields.
    """
    
    VAGA_MODE = 'vaga'
    MATCH_MODE = 'match'
    MODE_CHOICES = [
        (VAGA_MODE, 'Porta Vaga'),
        (MATCH_MODE, 'Porta Match'),
    ]
    
    id = models.AutoField(primary_key=True)
    
    # Store relationship (OneToOne: one config per store)
    business_unit = models.OneToOneField(
        BusinessUnit,
        related_name='signup_configuration',
        on_delete=models.CASCADE,
    )
    
    # Organization scope
    organization = models.ForeignKey(
        Organization,
        related_name='store_signup_configs',
        on_delete=models.CASCADE,
    )
    
    # Optional: if set, only use this config with this specific QR
    entry_point = models.ForeignKey(
        EntryPoint,
        null=True,
        blank=True,
        related_name='store_configs',
        on_delete=models.CASCADE,
    )
    
    # Which questionnaire to display
    questionnaire_template = models.ForeignKey(
        QuestionnaireTemplate,
        null=True,
        blank=True,
        related_name='store_configs',
        on_delete=models.SET_NULL,
    )
    
    # Required base fields (always shown)
    require_phone = models.BooleanField(default=True)
    require_experience = models.BooleanField(default=True)
    require_location = models.BooleanField(default=True)
    
    # Default mode for this store's candidates
    default_mode = models.CharField(
        max_length=10,
        choices=MODE_CHOICES,
        default=MATCH_MODE,
    )
    
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Store Signup Configuration'
        ordering = ['business_unit__name']
        indexes = [
            models.Index(fields=['organization', 'enabled']),
            models.Index(fields=['entry_point', 'enabled']),
        ]
```

#### 2. **CandidateSignupAnswer** (NEW)

Immutable record of candidate's answers to store-specific questions.

```python
class CandidateSignupAnswer(models.Model):
    """
    Records candidate's answers when signing up via a store.
    Audit trail: one entry per signup attempt per store.
    """
    
    candidate = models.ForeignKey(
        CandidateProfile,
        related_name='signup_answers',
        on_delete=models.CASCADE,
    )
    
    # Which store did they sign up for?
    business_unit = models.ForeignKey(
        BusinessUnit,
        related_name='candidate_signup_answers',
        on_delete=models.CASCADE,
    )
    
    # Which QR + questionnaire template were used?
    entry_point = models.ForeignKey(
        EntryPoint,
        null=True,
        blank=True,
        related_name='candidate_signup_answers',
        on_delete=models.SET_NULL,
    )
    
    questionnaire_template = models.ForeignKey(
        QuestionnaireTemplate,
        null=True,
        blank=True,
        related_name='signup_answers',
        on_delete=models.SET_NULL,
    )
    
    # JSON: {question_key: answer_value, ...}
    # Same format as CandidateProfileSurveyResponse.responses
    responses = models.JSONField(default=dict, blank=True)
    
    # Optional: did they also apply to a specific job?
    position = models.ForeignKey(
        Position,
        null=True,
        blank=True,
        related_name='signup_answers',
        on_delete=models.SET_NULL,
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Candidate Signup Answer'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['candidate', 'business_unit']),
            models.Index(fields=['entry_point', 'created_at']),
        ]
```

#### 3. **EntryPoint Model — Changes**

```python
# Add to EntryPoint:

# NEW: Support org-wide QR (not store-specific)
KIND_ORGANIZATION = 'organization'
# Update KIND_CHOICES to include:
# (KIND_ORGANIZATION, _('Organização (multi-loja)'))

# NEW: Does this QR allow store selection?
allows_store_selection = models.BooleanField(
    default=False,
    help_text='Show store selector when scanned; if False, use scope_store or redirect',
)

# NEW: If set, restrict store selector to these stores
# (if blank, show all stores in organization)
allowed_stores = models.ManyToManyField(
    BusinessUnit,
    blank=True,
    related_name='entry_points_allowed',
    help_text='Stores available in selector. Blank = all stores in org.',
)
```

---

### Data Model Examples

#### BEFORE (Current State)

```
Organization "Bourbon":
  ├─ EntryPoint (QR-001)
  │  ├─ id: uuid-111
  │  ├─ scope_store → Loja A
  │  ├─ kind: 'store'
  │  └─ mode: 'match'
  │
  ├─ EntryPoint (QR-002)
  │  ├─ id: uuid-222
  │  ├─ scope_store → Loja B
  │  ├─ kind: 'store'
  │  └─ mode: 'hybrid'
  │
  └─ EntryPoint (QR-003)
     ├─ id: uuid-333
     ├─ scope_store → Loja C
     ├─ kind: 'store'
     └─ mode: 'vaga'

Candidate scans QR-001:
→ Redirects directly to signup for Loja A
→ Generic form (name, email, phone, experience)
```

#### AFTER (Proposed)

```
Organization "Bourbon":
  └─ EntryPoint (QR ÚNICO)
     ├─ id: uuid-universal
     ├─ scope_store: NULL
     ├─ kind: 'organization'
     ├─ allows_store_selection: True
     ├─ allowed_stores: [Loja A, Loja B, Loja C]
     └─ mode: 'hybrid'

  ├─ StoreSignupConfiguration (Loja A)
  │  ├─ business_unit → Loja A
  │  ├─ questionnaire_template → "Loja A v1"
  │  └─ default_mode: 'match'
  │
  ├─ StoreSignupConfiguration (Loja B)
  │  ├─ business_unit → Loja B
  │  ├─ questionnaire_template → "Loja B v2"
  │  └─ default_mode: 'hybrid'
  │
  └─ StoreSignupConfiguration (Loja C)
     ├─ business_unit → Loja C
     ├─ questionnaire_template → "Loja C v1"
     └─ default_mode: 'vaga'

Candidate scans QR ÚNICO:
1. "Escolha sua loja" → [Loja A] [Loja B] [Loja C]
2. Clicks "Loja A"
3. "O que você quer fazer?"
   → [Perfil geral]
   → [Candidatar a Vaga X (Gerente)]
   → [Candidatar a Vaga Y (Atendente)]
4. Completes form with Loja A's custom questions
5. CandidateSignupAnswer created + CandidateProfile updated
```

---

### Database Migrations

**Migration 0037:** `recruitment_storesignupconfiguration`

```sql
CREATE TABLE recruitment_storesignupconfiguration (
  id SERIAL PRIMARY KEY,
  business_unit_id INTEGER NOT NULL UNIQUE 
    REFERENCES recruitment_store(id),
  entry_point_id UUID NULL 
    REFERENCES recruitment_entrypoint(id),
  organization_id INTEGER NOT NULL 
    REFERENCES recruitment_organization(id),
  questionnaire_template_id INTEGER NULL 
    REFERENCES recruitment_questionnairetemplate(id),
  require_phone BOOLEAN DEFAULT true,
  require_experience BOOLEAN DEFAULT true,
  require_location BOOLEAN DEFAULT true,
  default_mode VARCHAR(10) DEFAULT 'match',
  enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_store_signup_org_enabled 
  ON recruitment_storesignupconfiguration(organization_id, enabled);
CREATE INDEX idx_store_signup_ep_enabled
  ON recruitment_storesignupconfiguration(entry_point_id, enabled);
```

**Migration 0038:** `recruitment_candidatesignupanswer`

```sql
CREATE TABLE recruitment_candidatesignupanswer (
  id BIGSERIAL PRIMARY KEY,
  candidate_id INTEGER NOT NULL 
    REFERENCES recruitment_candidateprofile(id),
  business_unit_id INTEGER NOT NULL 
    REFERENCES recruitment_store(id),
  entry_point_id UUID NULL 
    REFERENCES recruitment_entrypoint(id),
  questionnaire_template_id INTEGER NULL 
    REFERENCES recruitment_questionnairetemplate(id),
  position_id INTEGER NULL 
    REFERENCES recruitment_position(id),
  responses JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cand_signup_ans_candidate_store
  ON recruitment_candidatesignupanswer(candidate_id, business_unit_id);
CREATE INDEX idx_cand_signup_ans_ep_created
  ON recruitment_candidatesignupanswer(entry_point_id, created_at);
```

**Migration 0039:** `entrypoint_org_mode`

```python
# In Django migration:
# 1. Add allows_store_selection (default False)
# 2. Create M2M table for allowed_stores
# 3. No data migration needed initially (legacy QRs keep current behavior)
```

---

## Part 2: View/URL Flow

### Current URLs (Reference)

From `urls_public.py`:
- `qr/<uuid:entry_point_id>/` → `EntryPointResolveView` (resolves & redirects)
- `candidato/signup/` → `MatchcoSignupView` (generic signup)
- `candidato/vaga/cadastro/` → `CandidateSignupView` (formal job signup)

### New URL Structure

```
POST /qr/<uuid:entry_point_id>/
  → EntryPointResolveView (unchanged, but now routes to store_chooser)

GET /candidato/escolher-loja/<uuid:entry_point_id>/
  → StoreChooserView (NEW)
  → Shows list of available stores
  → Sets session: selected_store_id, ep_id, ep_mode, etc.

GET /candidato/escolher-tipo/<uuid:entry_point_id>/?store_id=<id>
  → ActionChooserView (NEW)
  → "Perfil geral" vs. "Candidatar a vaga"
  → If vaga: show list of open positions at that store
  → Sets session: action_type, position_id (if applicable)

POST /candidato/signup-customizado/<uuid:entry_point_id>/?store_id=<id>
  → CustomSignupView (MODIFIED)
  → Loads StoreSignupConfiguration for selected store
  → Dynamically renders form with custom questions
  → Creates CandidateProfile + CandidateSignupAnswer
  → Redirects to success page or OTP verification
```

---

### View Flow Diagram

```
QR Scan
  ↓
EntryPointResolveView (existing)
  ├─ Validates: state == ACTIVE
  ├─ Sets session: ep_id, ep_mode, ep_kind, etc.
  └─ Redirects based on kind + mode
      ├─ If kind='organization' & allows_store_selection=True
      │  → Redirect to StoreChooserView
      │
      ├─ If kind='store' (legacy)
      │  → Redirect to signup (OLD FLOW)
      │
      └─ If kind='organization' & allows_store_selection=False
         → Redirect to signup (org-wide, no store choice)

StoreChooserView (NEW)
  ├─ Fetch EntryPoint
  ├─ Fetch allowed_stores (or all org stores)
  ├─ Render store selector UI
  └─ POST → StoreChooserView
      ├─ Validate store_id
      ├─ Set session: selected_store_id
      └─ Redirect to ActionChooserView

ActionChooserView (NEW)
  ├─ Fetch selected store + open positions
  ├─ Render: [Perfil geral] [Vaga X] [Vaga Y] ...
  └─ POST → ActionChooserView
      ├─ Set session: action_type, position_id (if applicable)
      └─ Redirect to CustomSignupView

CustomSignupView (MODIFIED)
  ├─ Fetch StoreSignupConfiguration for selected store
  ├─ Fetch QuestionnaireTemplate
  ├─ Dynamically build form:
  │  ├─ Base fields (name, email, phone, etc.)
  │  ├─ Custom questions from template
  │  └─ Position-specific questions (if applicable)
  ├─ Render HTML
  └─ POST → CustomSignupView
      ├─ Validate responses
      ├─ Create/update CandidateProfile
      ├─ Create CandidateSignupAnswer (audit trail)
      ├─ Log to Ledger (if applicable)
      └─ Redirect to:
          ├─ Success page, or
          ├─ OTP verification, or
          └─ Next onboarding step
```

---

### Session Data Structure

```python
# session keys used during flow

request.session = {
    # Entry point context (set by EntryPointResolveView)
    'ep_id': 'uuid-universal',
    'ep_mode': 'hybrid',  # match/vaga/hybrid
    'ep_kind': 'organization',
    'ep_purpose': 'recruitment',
    'ep_audience': 'candidate',
    'ep_audience_role': 'candidate',
    
    # Store selection (set by StoreChooserView)
    'selected_store_id': 1,  # BusinessUnit.id
    
    # Action type (set by ActionChooserView)
    'action_type': 'general_profile',  # or 'apply_position'
    'position_id': 123,  # if action_type == 'apply_position'
    
    # Candidate creation (set by CustomSignupView)
    'candidate_id': 456,
    'pending_otp_phone': '+55 11 99999-9999',
    
    # LGPD consent tracking
    'consent_flow_started_at': '2026-10-07T...',
}
```

---

### Detailed View Implementation: CustomSignupView

**Current behavior:**
```python
class MatchcoSignupView(TemplateView):
    template_name = 'recruitment/match/signup.html'
    
    def get(self, request):
        # Generic form: name, email, phone, bio, etc.
        # Questionnaire (if any) is loaded post-signup
        ...
```

**New behavior:**
```python
class CustomSignupView(TemplateView):
    template_name = 'recruitment/custom_signup.html'
    
    def get(self, request, entry_point_id):
        # Load selected store from session
        store_id = request.session.get('selected_store_id')
        if not store_id:
            return redirect('storeChooser', entry_point_id=entry_point_id)
        
        # Fetch store config
        try:
            config = StoreSignupConfiguration.objects.get(
                business_unit_id=store_id,
                enabled=True
            )
        except StoreSignupConfiguration.DoesNotExist:
            # Fallback to generic config
            config = None
        
        # Fetch questionnaire if configured
        questionnaire = None
        if config and config.questionnaire_template:
            questionnaire = config.questionnaire_template
        
        # Build form schema dynamically
        form_schema = self._build_form_schema(config, questionnaire)
        
        context = {
            'form_schema': form_schema,
            'store': business_unit,
            'position': position_if_applicable,
        }
        return render(request, self.template_name, context)
    
    def _build_form_schema(self, config, questionnaire):
        """Build form field definitions from config + questionnaire."""
        schema = {
            'sections': [
                {
                    'title': 'Informações Básicas',
                    'fields': [
                        {'key': 'first_name', 'label': 'Nome', 'type': 'text', 'required': True},
                        {'key': 'email', 'label': 'Email', 'type': 'email', 'required': True},
                    ]
                }
            ]
        }
        
        # Add phone if required by config
        if config and config.require_phone:
            schema['sections'][0]['fields'].append({
                'key': 'phone', 'label': 'Telefone', 'type': 'phone', 'required': True
            })
        
        # Add experience if required
        if config and config.require_experience:
            schema['sections'][0]['fields'].append({
                'key': 'experience_years', 'label': 'Anos de experiência', 'type': 'number'
            })
        
        # Add custom questions from questionnaire
        if questionnaire:
            custom_section = {
                'title': questionnaire.name,
                'fields': []
            }
            for question in questionnaire.questions.filter(active=True).order_by('order'):
                custom_section['fields'].append({
                    'key': question.key,
                    'label': question.label,
                    'type': question.field_type,
                    'required': question.required,
                    'options': question.options if question.options else None,
                })
            schema['sections'].append(custom_section)
        
        return schema
    
    def post(self, request, entry_point_id):
        # Extract session & form data
        store_id = request.session.get('selected_store_id')
        position_id = request.session.get('position_id')
        
        # Validate & create candidate
        data = request.POST.dict()
        
        # Check existing candidate (by email)
        candidate, created = CandidateProfile.objects.get_or_create(
            organization_id=ep.organization_id,
            email=data['email'],
            defaults={
                'first_name': data['first_name'],
                'email': data['email'],
                'phone': data.get('phone', ''),
                'preferred_store_id': store_id,
                'qr_id': str(entry_point_id),
            }
        )
        
        # Extract answers to custom questions
        config = StoreSignupConfiguration.objects.get(business_unit_id=store_id)
        questionnaire = config.questionnaire_template
        
        custom_responses = {}
        if questionnaire:
            for q in questionnaire.questions.filter(active=True):
                if q.key in data:
                    custom_responses[q.key] = data[q.key]
        
        # Create signup answer (audit trail)
        CandidateSignupAnswer.objects.create(
            candidate=candidate,
            business_unit_id=store_id,
            entry_point_id=entry_point_id,
            questionnaire_template=questionnaire,
            position_id=position_id,
            responses=custom_responses,
        )
        
        # Log to Ledger (append-only audit)
        if questionnaire:
            from .models import Ledger
            Ledger.objects.create(
                type='CANDIDATE_SIGNUP',
                identity=candidate.identity,
                organization=candidate.organization,
                details={
                    'store_id': store_id,
                    'questionnaire_template': questionnaire.code,
                    'responses_count': len(custom_responses),
                }
            )
        
        # Redirect to OTP or success
        request.session['candidate_id'] = candidate.id
        return redirect('recruitment_public:candidato_entrar_codigo')
```

---

## Part 3: Implementation Roadmap

### Phase 0: Planning & Design (3 days)
- Design reviews with FE/BE team
- Data model review + schema design
- Create migration scripts
- Set up feature flag (NEW_QR_FLOW)

**Deliverables:**
- Approved data model
- Migration files (0037, 0038, 0039)
- Feature flag configuration

---

### Phase 1: Database & Models (4 days)

**Backend:**
- Create `StoreSignupConfiguration` model + migrations
- Create `CandidateSignupAnswer` model + migrations
- Update `EntryPoint` model with `allows_store_selection` + M2M
- Add model tests: creation, validation, relationships
- Add admin views for both new models

**Database:**
- Create migrations
- Test on staging database
- Verify indexes + performance

**Effort:** 4 dev days

---

### Phase 2: Views & URLs (6 days)

**New Views:**
1. `StoreChooserView` (GET/POST)
   - Fetch allowed stores from EntryPoint
   - Render store selector UI
   - Session management
   - Tests

2. `ActionChooserView` (GET/POST)
   - Show open positions for store
   - "Profile only" vs. "Apply to job"
   - Fetch + render positions dynamically
   - Tests

3. `CustomSignupView` (refactor from existing signup)
   - Dynamic form schema from StoreSignupConfiguration
   - Load questionnaire if configured
   - Validate custom answers
   - Create CandidateSignupAnswer audit record
   - Tests

**URL Updates:**
- Update `EntryPointResolveView` to route to store chooser (conditional on kind='organization')
- Add new URL paths
- Backward-compat: old QRs (kind='store') continue working

**Frontend:**
- Create store selector UI template
- Create action chooser UI template
- Create dynamic form builder (JS + Django template)

**Effort:** 6 dev days

---

### Phase 3: Console/Admin (5 days)

**Console Features:**
1. **QR Configuration**
   - UI to create org-wide QR
   - Toggle `allows_store_selection`
   - Pick `allowed_stores` (multi-select)
   - Show link to generate QR code

2. **Store Configuration**
   - For each store, configure:
     - Which questionnaire to use
     - Which fields to require (phone, experience, location)
     - Default mode (match/vaga)
   - Bulk-edit multiple stores
   - Tests

3. **Reporting**
   - Signup answers per store
   - Response rate by question
   - Audit trail view (CandidateSignupAnswer records)

**Effort:** 5 dev days

---

### Phase 4: Testing & QA (4 days)

**QA:**
- Integration tests (E2E flows)
  - Scan QR → choose store → fill form → candidate created
  - Verify session data correctly passed
  - Verify CandidateSignupAnswer created + linked
  
- Edge cases:
  - Existing candidate re-signing for different store
  - Position-specific flow
  - Missing questionnaire (fallback)
  - Empty allowed_stores (all stores)
  
- Backward-compat tests:
  - Old QRs (kind='store') still work
  - Existing candidates unaffected
  
- Performance:
  - Load test store chooser with 100+ stores
  - Verify form rendering speed with large questionnaires

**Effort:** 4 dev days (including test automation)

---

### Phase 5: Deployment & Monitoring (2 days)

**Rollout:**
1. Deploy migrations (safe: additive only, no deletions)
2. Deploy code with feature flag OFF (no-op)
3. Manual QA on staging
4. Enable feature flag for 10% of orgs (canary)
5. Monitor: error rates, response times, signup completion
6. Rollout to 50%, then 100%

**Monitoring:**
- Track signup completion rate (before/after)
- Monitor new view response times
- Watch for database query performance issues
- Alert on Ledger write failures

**Effort:** 2 dev days (mostly deployment + monitoring)

---

### Timeline Summary

| Phase | Duration | Key Deliverable |
|-------|----------|-----------------|
| Phase 0 | 3 days | Approved design, migrations |
| Phase 1 | 4 days | DB + models + admin |
| Phase 2 | 6 days | Views + URLs + templates |
| Phase 3 | 5 days | Console features |
| Phase 4 | 4 days | Testing + edge cases |
| Phase 5 | 2 days | Deploy + monitor |
| **Total** | **24 days** | Full rollout (5-6 weeks at 4 dev days/week) |

---

## Part 4: Backwards Compatibility

### Strategy

**Goal:** Existing QRs continue working; new QRs use new flow.

### Approach

#### 1. **No Data Migration Needed**

Existing `EntryPoint` records remain unchanged:
- `kind = 'store'` (unchanged)
- `scope_store` points to specific store (unchanged)
- `allows_store_selection = False` (default)
- No M2M entries (allowed_stores is empty)

Existing `CandidateProfile` records remain unchanged.

#### 2. **EntryPointResolveView Logic (Backward-Compat)**

```python
def get(self, request, entry_point_id):
    ep = EntryPoint.objects.get(pk=entry_point_id)
    
    # Set session (unchanged)
    request.session['ep_id'] = str(ep.id)
    request.session['ep_mode'] = ep.mode
    ...
    
    # NEW: Check if this is multi-store QR
    if ep.kind == 'organization' and ep.allows_store_selection:
        # New flow: store chooser
        return redirect('recruitment_public:store_chooser', entry_point_id=ep.pk)
    
    # OLD flow: unchanged
    if ep.mode == EntryPoint.MODE_HYBRID:
        return redirect('recruitment_public:entry_point_choice', ...)
    if ep.mode == EntryPoint.MODE_VAGA:
        return redirect('recruitment_public:candidato_vaga_signup', ...)
    return redirect('recruitment_public:candidato_signup')
```

#### 3. **CustomSignupView Fallback**

If `StoreSignupConfiguration` not found:
```python
# Fallback to existing behavior (generic form)
if not config:
    return redirect('recruitment_public:candidato_signup')
```

#### 4. **Feature Flag (Optional but Recommended)**

Add Django setting:
```python
FEATURES = {
    'RECRUITMENT_NEW_QR_FLOW': False,  # Initially off
}
```

Wrap new views:
```python
def store_chooser(request, entry_point_id):
    if not settings.FEATURES.get('RECRUITMENT_NEW_QR_FLOW'):
        # Redirect to old flow
        return redirect('recruitment_public:candidato_signup')
    ...
```

### Data Safety

| Object | Change | Safe? | Notes |
|--------|--------|-------|-------|
| EntryPoint | Add fields | ✅ | Backward-compat: defaults allow old behavior |
| CandidateProfile | Unchanged | ✅ | No migrations needed |
| StoreSignupConfiguration | New table | ✅ | Optional; no FK required from existing tables |
| CandidateSignupAnswer | New table | ✅ | Optional; audit trail only |

### Rollback Plan

If issues discovered:
1. Disable feature flag
2. Old QRs continue working (unchanged flow)
3. New QRs revert to generic signup
4. No data loss

---

## Part 5: Console/Admin Changes

### Current Console State

**Recruitment → QR Management:**
- List all EntryPoints
- Create QR code (per store)
- View details (scope_store, mode, state)
- Activate/revoke QR
- Download QR image

### New Console Features

#### 1. **QR Creation Flow (Revised)**

**OLD:**
1. Select store → Create QR → Download
2. Repeat for each store

**NEW (Option A: Single QR per Org):**
1. Organization → Create QR
2. Set `kind = 'organization'`
3. Toggle `allows_store_selection`
4. Pick `allowed_stores` (multi-select)
5. Download single QR → use everywhere

**NEW (Option B: Continue Creating Store-Specific QRs):**
- Existing "create per store" flow still available
- New "create org-wide" option

#### 2. **Store Configuration UI (New Tab)**

**Path:** Console → Recruitment → Store Configurations

**Features:**
- List all stores
- For each store:
  - Select questionnaire template (dropdown)
  - Toggle required fields: phone, experience, location
  - Set default mode: match / vaga
  - View signup answers (link to list view)

**Form Example:**
```
┌─────────────────────────────────────────┐
│ Store Configuration: Loja A             │
├─────────────────────────────────────────┤
│ Questionnaire Template:                 │
│ [Dropdown: "Loja A Onboarding v2"]      │
│                                         │
│ Required Fields:                        │
│ ☑ Phone Number                          │
│ ☑ Years of Experience                   │
│ ☑ Location (CEP)                        │
│                                         │
│ Default Mode:                           │
│ ◉ Match    ○ Vaga    ○ Hybrid           │
│                                         │
│ [Save Changes]                          │
└─────────────────────────────────────────┘
```

#### 3. **Questionnaire Management (Existing + Enhanced)**

**Path:** Console → Recruitment → Questionnaires

**Changes:**
- Add `scope_store` FK (already exists, but enhance UI)
- Link to StoreSignupConfiguration
- Show "used by X stores" indicator
- Bulk-assign questionnaire to multiple stores

#### 4. **Signup Answers Reporting (New List View)**

**Path:** Console → Recruitment → Signup Answers

**Features:**
- Filter by store, date range, entry point
- Export to CSV
- View per-candidate answers
- Analytics: "Top unanswered questions"

**Table Columns:**
| Date | Candidate | Store | Questions Answered | Position | Status |
|------|-----------|-------|-------------------|----------|--------|
| 2026-10-07 | João Silva | Loja A | 5/6 | Gerente | ✓ Onboarded |
| 2026-10-07 | Maria Santos | Loja B | 4/6 | — | Pending OTP |

#### 5. **Audit Trail / Ledger Viewer (Enhanced)**

**Path:** Console → Recruitment → Audit Log

**Addition:**
- New log type: `CANDIDATE_SIGNUP_CUSTOMIZED`
- Show questionnaire + response count
- Link to CandidateSignupAnswer record

---

### Admin UI Components

#### Questionnaire Template Admin (Updated)

```python
class StoreSignupConfigurationInline(admin.TabularInline):
    model = StoreSignupConfiguration
    extra = 0
    fields = ('business_unit', 'default_mode', 'require_phone', 'enabled')
    readonly_fields = ('business_unit',)

class QuestionnaireTemplateAdmin(admin.ModelAdmin):
    # existing fields...
    inlines = [StoreSignupConfigurationInline]
```

#### StoreSignupConfiguration Admin (New)

```python
class StoreSignupConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'business_unit__name',
        'organization__name',
        'questionnaire_template__name',
        'default_mode',
        'enabled',
    )
    list_filter = ('organization', 'enabled', 'default_mode')
    search_fields = ('business_unit__name',)
    
    fieldsets = (
        ('Store Info', {
            'fields': ('business_unit', 'organization', 'entry_point'),
        }),
        ('Questionnaire', {
            'fields': ('questionnaire_template',),
        }),
        ('Required Fields', {
            'fields': ('require_phone', 'require_experience', 'require_location'),
        }),
        ('Defaults', {
            'fields': ('default_mode', 'enabled'),
        }),
    )
```

---

## Part 6: Key Design Decisions

### 1. **OneToOne vs. ForeignKey for StoreSignupConfiguration**

**Decision:** OneToOne (business_unit → signup_configuration)

**Rationale:**
- Simplifies queries: `store.signup_configuration` (no filter needed)
- Prevents multiple configs per store (data integrity)
- Easier to update: always one config to modify

**Trade-off:** Cannot have multiple questionnaire variants per store without creating new stores

---

### 2. **CandidateSignupAnswer as Audit Trail (NOT One-to-One)**

**Decision:** ForeignKey (candidate → multiple signup_answers)

**Rationale:**
- Candidate can sign up multiple times (different QRs, different stores)
- Audit trail: track all signup attempts
- Later analysis: "why did this candidate signup twice?"

**Example:**
```
Candidate "João Silva"
├─ CandidateSignupAnswer (Oct 1, Loja A, QR-1)
├─ CandidateSignupAnswer (Oct 3, Loja B, QR-2)
└─ CandidateSignupAnswer (Oct 5, Loja A, QR-1, applied to Vaga X)
```

---

### 3. **M2M for allowed_stores (vs. Text List)**

**Decision:** M2M relationship (EntryPoint.allowed_stores)

**Rationale:**
- Django ORM handles queries efficiently
- Admin UI: multi-select widget
- Scalable: works with 10 or 1000 stores

---

### 4. **JSON for Responses (vs. Relational)**

**Decision:** JSON in CandidateSignupAnswer.responses

**Rationale:**
- Flexible: questionnaire can change without migrations
- Versioning: exact questionnaire state captured (questionnaire_template_id)
- Performance: single record per signup, no per-question rows

**Example:**
```json
{
  "experiencia_caixa": "3 anos",
  "idiomas": ["Portuguese", "English"],
  "disponibilidade": "Segunda a Sexta, 08:00-18:00"
}
```

---

### 5. **Backwards Compatibility via Feature Flag (Optional)**

**Decision:** Recommended but not required

**Rationale:**
- Graceful rollout: test with 10% of orgs first
- Safe rollback: flip flag if issues found
- No data loss: old QRs unaffected

---

## Part 7: Testing Strategy

### Unit Tests

**Models:**
```python
def test_store_signup_config_create():
    store = BusinessUnit.objects.create(...)
    config = StoreSignupConfiguration.objects.create(
        business_unit=store,
        require_phone=True,
    )
    assert config.business_unit == store

def test_candidate_signup_answer_responses_json():
    answer = CandidateSignupAnswer(
        responses={
            "q1": "answer 1",
            "q2": ["opt1", "opt2"],
        }
    )
    assert answer.responses["q1"] == "answer 1"
```

### Integration Tests

```python
def test_store_chooser_flow():
    """Scan QR → select store → redirect."""
    ep = EntryPoint.objects.create(
        kind='organization',
        allows_store_selection=True,
        ...
    )
    response = client.get(f'/qr/{ep.id}/')
    assert response.status_code == 302
    assert 'store-chooser' in response.url

def test_custom_signup_with_questionnaire():
    """Fill custom form → create candidate + answer."""
    store = BusinessUnit.objects.create(...)
    template = QuestionnaireTemplate.objects.create(...)
    config = StoreSignupConfiguration.objects.create(
        business_unit=store,
        questionnaire_template=template,
    )
    
    response = client.post('/candidato/signup-customizado/', {
        'first_name': 'João',
        'email': 'joao@example.com',
        'q1_experience': '5 anos',
    })
    
    candidate = CandidateProfile.objects.get(email='joao@example.com')
    assert candidate.preferred_store == store
    
    answer = CandidateSignupAnswer.objects.get(candidate=candidate)
    assert answer.responses['q1_experience'] == '5 anos'
```

### E2E Tests (Selenium/Playwright)

```python
def test_full_signup_flow():
    """Real browser test: scan QR → store → form → success."""
    # Navigate to QR
    driver.get(f'{QR_BASE}/qr/{ep_id}/')
    
    # Wait for store chooser, click store
    store_btn = driver.find_element(By.ID, 'store-loja-a')
    store_btn.click()
    
    # Fill form
    driver.find_element(By.NAME, 'first_name').send_keys('João')
    driver.find_element(By.NAME, 'email').send_keys('joao@example.com')
    driver.find_element(By.NAME, 'phone').send_keys('+55 11 99999-9999')
    
    # Submit
    driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()
    
    # Verify success page
    assert 'Obrigado' in driver.page_source
    
    # Verify database
    candidate = CandidateProfile.objects.get(email='joao@example.com')
    assert candidate.preferred_store.id == store_id
```

---

## Part 8: Security & Compliance (LGPD)

### Consent Tracking

**Current:** Granular consent via CandidateConsent model

**Enhancement:** Link CandidateSignupAnswer to consent

```python
# In CustomSignupView.post():

# 1. Create/update CandidateConsent records
CandidateConsent.objects.create(
    identity=candidate.identity,
    organization=ep.organization,
    purpose=CandidateConsent.PURPOSE_CIRCULATION_STORE,
    legal_basis=CandidateConsent.BASIS_CONSENT,
    granted=True,
    policy_version='2.0',
    source='signup_flow',
)

# 2. Create Ledger entry (append-only)
Ledger.objects.create(
    type='CANDIDATE_SIGNUP_CUSTOMIZED',
    identity=candidate.identity,
    organization=ep.organization,
    details={
        'store_id': store_id,
        'ep_id': str(ep.id),
        'questionnaire_version': questionnaire.version,
    }
)
```

### Audit Requirements

**Track:**
- Which questionnaire version was shown
- Which questions were answered
- Timestamp of signup
- IP address (via middleware)
- Store selected

**Compliance:**
- All stored in CandidateSignupAnswer (immutable)
- Ledger entry for each signup
- Data exportable via GDPR interface

---

## Part 9: Performance Considerations

### Queries

**StoreChooserView:**
```python
# N+1: fetch allowed_stores
queryset = ep.allowed_stores.all()  # ✅ Efficient: M2M load

# Or, if empty (means all stores):
if not queryset.exists():
    queryset = BusinessUnit.objects.filter(
        organization=ep.organization
    )
```

**CustomSignupView:**
```python
# Load config + questionnaire in one query
config = StoreSignupConfiguration.objects.select_related(
    'questionnaire_template'
).get(business_unit_id=store_id)

# Load questions
questions = config.questionnaire_template.questions.filter(
    active=True
).order_by('order')
```

### Caching

**Recommended:**
```python
# Cache store list (TTL 1 hour)
from django.views.decorators.cache import cache_page

@cache_page(3600)
def store_chooser(request, entry_point_id):
    ...

# Cache questionnaire questions
QUESTIONNAIRE_CACHE_KEY = f'questionnaire_{template.id}_v{template.version}'
questions = cache.get_or_set(
    QUESTIONNAIRE_CACHE_KEY,
    lambda: list(template.questions.filter(active=True)),
    timeout=3600
)
```

---

## Conclusion & Next Steps

### Executive Checklist

- [ ] Approve data model
- [ ] Create migration scripts
- [ ] Schedule dev work
- [ ] Set up feature flag
- [ ] Create console mockups
- [ ] Get stakeholder sign-off

### Development Checklist (Phase 1-2)

- [ ] Create models + migrations
- [ ] Implement views
- [ ] Write unit + integration tests
- [ ] Build console admin UI
- [ ] Create E2E test scenarios

### Deployment Checklist (Phase 5)

- [ ] Run migrations on staging
- [ ] Canary: 10% of orgs
- [ ] Monitor: signup completion rate, error rate
- [ ] Full rollout: 100%
- [ ] Notify customers: new QR feature available
