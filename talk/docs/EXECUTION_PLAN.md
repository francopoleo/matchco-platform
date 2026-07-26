# Talk Platform - Development Execution Plan

**Last Updated:** 2026-07-26
**Status:** Phase 1 Complete (UI/OBAC) | Phase 2 97% Complete (Enterprise Users + Production Hardening)
**Git Tag:** `v1.0.0-ui-obac` ← Current Release
**Phase 2 Progress:** Weeks 1-4 Complete | Week 5 In Progress (Hardening - Core complete, Monitoring pending)

---

## Phase 1: ✅ COMPLETE - UI Standardization & OBAC (v1.0.0)

### Scope
Standardize UI/UX across console and fix organization-based access control vulnerabilities.

### Completed Tasks

#### UI Standardization (✅ 100%)
- [x] Responsive header pattern applied (text-2xl → sm:text-3xl → lg:text-4xl)
- [x] SVG icon fixes (replaced corrupted icons with Flowbite)
- [x] Form width standardization (removed max-width, use w-full)
- [x] Padding hierarchy fixes (no px- duplication in detail pages)
- [x] Back link standardization (consistent arrow + text pattern)
- [x] Template syntax errors fixed (learning_metrics.html)

**Files Modified:** 40+
**Pages Standardized:** 20+

#### Organization-Based Access Control (OBAC) - ✅ 48% Complete
**Fixed (14 pages):**
- ✅ user_list.html - Filters users by selected organization (2026-07-26)
- ✅ dashboard.html - Filters user/rule counts (2026-07-26)
- ✅ course_list.html
- ✅ course_form.html
- ✅ document_form.html
- ✅ publication_form.html
- ✅ trail_form.html
- ✅ content_metrics.html
- ✅ engagement_funnel.html
- ✅ audience_simulation.html
- ✅ management_report.html
- ✅ membership_assignment.html
- ✅ organization_settings.html
- ✅ registration_request_list.html

**Remaining (15 pages):**
- ❌ document_list.html
- ❌ publication_list.html
- ❌ trail_list.html
- ❌ learning_metrics.html (partially done)
- ❌ demo_visit_list.html
- ❌ content_question_list.html
- ❌ trail_progress.html
- ❌ trail_assignment_form.html
- ❌ management_assignment_form.html
- ❌ trail_step_stats.html
- ❌ trail_abandonment_summary.html
- ❌ document_version_compare.html
- ❌ user_form.html
- ❌ audience_impact.html (include file)
- ❌ base.html (base template)

### Backend Changes
- Modified `UserConsoleListView.get_queryset()` to filter by active organization
- Modified `ConsoleDashboardView.get_context_data()` to scope statistics
- Pattern: Uses `active_organization_queryset()` helper function

### Impact on Current System
✅ **Non-breaking:** All changes are additive or internal refactoring
- Existing functionality preserved
- No data migrations required
- No API changes
- No user-facing breaking changes

### Deployment Notes
- Single commit: `feat: UI standardization & organization-based access control`
- Git Tag: `v1.0.0-ui-obac`
- Database: No migrations needed
- Settings: No configuration changes needed

### Testing Recommendations
1. Verify user_list.html shows only users from selected organization
2. Verify dashboard KPIs update when switching organizations
3. Verify all pages have consistent header styling
4. Visual inspection: icons render correctly (no broken SVGs)

---

## Phase 2: ✅ 95% COMPLETE - Enterprise User System (v2.0.0)

### Status: Weeks 1-4 ✅ | Week 5 🟡 In Progress (Core ✅ | Monitoring 🔜)
- **Week 1 (Data Model):** ✅ COMPLETE - Membership, MembershipAudit, company nullable, is_public
- **Week 2 (Auth & Session):** ✅ COMPLETE - org selector, middleware, content filtering, backfill
- **Week 3 (Admin Console):** ✅ COMPLETE - MembershipAdmin, AuditAdmin, all models registered
- **Week 4 (Public Signup):** ✅ COMPLETE - Public orgs, signup flow, email confirmation, templates
- **Week 5 (Hardening):** 🟡 IN PROGRESS
  - ✅ Rate limiting (5/h signup, 10/h login)
  - ✅ CAPTCHA v3 integration
  - ✅ Email verification enforcement
  - 🔜 Sentry monitoring
  - 🔜 Signup funnel dashboard

### Overview
Implement production-grade multi-company user management system inspired by Slack, Notion, Salesforce, and Asana.

### Goals
- One global login → multiple memberships/organizations
- Clear separation: Django permissions vs business roles vs data scope
- Organization selector in navbar (like Slack workspace switcher)
- Complete audit trail for compliance (GDPR, SOC2)
- Enterprise-grade permission system (RBAC)
- Non-breaking 5-week rollout

### Architecture Documents Created
1. **User Management Analysis** (user_management_analysis.md)
   - 8 identified problems
   - Current state diagnosis
   - Recommendations for robustness

2. **Enterprise User Architecture** (enterprise_user_architecture.md)
   - Complete design (200+ lines)
   - How Slack/Notion/Salesforce do it
   - Data model changes
   - Authentication flow
   - Permission separation

3. **Enterprise Architecture Quick Ref** (enterprise_architecture_quick_ref.md)
   - Visual diagrams
   - Quick reference tables
   - Three user scenarios
   - Implementation order

4. **Definitive Enterprise System** (definitive_enterprise_system.md)
   - Production-grade implementation
   - Complete models with migrations
   - RBAC with role permissions
   - Admin interface code
   - 5-week rollout plan
   - Audit trail design
   - Security checklist

### Data Model Changes (Phase 2 - Week 1)

#### New/Modified Tables
```
User (existing - no breaking changes)
├─ Remove: is_staff, is_superuser (use only for Django admin)
├─ Add: locale (timezone/language)
└─ Add: created_at (tracking)

Membership (existing - add fields)
├─ Add: role ('owner', 'admin', 'member', 'guest', 'viewer')
├─ Add: created_by (who added this membership)
├─ Add: updated_by (who last modified)
├─ Add: updated_at (timestamp)
├─ Add: UNIQUE constraint (user, is_primary=True)
└─ Add: Constraint (must have at least 1 active membership)

MembershipAudit (NEW table)
├─ membership (FK, nullable)
├─ user (who made the change)
├─ action ('created', 'role_changed', 'deactivated', etc.)
├─ old_values (JSON)
├─ new_values (JSON)
├─ reason (why)
└─ created_at, ip_address, user_agent

UserSession (NEW table - optional, for session tracking)
├─ user (FK)
├─ session_key
├─ active_organization (current workspace)
├─ last_activity_at
└─ ip_address, user_agent
```

#### Migrations Sequence
1. Week 1, Migration 1: Add fields (role, created_by, updated_by, updated_at)
2. Week 1, Migration 2: Create MembershipAudit table
3. Week 1, Migration 3: Add UNIQUE constraint (one is_primary)
4. Week 1, Migration 4: Data backfill (validate consistency)

### Implementation Timeline

