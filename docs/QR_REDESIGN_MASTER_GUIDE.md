---
name: QR Redesign Master Implementation Guide
description: Complete reference for all 6 phases of QR redesign
type: reference
---

# QR Redesign: Master Implementation Guide

**Project**: MatchCo Platform - Universal QR with Store-Customizable Signup  
**Status**: ✅ **Phases 1-5 Complete** | 🚀 **Phase 6 Ready**  
**Last Updated**: 2026-10-09  
**Total Scope**: 6 Phases, 90-day timeline  
**Progress**: 83% (5 of 6 phases complete)

---

## 📋 Quick Navigation

### Documentation by Phase

| Phase | Goal | Status | File |
|-------|------|--------|------|
| **1** | Data Model | ✅ Complete | QR_REDESIGN_IMPLEMENTATION_SUMMARY.md |
| **2-3** | Views & Signup | ✅ Complete | QR_REDESIGN_IMPLEMENTATION_SUMMARY.md |
| **4** | RBAC Enforcement | ✅ Complete | QR_REDESIGN_PHASE4_RBAC.md |
| **5** | Admin Validation | ✅ Complete | QR_REDESIGN_PHASE5_ADMIN_VALIDATION.md |
| **6** | E2E Testing | 📋 Ready | QR_REDESIGN_PHASE6_TESTING.md (TBD) |

---

## 🎯 What's Been Built (Phases 1-4)

### Phase 1: Data Model ✅
**File**: `docs/CODEBASE_MAP.md` (Architecture section)

**Model**: `StoreSignupConfiguration`
- Links store to questionnaire templates
- Separate templates for profile vs job applications
- Validation ensures organization alignment
- Migration: `0072_add_store_signup_configuration`

**Key Feature**: "One QR → Multiple stores with custom questions"

---

### Phases 2-3: Dynamic Signup Flow ✅
**File**: `docs/QR_REDESIGN_IMPLEMENTATION_SUMMARY.md`

**3 New Views**:
1. `StoreChooserView` (`/candidato/loja/escolher/`)
   - Candidate selects store
   - Loads active `StoreSignupConfiguration` entries

2. `ActionChooserView` (`/candidato/acao/escolher/`)
   - Choose: Profile Creation OR Job Application
   - Skips if only one action available

3. `CustomSignupView` (`/candidato/formulario/`)
   - Dynamic form from store's questionnaire
   - Always fresh (no pre-filling)
   - Supports all question types (text, boolean, select, date, scale)
   - Phone verification via OTP

**Templates** (Tailwind + Dark Mode):
- `store_chooser.html` — Radio selection
- `action_chooser.html` — Action cards  
- `custom_signup.html` — Dynamic form (180+ lines)

**Integration**: OTP verification creates `CandidateProfile` + `CandidateSignupAnswer`

---

### Phase 4: RBAC Enforcement ✅
**File**: `docs/QR_REDESIGN_PHASE4_RBAC.md`

**Problem Solved**: Stores were accessing candidates in any state (even NOTICE_DELIVERED).

**Solution**: State-based access control

**Protected Views**:
| View | Allowed States | Prevents |
|------|---|---|
| View Detail | EMPLOYER_INTEREST_VIEW+ | Early-stage access |
| Interessar | EMPLOYER_INTEREST_VIEW only | Premature interest |
| Declinar | EMPLOYER_INTEREST_VIEW only | Declining wrong state |
| Liberar Contato | MATCHED+ | Contact before match |
| Responder | CONTACT_ENABLED+ | Response before contact |

**State Machine**:
```
NOTICE_DELIVERED
    → PERSON_INTERESTED  
    → EMPLOYER_INTEREST_VIEW ← [Employer sees, can decide]
    → EMPLOYER_INTERESTED
    → MATCHED ← [Bilateral confirmed]
    → CONTACT_ENABLED ← [Can exchange contact]
    → RESPONSE_CREATED
    → CLOSED
```

---

## 🔧 Phase 5: Admin Question Validation ✅
**File**: `docs/QR_REDESIGN_PHASE5_ADMIN_VALIDATION.md`

