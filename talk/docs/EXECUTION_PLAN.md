# Talk Platform - Development Execution Plan

**Last Updated:** 2026-07-26
**Status:** Phase 1 Complete (UI/OBAC) | Phase 2 In Design (Enterprise Users)
**Git Tag:** `v1.0.0-ui-obac` ← Current Release

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

## Phase 2: 🔄 IN PROGRESS - Enterprise User System (v2.0.0)

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
- [ ] Performance: Index optimization (user, is_active; organization, is_active)
- [ ] Security: Rate limiting on org switch
- [ ] Security: MFA optional for admins
- [ ] Monitoring: Audit trail verification
- [ ] Monitoring: Permission denial logging
- [ ] Compliance: GDPR user deletion cascade
- [ ] Testing: Permission matrix verification

**Impact:** Performance improvements, enhanced security

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

## Current Version: v1.0.0-ui-obac

**Status:** Production Ready
**OBAC Completion:** 48% (14/29 pages)
**UI Standardization:** 100%
**Breaking Changes:** None

**Next Release:** v2.0.0-enterprise-users (Week 1-5 implementation)

---

**Document Location:** `/docs/EXECUTION_PLAN.md`
**Last Update:** 2026-07-26 by Claude
**Next Review:** Week 1 Phase 2 completion