#### Week 1: Data Model & Constraints (Non-Breaking)
- [ ] Add Membership.role field (default='member')
- [ ] Add Membership.created_by/updated_by (ForeignKey, nullable)
- [ ] Add Membership.updated_at (auto_now)
- [ ] Create MembershipAudit model
- [ ] Add UNIQUE constraint: (user, is_primary=True)
- [ ] Create migrations
- [ ] Backfill: Set created_by for all existing memberships
- [ ] Backfill: Ensure each user has exactly 1 is_primary=True
- [ ] Verification: No orphaned users

**Impact:** Zero breaking changes (additive only)

#### Week 2: Authentication & Session Management
- [ ] Create ActiveOrganizationMiddleware
- [ ] Create organization_select view
- [ ] Create switch_organization view
- [ ] Create organization_selector.html template
- [ ] Update login flow (post-auth redirect to org selector)
- [ ] Add UserSession tracking (optional)
- [ ] Update navbar with dropdown switcher

**Impact:** New flow after login, existing pages unaffected

#### Week 3: Admin & Console Console
- [ ] Create custom UserAdmin with MembershipInline
- [ ] Create MembershipAuditInline (view-only)
- [ ] Create @membership_required permission decorator
- [ ] Create members_list view (per organization)
- [ ] Create member_edit view (change role)
- [ ] Create member_add view (invite users)
- [ ] Create audit_trail view (show MembershipAudit)
- [ ] Console: members management page

**Impact:** New pages, existing pages still work

#### Week 4: Signup & Onboarding
- [ ] Create signup_create_user view
- [ ] Create signup_join_organization view
- [ ] Create first_login_setup view
- [ ] Create InvitationCode model (if not exists)
- [ ] Create invitation_code generation UI
- [ ] Update signup flow templates

**Impact:** New signup path, existing auth still works

#### Week 5: Production Hardening
- [x] Security: Rate limiting (django-ratelimit) - 5/hour signup, 10/hour login
- [x] Security: CAPTCHA v3 integration (django-recaptcha)
- [x] Security: Email verification enforcement
- [x] Monitoring: Rate limit error handling with user-friendly messages
- [ ] Monitoring: Sentry integration for error tracking
- [ ] Monitoring: Signup funnel dashboard (view → signup → confirmation)
- [ ] Performance: Database indexes on active user/organization queries

**Status:** ✅ Core security hardening complete (3/7)  
**Impact:** Production-ready signup flow with bot protection and rate limiting

### Week-by-Week Deliverables

**Week 1 Deliverable:** v2.0.0-alpha.1
- All database migrations applied
- New tables exist with data
- No breaking changes
- Existing code still works

**Week 2 Deliverable:** v2.0.0-alpha.2
- Organization selector working
- Can switch between organizations
- Session tracks active org
- Navbar shows dropdown

**Week 3 Deliverable:** v2.0.0-beta.1
- Admin UI functional
- Members can be managed
- Audit trail visible
- Permission decorator works

**Week 4 Deliverable:** v2.0.0-beta.2
- New signup flow functional
- Invitation codes working
- Onboarding complete

**Week 5 Deliverable:** v2.0.0 (Final)
- Production-ready
- Security hardened
- Performance optimized
- Compliance verified

### Permission Architecture (Phase 2)

#### Layer 1: System Admin (Django)
```
User.is_staff = True
├─ Can access Django admin
├─ Can view all organizations
└─ Can manage infrastructure

User.is_superuser = True
├─ Full system access
├─ No data scope restrictions
└─ Global visibility (all orgs)
```

#### Layer 2: Business Role (Per Membership)
```
membership.role = 'owner' | 'admin' | 'member' | 'guest'
├─ Determines: can view members? can invite? can delete?
├─ Can change roles?
├─ Can view reports?
└─ User can have different role in different organizations
```

#### Layer 3: Data Access (Audience Scope)
```
membership.company
membership.business_unit
membership.channels
membership.functions
├─ Which data user sees
├─ Which users they can search
├─ Which reports show their data
└─ Which content they can access
```

### RBAC Permission Matrix (Phase 2)

```
                    owner  admin  member  guest  viewer
can_view_members      ✓      ✓      ✗      ✗      ✗
can_invite_members    ✓      ✓      ✗      ✗      ✗
can_remove_members    ✓      ✓      ✗      ✗      ✗
can_change_roles      ✓      ✗      ✗      ✗      ✗
can_view_settings     ✓      ✓      ✗      ✗      ✗
can_edit_settings     ✓      ✓      ✗      ✗      ✗
can_delete_org        ✓      ✗      ✗      ✗      ✗
can_manage_billing    ✓      ✗      ✗      ✗      ✗
can_view_audit_logs   ✓      ✓      ✗      ✗      ✗
can_create_content    ✓      ✓      ✓      ✗      ✗
can_view_all_content  ✓      ✓      ✗      ✗      ✗
```

### Impact Analysis (Phase 2)

#### Breaking Changes
⚠️ **None!** This is the design goal.

#### Behavioral Changes
- After login: User sees organization selector (new step)
- Navbar: Shows organization dropdown instead of static badge
- Console: Members page redesigned
- Admin: Users can be managed with memberships inline

#### Performance Impact
- Small query overhead: validate membership per request (cached)
- New table: MembershipAudit (log-only, no query overhead)
- Session: one extra session key (active_organization_id)

**Estimate:** < 5% performance impact

#### Data Migration Complexity
- Simple: All additive (no columns removed)
- Safe: Full audit trail created
- Reversible: Can rollback migrations if needed

### Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Org selector causes confusion | Navbar dropdown clearly labeled; auto-select if 1 org |
| Permission denials | Comprehensive permission decorator + audit logging |
| Session hijacking | Validate membership on every request |
| Data leakage | active_organization_id verified per request |
| Audit trail corruption | Database constraints + immutable logs |
| Signup spam | Rate limiting + invitation codes |

### Rollback Plan
Each week's changes can be independently rolled back:
- Week 1: Revert migrations (data in audit trail preserved)
- Week 2: Remove middleware, redirect to default org
- Week 3: Hide admin UI, keep console functional
- Week 4: Disable new signup, keep old flow
- Week 5: No rollback needed (safe changes only)

### Success Criteria

#### Week 1
- ✓ All migrations apply without errors
- ✓ No data loss
- ✓ Existing code still works
- ✓ Backfill scripts complete

#### Week 2
- ✓ Org selector appears after login
- ✓ Can switch between organizations
- ✓ Session tracks organization
- ✓ Navbar shows current organization

#### Week 3
- ✓ Members can be listed
- ✓ Members can be added/removed
- ✓ Role can be changed
- ✓ Audit trail shows changes

#### Week 4
- ✓ New signup creates user
- ✓ Join organization works
- ✓ Invitation codes validate
- ✓ First-login setup completes

#### Week 5
- ✓ All tests pass
- ✓ Performance < 5% degradation
- ✓ Security checklist complete
- ✓ Documentation updated

### Testing Plan

#### Unit Tests
- Permission checks (@membership_required)
- Role validation
- Constraint enforcement (one is_primary)

#### Integration Tests
- Login → org selection → dashboard
- Org switch → session update → data filtering
- Add member → audit log created
- Remove member → session invalidated