**Implementation Complete**:
- ✅ Question whitelist (30+ allowed patterns)
- ✅ Question blacklist (35+ forbidden patterns)
- ✅ Admin warning system
- ✅ Audit log for question changes
- ✅ Ops approval workflow
- ✅ Auto-compliance checking
- ✅ Migration: `0073_phase5_admin_validation`

**Whitelist Coverage**:
- Availability & schedule
- Experience & skills
- Practical knowledge (POS, inventory, sales)
- Personal qualities (communication, teamwork)
- Transport & certifications

**Blacklist Coverage**:
- Age, birth, education, religion, sexuality, gender
- Marital/family status, political opinion
- Salary, health, disability, race, ethnicity
- Criminal record, appearance, lifestyle

**Ops Workflow**:
1. Question created → Auto-check compliance
2. Whitelist match → APPROVED (live immediately)
3. Blacklist match → REJECTED (error shown)
4. No match → REQUIRES_OPS_APPROVAL (ops reviews)
5. Audit log captures all decisions

---

## 🧪 Phase 6: E2E Testing (Ready to Implement)

**Goal**: Full test coverage of critical paths

**Implementation Needed**:
- [ ] Selenium/Playwright test suite
- [ ] Signup → Match → Interest → Contact flow
- [ ] Performance tests under load
- [ ] Browser compatibility (Chrome, Firefox, Safari, Mobile)

**Critical Paths**:
1. Candidate: signup → match → interest → contact
2. Employer: declare need → view candidates → declare interest → enable contact
3. Store: create questions → receive responses → track candidates

**Estimated**: 2-3 days

---

## 📁 Documentation Structure

```
docs/
├── CODEBASE_MAP.md                           ← Full architecture
├── QR_REDESIGN_MASTER_GUIDE.md               ← THIS FILE (navigation hub)
├── QR_REDESIGN_IMPLEMENTATION_SUMMARY.md     ← Phases 1-3 details
├── QR_REDESIGN_PHASE4_RBAC.md                ← Phase 4 RBAC enforcement
├── QR_REDESIGN_PHASE5_ADMIN_VALIDATION.md    ← Phase 5 compliance whitelist
├── QR_REDESIGN_TEST_GUIDE.md                 ← Manual testing procedures
└── README.md                                 ← Docs index
```

### How to Use

1. **New to the project?** → Start with `CODEBASE_MAP.md`
2. **Understand QR flow?** → Read `QR_REDESIGN_IMPLEMENTATION_SUMMARY.md`
3. **Debug RBAC issues?** → Check `QR_REDESIGN_PHASE4_RBAC.md`
4. **Test manually?** → Follow `QR_REDESIGN_TEST_GUIDE.md`
5. **Implement Phase 5?** → Plan from `QR_REDESIGN_MASTER_GUIDE.md`

---

## ✅ Deployment Checklist

### Pre-Launch (Phases 1-4)
- [x] Data model created + migration applied
- [x] Views implemented (store, action, form)
- [x] OTP integration working
- [x] RBAC enforcement active
- [x] Syntax validated
- [x] Documentation complete
- [x] Backwards compatibility verified

### Phase 5 (Admin Validation)
- [ ] Question whitelist defined
- [ ] Admin warning logic added
- [ ] Audit log captures changes
- [ ] Approval workflow implemented

### Phase 6 (E2E Testing)
- [ ] Test suite written
- [ ] All browsers tested
- [ ] Load tested (100+ concurrent)
- [ ] Performance baselines established

---

## 🚀 Deployment Process

### Step 1: Database
```bash
cd matchco
python manage.py migrate recruitment
```
Applies migration `0072_add_store_signup_configuration`

### Step 2: Code
Deploy updated files:
- `matchco/recruitment/models.py`
- `matchco/recruitment/views.py`
- `matchco/recruitment/portal_views.py`
- `matchco/recruitment/urls_public.py`
- Templates (3 new files)

### Step 3: Verify
```bash
# Check no syntax errors
python -m py_compile recruitment/models.py recruitment/views.py

# Run migrations
python manage.py migrate recruitment

# Load test
python manage.py shell  # Verify StoreSignupConfiguration accessible
```

### Step 4: Monitor
Watch for:
- 403 errors on `/portal/relation/*/` (RBAC working)
- Form rendering on `/candidato/formulario/` (views working)
- OTP delivery (integration OK)

---

## 📊 Metrics & Monitoring