#### Load Tests
- 1000 users across 10 orgs
- Rapid org switching (stress test)
- Large audit trail queries (performance)

#### Security Tests
- User A cannot see User B's data
- Cannot downgrade own role
- Cannot escalate privileges
- Session validation on every request

### Deployment Checklist

Before each week's release:
- [ ] All migrations tested locally
- [ ] Code reviewed
- [ ] Tests passing (unit + integration)
- [ ] No console warnings/errors
- [ ] Documentation updated
- [ ] Git tagged (v2.0.0-alpha.X, v2.0.0-beta.X)
- [ ] Changelog updated
- [ ] Team notified of changes

### Post-Implementation

#### Phase 3 (Months 2-3) - Optional Enhancements
- [ ] MFA for organization owners
- [ ] Invite templates (email with code)
- [ ] Organization transfer ownership
- [ ] Bulk user import from CSV
- [ ] SSO integration (SAML/OAuth)
- [ ] Advanced audit trail search
- [ ] Compliance reports (SOC2, GDPR)

#### Monitoring
- Organization selection time (SLA < 100ms)
- Audit trail latency (< 50ms)
- Permission check failures (alert if > 1%)
- Orphaned users (automatic cleanup)

---

## Summary: v1.0 → v2.0 Transition

### What Stays the Same
- User login flow (email + password)
- All existing pages and features
- Database (no table deletions)
- API endpoints (no breaking changes)

### What Changes
- Post-login: Organization selection (new)
- Navbar: Organization dropdown (instead of badge)
- Admin: UserAdmin with memberships (new)
- Console: Members page redesigned

### What's New
- MembershipAudit table (complete trail)
- @membership_required decorator
- switch_organization view
- organization_select view
- Audit trail viewer

### Timeline
- **Now (v1.0.0):** UI standardization + OBAC (14/29 pages)
- **Week 1-5:** Enterprise User System (v2.0.0)
- **Month 2-3:** Optional enhancements (v2.1, v2.2)

### Key Documents
- Design: `enterprise_user_architecture.md`
- Reference: `enterprise_architecture_quick_ref.md`
- Implementation: `definitive_enterprise_system.md`
- Analysis: `user_management_analysis.md`

---

## Phase 2 Summary: Enterprise Users (Implemented 2026-07-26)

### Week 1: Data Model ✅
- Added Membership.role, is_primary, created_by, updated_by
- Created MembershipAudit table (complete audit trail)
- Made Membership.company nullable (for public users)
- Added Organization.is_public + description
- **3 Migrations Applied:**
  - configuration/migrations/0009: is_public field
  - configuration/migrations/0010: description field
  - configuration/migrations/0011: company nullable

### Week 2: Auth & Session ✅
- OrganizationSelectorView (initial selection)
- SwitchOrganizationView (navbar switcher)
- ActiveOrganizationMiddleware (context management)
- Fixed active_company_id session key sync
- Backfilled 48 content objects (8 trails, 20 courses, 20 publications)
- Updated admin columns: ContentTrailAdmin, CourseAdmin, PublicationAdmin

### Week 3: Admin Console ✅
- MembershipAdmin configured (list_display, filters, search)
- MembershipAuditAdmin configured (audit viewer)
- All models registered and searchable
- No additional work needed (already implemented)

### Week 4: Public Signup ✅ NEW
- PublicSignupView, PublicConfirmEmailView, PublicSignupConfirmationView
- 4 public organizations created: candidates, doctors, partners, students
- Email confirmation flow with token generation
- 3 beautiful templates (Tailwind CSS)
- Management command: create_public_orgs
- **End-to-end test passed:** User signup → confirm email → login → home
- User model import fixed (using user_management.User)
- All views imported and tested

### Files Created/Modified (Phase 2 Week 4)
**New Files:**
- accounts/views.py: Added PublicSignupView + 2 support views
- accounts/urls.py: Added 3 public signup URLs
- accounts/templates/public/signup.html
- accounts/templates/public/signup_confirmation.html
- accounts/templates/public/confirm_email.html
- configuration/management/commands/create_public_orgs.py
- test_public_signup_flow.py (E2E test script)

**Modified Files:**
- configuration/models.py: Added is_public, description, company nullable
- accounts/views.py: Import user_management.User (custom User model)

### Migrations Applied
- 0009_alter_organization_options_organization_is_public.py
- 0010_organization_description.py
- 0011_alter_membership_company.py

### Ready for Week 5: Production Hardening
- [ ] Rate limiting on public signup (5 attempts/hour)
- [ ] CAPTCHA integration
- [ ] Email verification required (enforce)
- [ ] Password complexity rules
- [ ] Monitoring dashboards

---

## Current Version: v1.0.0-ui-obac (Phase 1 Complete)

**Status:** Production Ready
**OBAC Completion:** 48% (14/29 pages)
**UI Standardization:** 100%
**Breaking Changes:** None

**Next Release:** v2.0.0-enterprise-users (95% Complete - Week 5 Hardening Only)
**Public User System:** Ready for production (candidates, doctors, partners, students)

---

## External Access Use Cases: Recruitment & Professional Onboarding

### 1. Recruitment: Job Candidate Hiring Funnel

**Scenario:** Company wants to hire developers. Places QR code on careers page.

**Flow:**
```
1. Candidate scans QR code
2. Lands on /signup/public/candidates/
3. Creates account with email + password
4. Receives confirmation email
5. Clicks confirmation link → auto-login
6. Sees personalized hiring trail

Trail Content:
├─ "Vaga: Desenvolvedor Sênior" (job description)
├─ "Enviar Documentos" (upload CV, certifications)
├─ "Teste Técnico" (coding assessment)
├─ "Conhecer a Empresa" (company info course)
├─ "Onboarding: Primeiros Passos" (welcome course)
└─ "Assinatura de Contrato" (DocuSign integration - future)

Post-Hire: Admin converts membership
├─ Remove: role='viewer', organization='Public - Candidates'
└─ Add: role='member', organization='Hospital Generative'
```

**Timeline:**
- Day 1: Apply → Receive documents trail
- Day 3-7: Complete assessment → See results
- Day 7: If pass → Offer sent
- Day 14: Sign contract
- Day 21: Become internal employee

---

### 2. Medical: Doctor Credentialing & Compliance

**Scenario:** New medication approved. Doctors need certification before prescribing.

**Flow:**
```
1. Pharmaceutical company sends QR code to doctors
2. Doctors scan → /signup/public/doctors/
3. Register with medical license info
4. Confirmation email
5. Access required training trail

Trail Content:
├─ "Novo Remédio X: Guia Clínico" (medical manual)
├─ "Modo de Ação & Indicações" (course module)
├─ "Efeitos Colaterais & Contraindicações" (assessment)
├─ "Quiz de Conformidade" (compliance test)
├─ "Assinatura de Conformidade" (legal agreement)
└─ "Certificação Concedida" (badge award)

Post-Certification:
├─ Auto-generate certificate
├─ Send to regulatory body
├─ Doctor can prescribe
└─ Audit trail complete
```

**Regulatory Compliance:**
- Complete audit trail (MembershipAudit)
- Doctor signatures (legal compliance)
- Certificate generation
- Expiration tracking (future)

---

### 3. Integration Partners: API Access & Onboarding

**Scenario:** Tech partner needs API credentials and documentation.

**Flow:**
```
1. Partner receives QR code (/signup/public/partners/)
2. Signs up → Receives API documentation trail
3. Completes security training
4. Gets API key via admin
5. Access to dedicated documentation

Trail Content:
├─ "API Authentication" (OAuth2, JWT)
├─ "Rate Limiting & Quotas" (usage guide)
├─ "Webhook Setup" (integration guide)
├─ "Test Integration" (sandbox account)
├─ "Production Handoff" (launch checklist)
└─ "Support & SLAs" (support channels)

Post-Signup Admin Flow:
├─ Admin approves partner
├─ Generate API credentials
├─ Set rate limits
└─ Enable production access
```

---

### 4. Students: Public Course Access

**Scenario:** Company offers free certification courses to public.

**Flow:**
```
1. User sees /signup/public/students/
2. Enroll in free course
3. Confirmation email
4. Access course content
5. Complete assessments
6. Receive certificate

Trail Content:
├─ "Introdução à Segurança" (course module)
├─ "Boas Práticas" (course module)
├─ "Avaliação Final" (quiz)
└─ "Certificado" (downloadable)

Post-Course:
├─ Certificate email sent
├─ LinkedIn integration (optional)
└─ Alumni access (view-only membership)
```

---

## Implementation: Virtual Public Organizations

**Database Design:**
```
User (Global Login)
├─ email (unique)
├─ password (hashed)
├─ is_active (False until email confirmed)
└─ created_at

Membership (Multi-tenant Context)
├─ user → User
├─ organization → Organization
│  ├─ "Public - Candidates" (is_public=True)
│  ├─ "Public - Doctors" (is_public=True)
│  ├─ "Public - Partners" (is_public=True)
│  ├─ "Public - Students" (is_public=True)
│  └─ "Hospital Generative" (is_public=False, internal)
├─ company → Company (NULL for public users)
├─ role → "viewer" for public, "member"/"admin" for internal
├─ active (False until email confirmed, then True)
└─ created_by (NULL for self-signup)

MembershipAudit (Compliance Trail)
├─ membership → Membership
├─ user → User (who made the change)
├─ action → "created" | "updated" | "deleted"
├─ old_values → JSON (before change)
├─ new_values → JSON (after change)
└─ created_at → timestamp
```

**Key Features:**
- ✅ One User, multiple Memberships
- ✅ Each trail/course filters by active organization
- ✅ Public users can ONLY see public-org content
- ✅ Internal users see internal-org content
- ✅ Complete audit trail for compliance
- ✅ No data sharing between orgs/companies

---

## Use Case Matrix

| Feature | Candidates | Doctors | Partners | Students |
|---------|-----------|---------|----------|----------|
| Email Confirmation | ✅ Required | ✅ Required | ✅ Required | ✅ Required |
| Document Upload | ✅ Yes (CV) | ✅ Yes (License) | ✅ No | ✅ No |
| Assessments | ✅ Technical test | ✅ Compliance quiz | ✅ Integration test | ✅ Course quiz |
| Certificate | ✅ Offer letter | ✅ Medical cert | ✅ API key | ✅ Course cert |
| Audit Trail | ✅ Yes | ✅ Yes (Regulatory) | ✅ Yes | ✅ Yes |
| Time Limit | ❌ No | ⏳ 30 days | ❌ No | ❌ No |
| Post-Action | Convert to member | Prescribe medicine | Enable API | Alumni view |

---

## Deployment Strategy

**Phase A: MVP (Week 4 - Done)**
- [x] Public signup form
- [x] Email confirmation
- [x] 4 virtual public organizations
- [x] Basic content filtering
- [x] Audit trail

**Phase B: Production Ready (Week 5)**
- [ ] Rate limiting (5 signup/hour per IP)
- [ ] CAPTCHA on forms
- [ ] Email verification required
- [ ] Monitoring + alerting
- [ ] Backup & disaster recovery

**Phase C: Advanced Features (Post-Week 5)**
- [ ] Document upload (Candidates)
- [ ] Assessment scoring (Doctors)
- [ ] API key generation (Partners)
- [ ] Certificate generation (Students)
- [ ] Integrations (DocuSign, Twilio, etc.)

---

## Success Metrics

**Week 4 (MVP):**
- ✅ Signup form works
- ✅ Email confirmation works
- ✅ Content filtering works
- ✅ Audit trail logs correctly

**Week 5 (Production):**
- [ ] Zero security vulnerabilities
- [ ] <100ms page load time
- [ ] <1% email bounce rate
- [ ] <5% signup abandonment

**Post-Production:**
- [ ] 100+ candidates applying
- [ ] 50+ doctors certified
- [ ] 10+ API partners integrated
- [ ] 500+ students enrolled

---

## Phase 3: Compliance Training & User Groups (Future - Scalable)

### Part 1: Compliance Training Flows (Viável - Próxima)

**Three Compliance Pathways - Same System, Different Roles:**

#### 1A. Internal Employee Compliance

**Scenario:** Employee hired. Must complete LGPD + Security + Operations training.

```
Timeline:
Day 1: Hire → Auto-assign "LGPD & Data Protection" trail
       ├─ Manual LGPD (read course)
       ├─ Quiz (compliance test)
       ├─ Assinar termo (DocuSign integration - future)
       └─ Badge awarded

Day 2: Auto-assign "Security Best Practices" trail
       ├─ Password management
       ├─ Phishing awareness
       ├─ Incident response
       ├─ Quiz
       └─ Badge awarded

Day 3: Auto-assign "Operations Training" trail (role-specific)
       ├─ If role=admin → Admin responsibilities
       ├─ If role=member → Member access guide
       ├─ If role=viewer → View-only guide
       └─ Department-specific content

Due Date: All completed within 30 days
Compliance: MembershipAudit logs every step
Alert: If incomplete → Manager notification
```

**Database:**
- Membership.compliance_status (pending/in_progress/completed)
- Membership.compliance_due_date
- TrailAssignment.is_mandatory (boolean)
- MembershipAudit logs: "compliance_trail_assigned", "compliance_quiz_passed"

---

#### 1B. External Partner Compliance

**Scenario:** Partner needs to access customer data. Must complete security + NDA.

```
Timeline:
Day 1: Partner signup (/signup/public/partners/)
       ├─ Auto-assign "Data Protection Agreement" (required reading)
       ├─ Auto-assign "Security Certification" (video + quiz)
       └─ Auto-assign "API Security" (technical guide)

Day 2: Admin reviews completion
       ├─ If passed → Activate API credentials
       ├─ If failed → Deny access until retake
       └─ Send notification

Ongoing: Quarterly recertification required
         ├─ Annual security update
         ├─ Data handling policy changes
         └─ Compliance status dashboard
```

**Database:**
- Membership.compliance_status (pending/certified/expired)
- Membership.compliance_expiry_date
- Certificate generation (PDF)

---

#### 1C. Stakeholder/Manager Compliance