### Success Indicators (Post-Launch)

**Adoption**:
- % of signups using new flow (target: 80%+)
- Average questions per signup (target: 3-6, up from 6 fixed)

**Quality**:
- Form abandonment rate (target: <20%)
- OTP delivery success (target: >98%)

**Security**:
- RBAC blocks per day (baseline)
- Attempted early-stage access (should be 0)

**Performance**:
- Form render time (<200ms)
- Store list load (<100ms)

---

## 🐛 Troubleshooting

### Issue: "No tenant for hostname"
**Cause**: Multi-tenant system requires proper domain  
**Fix**: Use hostname from `.env` ALLOWED_HOSTS or test via CLI

### Issue: 403 Forbidden on relation detail
**Expected behavior** if relation state not in VIEWABLE_STATES  
**Check**: `relation.state` and `LojistaRelationDetailView.VIEWABLE_STATES`

### Issue: Form not rendering
**Debug**:
```python
from recruitment.models import StoreSignupConfiguration
config = StoreSignupConfiguration.objects.filter(store_id=<id>).first()
if not config:
    print("No config for store")
if not config.profile_questionnaire:
    print("No questionnaire template")
```

### Issue: OTP not sending
**Debug**:
```python
from recruitment.services import request_otp
try:
    otp, created = request_otp(mobile="+5511998765432", email="test@example.com")
    print(f"OTP: {otp}")
except Exception as e:
    print(f"Error: {e}")
```

---

## 🔐 Security Checklist

- [x] CSRF tokens on forms
- [x] Session isolation (one session = one user)
- [x] Phone verification (OTP)
- [x] State-based RBAC (Phases 1-4)
- [x] Org/store boundary enforcement
- [ ] Question text sanitization (Phase 5)
- [ ] Rate limiting on OTP (Phase 5)

---

## 📈 Roadmap & Timeline

### Week 1 (Phases 1-4) ✅
- Days 1-3: Model + Views + Templates
- Days 4-5: RBAC Enforcement
- **Status**: DONE

### Week 2 (Phase 5)
- Days 1-2: Question Whitelist + Admin UI
- Day 3: Approval Workflow
- Day 4-5: Testing + Cleanup

### Week 3 (Phase 6)
- Days 1-4: E2E Test Suite
- Day 5: Load Testing + Performance Tuning

### Week 4 (Go-Live)
- Day 1: Final QA
- Day 2: Deploy to staging
- Day 3-5: Monitor + Support

---

## 📞 Contact & Support

### Questions?
- **Architecture**: See `docs/CODEBASE_MAP.md`
- **Phase Details**: See specific phase document
- **Testing**: See `docs/QR_REDESIGN_TEST_GUIDE.md`

### Report Issues
Create task in Linear `INGEST` project with:
- Phase number
- View/file affected
- Expected vs actual behavior

---

## 🎓 Key Learning Resources

### Understanding Relation States
- Read: `matchco/recruitment/models.py` line 2860 (Relation class)
- Understand: ALLOWED_TRANSITIONS state machine

### Understanding Multi-Tenancy
- Read: `docs/CODEBASE_MAP.md` section "Multi-Tenant Architecture"
- Understand: Schema-per-tenant via `django-tenants`

### Understanding Authority Scopes
- Read: `matchco/recruitment/models.py` - AuthorityScope class
- Understand: AA-1 through AA-8 hierarchy

---

## 🎉 Summary: What's Live

✅ **Live Phases**:
- Phase 1: StoreSignupConfiguration model
- Phase 2-3: Dynamic signup flow (store → action → form)
- Phase 4: RBAC enforcement (state-based access)

🎯 **Key Feature**: One universal QR → Store-customizable forms

📊 **Impact**:
- Merchants can define their own questions
- Candidates fill only relevant fields
- Stores see only legitimate prospects
- Backward compatible with old signup

---

## 📝 Version Info

| Component | Version | Date |
|-----------|---------|------|
| MatchCo Platform | v2.0.0-alpha.2 | 2026-10-09 |
| QR Redesign | Phases 1-4 | 2026-10-09 |
| Migration | 0072 | 2026-10-09 |

---

**Status**: ✅ **PHASES 1-4 COMPLETE** | Ready to deploy | Next: Phase 5 (Admin Validation)