**Scenario:** Manager/Director must understand compliance responsibilities.

```
Timeline:
Day 1: Manager added
       ├─ "Leadership Compliance Responsibilities" trail
       ├─ "Audit & Monitoring" course
       ├─ "Risk Assessment" training
       ├─ "Incident Response as Manager" guide
       └─ Quiz (manager-level)

Monthly:
       ├─ Compliance dashboard (team status)
       ├─ Risk scorecard (by department)
       ├─ Audit report (team activities)
       └─ Certification renewal status
```

**Database:**
- Membership.is_manager (boolean)
- Membership.supervised_users (M2M)
- Dashboard widget: "Team Compliance Status"

---

### Part 2: User Groups (Viável - Escalável)

**Concept:** Group users with relationships (not hierarchy yet).

#### Simple User Groups Structure

```
UserGroup (New Model)
├─ name (string): "School Parents", "Alumni 2024", "IT Department"
├─ slug (slug): "school-parents", "alumni-2024", "it-department"
├─ organization → Organization (FK)
├─ group_type (choices): "parents" | "alumni" | "department" | "custom"
├─ created_at
├─ updated_at

GroupMembership (New Model - Join Table)
├─ user → User (FK)
├─ group → UserGroup (FK)
├─ role (choices): "admin" | "member" | "viewer"
├─ joined_at
└─ status: "active" | "pending" | "inactive"

GroupAccess (New Model - Permissions)
├─ group → UserGroup (FK)
├─ content_type (Trail / Course / Publication)
├─ object_id
├─ access_level (choices): "view" | "view_progress" | "download"
└─ created_at
```

---

#### 2A. Parents + Students Group

**Use Case:** School wants parents to track student progress.

```
Structure:
Organization (School) 
├─ User: "João Silva" (student, role=member)
├─ User: "Maria Silva" (parent, role=viewer)
└─ UserGroup: "Pais dos Alunos 2024"
    ├─ GroupMembership: Maria → role=member
    ├─ GroupAccess: Can VIEW student's trail progress
    └─ GroupAccess: Can DOWNLOAD student's certificates

Flow:
1. Parent signs up with student email as relation
2. Auto-added to "Pais dos Alunos" group
3. Can only see linked student's progress
4. Cannot see other students
5. Gets notifications: "João completed trail X"
```

**Relationships:**
```
User (Maria - Parent)
├─ UserGroup: "Pais dos Alunos"
└─ GroupMembership.linked_student → User (João)

User (João - Student)
├─ Memberships: "Hospital Generative"
├─ Trails: "Curso de Segurança"
└─ Progress: (Maria can see via group)
```

---

#### 2B. Alumni Group

**Use Case:** Graduates maintain access to resources, limited permissions.

```
Structure:
UserGroup: "Alumni 2024"
├─ User: "Carlos Santos" (graduated, alumni=true)
├─ Role: "viewer" (read-only)
└─ Access: View-only to past courses, no download

Timeline:
1. Student completes program
2. Auto-converted: role=member → alumni=true
3. Auto-added to "Alumni 2024" group
4. Role: "viewer" (limited permissions)
5. Access: View past courses, see peer directory
6. Cannot: Create content, enroll in new courses

Features:
├─ Alumni directory (find classmates)
├─ Alumni events trail (networking)
├─ Career advancement tracking
└─ Reconnection & mentorship opportunities
```

---

#### 2C. Department Groups (Future Scaling)

**Use Case:** Organize by department without full hierarchy.

```
Structure:
Organization (Company)
├─ UserGroup: "IT Department"
│  ├─ GroupMembership: Admin
│  ├─ GroupMembership: Lead
│  └─ GroupMembership: Members (5)
│
├─ UserGroup: "Sales Department"
│  ├─ GroupMembership: Manager
│  └─ GroupMembership: Members (10)
│
└─ UserGroup: "HR Department"
   ├─ GroupMembership: Manager
   └─ GroupMembership: Member

Features:
├─ Department-specific trails
├─ Group messaging (future)
├─ Department dashboards
└─ Skill-based grouping (inside departments)
```

---

### Implementation Roadmap (3 Phases)

#### Phase 3.1: Compliance Training (Weeks 1-2) - START HERE
**Scope:** Internal + External + Stakeholder compliance flows
**Effort:** 2 weeks
**Complexity:** Low (reuses existing Membership + Trail system)
**Non-breaking:** Yes - all additive, no data migrations needed

##### Week 1: Database + Admin Interface

**Models to Add/Modify:**
```python
# configuration/models.py - Add fields to Membership

class Membership(models.Model):
    # ... existing fields ...
    
    # NEW FIELDS:
    compliance_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('overdue', 'Overdue'),
            ('failed', 'Failed'),
        ],
        default='pending',
        help_text='Compliance training status for this membership'
    )
    
    compliance_due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When compliance training must be completed by'
    )
    
    compliance_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When user completed all compliance trainings'
    )
```

**Migration:**
```bash
python manage.py makemigrations configuration
python manage.py migrate
```

**Admin Updates:**
```python
# configuration/admin.py

class MembershipAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'organization', 'role', 'active',
        'compliance_status', 'compliance_due_date',  # NEW
        'created_at'
    )
    list_filter = (
        'organization', 'role', 'active',
        'compliance_status', 'compliance_due_date',  # NEW
        'created_at'
    )
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'compliance_completed_at')
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'organization', 'company', 'role', 'active')
        }),
        ('Compliance', {  # NEW
            'fields': (
                'compliance_status',
                'compliance_due_date',
                'compliance_completed_at'
            ),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
```

**TrailAssignment Updates:**
```python
# learning/models.py - Add to TrailAssignment

class TrailAssignment(models.Model):
    # ... existing fields ...
    
    # NEW FIELD:
    is_mandatory = models.BooleanField(
        default=False,
        help_text='If True, user MUST complete before accessing resources'
    )
    
    compliance_type = models.CharField(  # NEW
        max_length=20,
        choices=[
            ('general', 'General'),
            ('internal', 'Internal Employee'),
            ('external', 'External Partner'),
            ('stakeholder', 'Stakeholder/Manager'),
        ],
        default='general'
    )
```

**Migrations:**
```bash
python manage.py makemigrations learning
python manage.py migrate
```

**Checklist Week 1:**
- [ ] Membership migration created & applied
- [ ] TrailAssignment migration created & applied
- [ ] MembershipAdmin shows compliance fields
- [ ] Admin can filter by compliance_status
- [ ] Admin can set compliance_due_date
- [ ] Tests pass: test_membership_compliance.py

---

##### Week 2: Auto-Assignment + Tracking + Notifications

**Management Command: Auto-Assign Compliance Trails**
```python
# configuration/management/commands/assign_compliance_trails.py

from django.core.management.base import BaseCommand
from configuration.models import Organization, Membership
from learning.models import Trail, TrailAssignment
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Auto-assign compliance trails based on membership type'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org',
            type=str,
            help='Organization slug (if empty, run for all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be assigned without making changes'
        )

    def handle(self, *args, **options):
        org_slug = options.get('org')
        dry_run = options.get('dry_run', False)

        # Get organizations
        if org_slug:
            orgs = Organization.objects.filter(slug=org_slug)
        else:
            orgs = Organization.objects.filter(is_public=False)

        for org in orgs:
            self.assign_compliance_trails(org, dry_run)

    def assign_compliance_trails(self, org, dry_run):
        """Assign compliance trails to all active memberships"""
        
        # Get compliance trail templates
        compliance_trails = {
            'internal': Trail.objects.get(slug='compliance-internal-employee'),
            'external': Trail.objects.get(slug='compliance-external-partner'),
            'stakeholder': Trail.objects.get(slug='compliance-stakeholder'),
        }

        memberships = org.memberships.filter(active=True)
        
        for membership in memberships:
            # Determine compliance type
            if membership.organization.is_public:
                compliance_type = 'external'
            elif membership.role in ['admin', 'manager']:
                compliance_type = 'stakeholder'
            else:
                compliance_type = 'internal'

            trail = compliance_trails.get(compliance_type)
            
            if not trail:
                self.stdout.write(f'⚠️ Trail not found for {compliance_type}')
                continue

            # Check if already assigned
            if TrailAssignment.objects.filter(
                user=membership.user,
                trail=trail
            ).exists():
                continue

            if not dry_run:
                # Assign trail
                assignment = TrailAssignment.objects.create(
                    user=membership.user,
                    trail=trail,
                    is_mandatory=True,
                    compliance_type=compliance_type,
                    due_at=datetime.now() + timedelta(days=30),
                )

                # Update membership
                membership.compliance_status = 'pending'
                membership.compliance_due_date = assignment.due_at
                membership.save()

                self.stdout.write(
                    f'✅ Assigned {trail.title} to {membership.user.email}'
                )
            else:
                self.stdout.write(
                    f'[DRY-RUN] Would assign {trail.title} to {membership.user.email}'
                )

# Run:
# python manage.py assign_compliance_trails --org=hospital-generative
# python manage.py assign_compliance_trails --dry-run
```

**Compliance Status View:**
```python
# console/views.py - Add ComplianceDashboardView

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from configuration.models import Membership

class ComplianceDashboardView(LoginRequiredMixin, TemplateView):
    """Show compliance training status for organization"""
    template_name = 'console/compliance_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        org_id = self.request.active_organization_id

        # Get all memberships in org
        memberships = Membership.objects.filter(
            organization_id=org_id,
            active=True
        ).select_related('user', 'organization')

        # Group by status
        compliance_stats = {
            'total': memberships.count(),
            'completed': memberships.filter(compliance_status='completed').count(),
            'pending': memberships.filter(compliance_status='pending').count(),
            'in_progress': memberships.filter(compliance_status='in_progress').count(),
            'overdue': memberships.filter(compliance_status='overdue').count(),
        }

        context['compliance_stats'] = compliance_stats
        context['memberships'] = memberships
        context['completion_rate'] = (
            compliance_stats['completed'] / compliance_stats['total'] * 100
            if compliance_stats['total'] > 0 else 0
        )

        return context
```

**Email Reminder System:**
```python
# learning/tasks.py - Celery task (or management command)

from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from configuration.models import Membership

def send_compliance_reminders():
    """Send email reminders for overdue compliance"""
    
    # Find memberships due in 7 days or overdue
    due_soon = timezone.now() + timedelta(days=7)
    
    memberships = Membership.objects.filter(
        compliance_status__in=['pending', 'in_progress'],
        compliance_due_date__lte=due_soon,
    )

    for membership in memberships:
        days_remaining = (
            membership.compliance_due_date - timezone.now()
        ).days

        if days_remaining < 0:
            status = "OVERDUE"
            membership.compliance_status = 'overdue'
        else:
            status = f"DUE IN {days_remaining} DAYS"

        subject = f'Compliance Training Required: {status}'
        message = f'''
        Olá {membership.user.first_name},

        Você tem treinamentos de conformidade pendentes:
        
        Status: {status}
        Prazo: {membership.compliance_due_date.strftime('%d/%m/%Y')}
        
        Acesse o sistema e complete os treinamentos necessários.
        
        Att,
        Talk Platform
        '''

        send_mail(
            subject,
            message,
            'compliance@talk.local',
            [membership.user.email],
            fail_silently=True,
        )

        membership.save()

# Run as scheduled task:
# python manage.py send_compliance_reminders (daily/weekly)
```

**Checklist Week 2:**
- [ ] Management command: assign_compliance_trails created & tested
- [ ] ComplianceDashboardView created & integrated
- [ ] Email reminder task created & scheduled
- [ ] Templates created: compliance_dashboard.html
- [ ] Admin can see compliance stats by org
- [ ] Users receive reminder emails
- [ ] Compliance status auto-updates (pending → in_progress → completed)
- [ ] Tests pass: test_compliance_assignment.py, test_compliance_email.py

---

**✅ PHASE 3.1 COMPLETE (2026-07-26)**

**Files Created/Modified (Phase 3.1):**
```
MODIFIED:
✅ configuration/models.py (Membership: +3 compliance fields)
✅ learning/models.py (TrailAssignment: +2 compliance fields)
✅ configuration/admin.py (MembershipAdmin: compliance fieldset + filters)
✅ console/views.py (ComplianceDashboardView with KPIs + member list)
✅ console/urls.py (compliance-dashboard route)

NEW:
✅ configuration/management/commands/assign_compliance_trails.py
   • Auto-assign by role (internal/stakeholder/external)
   • Dry-run mode for testing
   • Skip inactive & already-assigned
✅ configuration/management/commands/send_compliance_reminders.py
   • Email notifications for pending/overdue
   • Customizable day threshold
✅ console/templates/console/compliance_dashboard.html
   • Status cards (5 KPIs with color coding)
   • Member table (email, role, status, due date)
   • Action buttons
✅ configuration/tests/__init__.py
✅ configuration/tests/test_membership_compliance.py (19 tests)
✅ configuration/tests/test_compliance_auto_assignment.py (9 tests)

MIGRATIONS:
✅ configuration/migrations/0012_membership_compliance_*.py
✅ learning/migrations/0015_trailassignment_compliance_*.py
```

**Database Changes Summary:**
- Membership: +3 fields (compliance_status, compliance_due_date, compliance_completed_at)
- TrailAssignment: +2 fields (is_mandatory, compliance_type)
- No new tables (reuse existing patterns)

**Test Coverage:**
- 28 total compliance tests (all passing)
- Week 1: Membership & TrailAssignment field validation (19 tests)
- Week 2: Auto-assignment workflows (9 tests)

**Ready for Production:**
✅ All migrations applied
✅ Admin interface complete
✅ Management commands tested
✅ Dashboard view working
✅ Email notifications ready
✅ All tests passing

---

#### Phase 3.2: Simple User Groups (Weeks 3-4)
**Scope:** Parents + Alumni + Department groups
**Effort:** 2 weeks
**Complexity:** Medium (new models, but simple relationships)
**Non-breaking:** Yes - additive only

##### Week 3: Models + Admin Interface

**New Models:**
```python
# configuration/models.py - Add UserGroup + GroupMembership + GroupAccess

class UserGroup(models.Model):
    """Groups of users with relationships (parents, alumni, departments)"""
    
    GROUP_TYPE_CHOICES = [
        ('parents', 'Parents/Guardians'),
        ('alumni', 'Alumni/Graduates'),
        ('department', 'Department'),
        ('custom', 'Custom Group'),
    ]
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='user_groups'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    group_type = models.CharField(
        max_length=20,
        choices=GROUP_TYPE_CHOICES,
        default='custom'
    )
    
    # For parents group: link to school/organization
    # For alumni: graduation year
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Custom data: {graduation_year, school_name, etc}'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['organization', 'slug']]
        ordering = ['group_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_group_type_display()})"


class GroupMembership(models.Model):
    """User membership in groups"""
    
    ROLE_CHOICES = [
        ('admin', 'Group Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer Only'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending Approval'),
        ('inactive', 'Inactive'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_memberships'
    )
    group = models.ForeignKey(
        UserGroup,
        on_delete=models.CASCADE,
        related_name='members'
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # For parent-student relationships
    linked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='group_linked_by',
        help_text='For parent groups: link to student'
    )
    
    joined_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='group_memberships_created'
    )
    
    class Meta:
        unique_together = [['user', 'group']]
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.email} → {self.group.name}"


class GroupAccess(models.Model):
    """Content access permissions for groups"""
    
    ACCESS_LEVEL_CHOICES = [
        ('none', 'No Access'),
        ('view', 'View Only'),
        ('view_progress', 'View Progress'),
        ('download', 'Download'),
        ('manage', 'Full Access'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('trail', 'Trail'),
        ('course', 'Course'),
        ('publication', 'Publication'),
        ('organization', 'All Organization Content'),
    ]
    
    group = models.ForeignKey(
        UserGroup,
        on_delete=models.CASCADE,
        related_name='access_rules'
    )
    
    content_type = models.CharField(
        max_length=50,
        choices=CONTENT_TYPE_CHOICES,
        help_text='Type of content to grant access to'
    )
    
    # For specific content
    object_id = models.IntegerField(
        null=True,
        blank=True,
        help_text='ID of Trail/Course/Publication (null for all)'
    )
    
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='view'
    )
    
    # Who created this rule
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='group_access_rules_created'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['group', 'content_type', 'object_id']]
        ordering = ['-created_at']
    
    def __str__(self):
        content = self.get_content_type_display()
        access = self.get_access_level_display()
        return f"{self.group.name} → {content}: {access}"
```

**Admin Interface:**
```python
# configuration/admin.py

class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0
    raw_id_fields = ('user', 'linked_user')
    fields = ('user', 'linked_user', 'role', 'status', 'joined_at')
    readonly_fields = ('joined_at',)


class GroupAccessInline(admin.TabularInline):
    model = GroupAccess
    extra = 0
    fields = ('content_type', 'object_id', 'access_level')


class UserGroupAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'slug', 'group_type', 'organization', 
        'member_count', 'created_at'
    )
    list_filter = ('group_type', 'organization', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [GroupMembershipInline, GroupAccessInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('organization', 'name', 'slug', 'group_type')
        }),
        ('Description', {
            'fields': ('description', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    def member_count(self, obj):
        return obj.members.filter(status='active').count()
    member_count.short_description = 'Active Members'


class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'status', 'joined_at')
    list_filter = ('group', 'role', 'status', 'joined_at')
    search_fields = ('user__email', 'group__name')
    readonly_fields = ('joined_at',)


class GroupAccessAdmin(admin.ModelAdmin):
    list_display = ('group', 'content_type', 'object_id', 'access_level')
    list_filter = ('content_type', 'access_level', 'created_at')
    search_fields = ('group__name',)


# Register
admin.site.register(UserGroup, UserGroupAdmin)
admin.site.register(GroupMembership, GroupMembershipAdmin)
admin.site.register(GroupAccess, GroupAccessAdmin)
```

**Migrations:**
```bash
python manage.py makemigrations configuration
python manage.py migrate
```

**Checklist Week 3:**
- [ ] UserGroup model created & tested
- [ ] GroupMembership model created & tested
- [ ] GroupAccess model created & tested
- [ ] All 3 admin interfaces working
- [ ] Can create groups in admin
- [ ] Can add users to groups in admin
- [ ] Can set access rules in admin
- [ ] Tests pass: test_user_groups.py

---

##### Week 4: Group Flows + Content Filtering + Templates

**1. Parent-Student Flow:**
```python
# console/views.py - ParentStudentLinkingView

class ParentStudentLinkingView(LoginRequiredMixin, TemplateView):
    """Allow parent to link to student"""
    template_name = 'console/parent_student_link.html'
    
    def post(self, request, *args, **kwargs):
        student_email = request.POST.get('student_email')
        student = User.objects.get(email=student_email)
        
        # Get or create "Parents" group
        parents_group, _ = UserGroup.objects.get_or_create(
            organization_id=request.active_organization_id,
            slug='parents',
            defaults={
                'name': 'Parents/Guardians',
                'group_type': 'parents',
            }
        )
        
        # Add parent to group
        GroupMembership.objects.get_or_create(
            user=request.user,
            group=parents_group,
            defaults={'role': 'member', 'status': 'active'}
        )
        
        # Add parent with link to student
        GroupMembership.objects.get_or_create(
            user=request.user,
            group=parents_group,
            linked_user=student,
            defaults={'role': 'member', 'status': 'active'}
        )
        
        # Grant access to student's content
        for trail in student.trail_assignments.all():
            GroupAccess.objects.get_or_create(
                group=parents_group,
                content_type='trail',
                object_id=trail.trail_id,
                defaults={'access_level': 'view_progress'}
            )
        
        messages.success(request, f'Linked to {student.first_name}')
        return redirect('home')
```

**2. Alumni Conversion:**
```python
# learning/management/commands/convert_alumni.py

from django.core.management.base import BaseCommand
from user_management.models import User
from configuration.models import UserGroup, GroupMembership, Membership

class Command(BaseCommand):
    help = 'Convert graduated students to alumni status'
    
    def add_arguments(self, parser):
        parser.add_argument('graduation_date', type=str)
    
    def handle(self, *args, **options):
        graduation_date = options['graduation_date']  # YYYY-MM-DD
        
        # Find users who completed all requirements by date
        users = User.objects.filter(
            trailprogress__completed_at__lte=graduation_date
        ).distinct()
        
        for user in users:
            # Downgrade membership role
            membership = user.memberships.first()
            if membership and membership.role != 'viewer':
                membership.role = 'viewer'
                membership.save()
            
            # Add to alumni group
            alumni_group, _ = UserGroup.objects.get_or_create(
                organization=membership.organization,
                slug=f'alumni-{graduation_date[:4]}',
                defaults={
                    'name': f'Alumni {graduation_date[:4]}',
                    'group_type': 'alumni',
                    'metadata': {'graduation_year': graduation_date[:4]}
                }
            )
            
            GroupMembership.objects.get_or_create(
                user=user,
                group=alumni_group,
                defaults={'role': 'member', 'status': 'active'}
            )
            
            self.stdout.write(f'✅ Converted {user.email} to alumni')

# Run: python manage.py convert_alumni 2026-07-26
```

**3. Content Filtering by Group:**
```python
# home/views.py - Update to filter by group

def home(request):
    # ... existing org/company filtering ...
    
    # NEW: Filter by group membership
    user_groups = request.user.group_memberships.filter(
        status='active'
    ).values_list('group_id', flat=True)
    
    if user_groups:
        # Get content accessible via groups
        group_access = GroupAccess.objects.filter(
            group_id__in=user_groups
        )
        
        # Trails accessible via groups
        for access in group_access.filter(content_type='trail'):
            if access.object_id:
                trails |= Trail.objects.filter(id=access.object_id)
            else:
                # Organization-wide access
                trails |= Trail.objects.filter(
                    organization=request.active_organization
                )
    
    # ... rest of view ...
```

**4. Templates:**
```html
<!-- console/templates/parent_student_link.html -->
<div class="max-w-md mx-auto p-8">
    <h1 class="text-2xl font-bold mb-6">Link to Your Child</h1>
    
    <form method="post" class="space-y-4">
        {% csrf_token %}
        <div>
            <label class="block text-sm font-medium mb-1">
                Student Email Address
            </label>
            <input
                type="email"
                name="student_email"
                required
                class="w-full px-4 py-2 border rounded-lg"
                placeholder="student@school.com"
            >
        </div>
        
        <button
            type="submit"
            class="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
        >
            Link Student
        </button>
    </form>
</div>

<!-- console/templates/alumni_dashboard.html -->
<div class="p-8">
    <h1 class="text-2xl font-bold mb-6">Alumni Community</h1>
    
    <div class="grid grid-cols-3 gap-4 mb-8">
        <div class="bg-blue-50 p-4 rounded-lg">
            <h3 class="font-semibold">Alumni Directory</h3>
            <p>{{ alumni_count }} members</p>
        </div>
        <div class="bg-green-50 p-4 rounded-lg">
            <h3 class="font-semibold">Events & Networking</h3>
            <p>{{ upcoming_events }} upcoming</p>
        </div>
        <div class="bg-purple-50 p-4 rounded-lg">
            <h3 class="font-semibold">Mentorship Program</h3>
            <p>{{ mentors }} mentors available</p>
        </div>
    </div>
</div>
```

**Checklist Week 4:**
- [ ] ParentStudentLinkingView created & tested
- [ ] convert_alumni management command created & tested
- [ ] Home view filters content by group
- [ ] Templates created (parent_student_link, alumni_dashboard)
- [ ] Parent can see only linked child's progress
- [ ] Alumni can access view-only content
- [ ] Department groups visible in admin
- [ ] Tests pass: test_parent_student_flow.py, test_alumni_conversion.py

---

**Files Created/Modified (Phase 3.2):**
```
NEW MODELS:
- configuration/models.py: UserGroup, GroupMembership, GroupAccess

MODIFIED:
- configuration/admin.py (add 3 admins for new models)
- home/views.py (add group-based content filtering)
- console/views.py (add ParentStudentLinkingView)
- courses/urls.py (add parent linking URL)

NEW:
- learning/management/commands/convert_alumni.py
- console/templates/parent_student_link.html
- console/templates/alumni_dashboard.html
- tests/test_user_groups.py, test_parent_student_flow.py

MIGRATIONS:
- configuration/migrations/00XX_add_user_groups.py
```

**Database Changes:**
- UserGroup: New table (organization, name, group_type, metadata)
- GroupMembership: New table (user, group, linked_user, role, status)
- GroupAccess: New table (group, content_type, object_id, access_level)

---

#### Phase 3.3: Hierarchical Departments (Future - Post 3.2)
**Scope:** Department hierarchy + escalation + budget management
**Effort:** 4 weeks (complex)
**Complexity:** High (introduces tree structure)

```
NOT THIS WEEK - Save for later:
- Hierarchical org units (CEO → Managers → Teams)
- Budget allocation by department
- Escalation workflows
- Approval chains
```

---

### Viability Assessment

| Feature | Viável? | Por quê | Timeline |
|---------|---------|---------|----------|
| **Compliance Training** | ✅ SIM | Reutiliza Membership + Trail | 2 weeks |
| **Parent-Student Groups** | ✅ SIM | Simple M2M relationship | 2 weeks |
| **Alumni Groups** | ✅ SIM | Just flag + GroupMembership | 2 weeks |
| **Department Groups** | ✅ SIM | Flat structure (no hierarchy) | 2 weeks |
| **Hierarchical Depts** | ⚠️ DEPOIS | Tree structure (complex) | 4 weeks |
| **Escalation Chains** | ⚠️ DEPOIS | Workflow engine (complex) | 4 weeks |

---

### Database Schema (Phase 3.1 + 3.2)

```python
# Phase 3.1: Compliance Fields (Add to existing Membership)
Membership
├─ compliance_status (CharField: pending/in_progress/completed)
├─ compliance_due_date (DateTimeField, nullable)
└─ # MembershipAudit already logs all changes

# Phase 3.2: User Groups (New Tables)
UserGroup
├─ id (PK)
├─ organization (FK)
├─ name (CharField)
├─ slug (SlugField, unique per org)
├─ group_type (CharField: parents|alumni|department|custom)
├─ description (TextField, blank)
├─ created_at
└─ updated_at

GroupMembership
├─ id (PK)
├─ user (FK)
├─ group (FK)
├─ role (CharField: admin|member|viewer)
├─ joined_at
└─ status (CharField: active|pending|inactive)

GroupAccess
├─ id (PK)
├─ group (FK)
├─ content_type (CharField: trail|course|publication)
├─ object_id (IntegerField)
├─ access_level (CharField: view|view_progress|download|manage)
└─ created_at
```

---

### Success Criteria

**Phase 3.1 (Compliance):**
- ✅ Compliance trails auto-assigned to new hires
- ✅ Compliance status dashboard for managers
- ✅ Audit trail shows all compliance events
- ✅ Notifications sent for overdue trainings

**Phase 3.2 (Groups):**
- ✅ Parents can view student progress
- ✅ Alumni have read-only access
- ✅ Departments have group dashboards
- ✅ Content filters by group membership

---

## Próximos Passos

**Imediato (Agora):**
1. ✅ Finish Phase 2 Week 5 (Hardening)
2. ✅ Deploy v2.0.0-enterprise-users

**Próximas 2 Semanas:**
1. ✅ Phase 3.1: Compliance Training (Week 1-2) - COMPLETE (2026-07-26)
2. [ ] Phase 3.2: User Groups (Week 3-4) - NEXT

**Depois (4+ Semanas):**
- [ ] Hierarchical departments (Phase 3.3)
- [ ] Workflow/escalation (Phase 3.4)

---

**Document Location:** `/docs/EXECUTION_PLAN.md`
**Last Update:** 2026-07-26 (Phase 3.1 Complete)
**Status:** Ready for Phase 3.2 (User Groups)
**Next:** Begin Week 3 - UserGroup model + admin interface
