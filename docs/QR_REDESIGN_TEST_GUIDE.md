---
name: QR Redesign Test Guide
description: Step-by-step testing instructions for the new store-customizable signup flow
type: reference
---

# QR Redesign Testing Guide

**Status**: Phase 1-3 Implementation Complete  
**Date**: 2026-10-09  
**Last Updated**: 2026-10-09

## Overview

The QR redesign enables one universal QR code that routes candidates to store-customizable signup forms. This guide covers manual testing of the new flow.

## Test Environment Setup

### 1. Prerequisites

```bash
cd /Users/franco/Dev/matchco-platform
source .venv/bin/activate  # or use .venv/bin/python directly
```

### 2. Database & Migrations

Migrations are already applied:
```bash
python matchco/manage.py migrate recruitment
```

### 3. Test Data

Use existing data:
- **Organization**: Bourbon Shopping (ID: 1)
- **Store**: 5àsec (ID: 11) 
- **Entry Point**: `4d584a8a-6bf2-4f90-8910-23cc50e356a5`
- **Questionnaire**: ID 20 (Test Quick Form)
- **Store Config**: ID 1 (already linked)

Or create new test data:
```python
from recruitment.models import (
    RecruitmentOrganization, RecruitmentStore,
    QuestionnaireTemplate, QuestionnaireQuestion,
    StoreSignupConfiguration, EntryPoint
)
from django.utils import timezone

# Get existing org/store
org = RecruitmentOrganization.objects.get(pk=1)
store = RecruitmentStore.objects.get(pk=11)

# Create questionnaire
q = QuestionnaireTemplate.objects.create(
    organization=org,
    code='my_test_form',
    name='My Test Form',
    status='published',
    is_approved_by_ops=True,
    published_at=timezone.now(),
)

# Add questions
QuestionnaireQuestion.objects.create(
    template=q,
    key='q1',
    label='Question 1?',
    field_type='text',
    required=True,
    order=1,
)

# Link to store
StoreSignupConfiguration.objects.get_or_create(
    store=store,
    defaults={
        'organization': org,
        'profile_questionnaire': q,
        'is_active': True,
    }
)
```

## Testing Paths

### Path A: Entry Point → Store Chooser → Action Chooser → Custom Form

**Start URL**: `/matchco/entrada/{entry_point_id}/`

**Expected Flow**:
1. ✅ Redirect to `/candidato/loja/escolher/`
2. ✅ Display list of active stores (filtered by `StoreSignupConfiguration.is_active=True`)
3. ✅ User selects store → session saves `ep_store_id`
4. ✅ Redirect to `/candidato/acao/escolher/`
5. ✅ Show available actions based on `StoreSignupConfiguration`:
   - Profile creation (if `profile_questionnaire` set)
   - Job application (if `job_questionnaire` set)
6. ✅ User selects action → session saves `signup_action`
7. ✅ Redirect to `/candidato/formulario/`
8. ✅ Display dynamic form with questions from questionnaire
9. ✅ User fills form + provides phone/email
10. ✅ OTP sent to phone
11. ✅ Redirect to OTP verification

### Path B: Direct Store Access (Pre-Scoped)

**Precondition**: Entry point already has `scope_store` set

**Start URL**: `/matchco/entrada/{entry_point_id}/`

**Expected Flow**:
1. ✅ Skip store chooser (store already in session)
2. ✅ Check if only one action available
   - If only profile or job: skip action chooser → go directly to form
   - If both: show action chooser

### Path C: Single Action Shortcut

**Precondition**: Store config has only one template (e.g., profile but no job)

**Start URL**: `/matchco/entrada/{entry_point_id}/` (with scoped store)

**Expected Flow**:
1. ✅ Skip both store and action choosers
2. ✅ Go directly to `/candidato/formulario/`

## Form Rendering Tests

### Question Types Supported

Test each question type by adding to questionnaire:

| Type | Expected Behavior | Test Method |
|------|-------------------|------------|
| `text` | Single-line text input | Type "hello" |
| `textarea` | Multi-line text input | Type multi-line text |
| `boolean` | Radio: Sim/Não | Click each radio |
| `single_choice` | Dropdown select | Open dropdown, select option |
| `multiple_choice` | Checkboxes | Check multiple boxes |
| `number` | Number spinner | Enter "42" |
| `date` | Date picker | Pick a date |
| `scale` | Radio 1-5 | Click scale value |

### Form Validation

Tests to run:

1. **Required Field Validation**:
   - Leave required question empty
   - Try to submit
   - ✅ Error message appears
   - ✅ Form re-displays with previous responses preserved

2. **Phone Field Validation**:
   - Submit without phone
   - ✅ Error: "Telefone é obrigatório"
   - Submit with phone but invalid
   - ✅ Validation via OTP request

3. **Always-Fresh Form**:
   - Fill and submit form once
   - Go back to store chooser
   - Select same store → action → form again
   - ✅ Form is completely blank (no pre-filling)

## OTP Integration Tests

### OTP Request

1. Fill form and click "Enviar"
2. ✅ OTP sent to phone
3. ✅ Redirect to `/candidato/entrar/codigo/`
4. ✅ Mobile shown: `"(11) 98765-****"`

### OTP Verification

1. Enter OTP code
2. ✅ New CandidateProfile created
3. ✅ CandidateSignupAnswer created with:
   - `questionnaire_template`: the form used
   - `responses`: JSON with all answers
   - `business_unit`: the selected store
4. ✅ Redirect to `/candidato/signup/pronto/`

### Session State

Verify session contains:
```python
session['pending_custom_signup'] = {
    'store_id': <int>,
    'action': 'profile' | 'job',
    'questionnaire_id': <int>,
    'mobile': '<normalized phone>',
    'email': '<lowercase email>',
    'responses': {'<question_id>': '<answer>', ...},
}
```

## Backwards Compatibility Tests

### Old Flow Still Works

1. Test `/candidato/signup/` (old fixed form)
2. ✅ Old MatchcoSignupView still renders
3. ✅ Works with or without Entry Point
4. ✅ No interference with new flow

### Side-by-Side Access

1. Open new flow: `/matchco/entrada/{ep_with_config}/`
2. In another tab, open old flow: `/candidato/signup/`
3. ✅ Both work independently
4. ✅ Sessions don't conflict

## Database Tests

### Verify Data Created

After successful signup:

```python
from recruitment.models import CandidateSignupAnswer, CandidateProfile

# Find the answer
answer = CandidateSignupAnswer.objects.latest('created_at')

# Verify structure
assert answer.questionnaire_template.code == 'my_test_form'
assert answer.business_unit_id == 11
assert answer.responses  # Non-empty dict
assert answer.candidate  # Link to profile
```

### Store Config Constraints

Test validation:

```python
from recruitment.models import StoreSignupConfiguration, ValidationError

# Try creating config without templates
try:
    config = StoreSignupConfiguration(
        store=store,
        organization=org,
        # No templates!
    )
    config.full_clean()  # Should raise ValidationError
except ValidationError as e:
    print(e)  # ✅ Should say need at least one template
```

## Performance Tests

### Questionnaire Loading

- Add 50+ questions to questionnaire
- ✅ Form still renders under 1s
- ✅ No N+1 queries (use `select_related`)

### Store Listing

- Add 20+ stores to config
- ✅ Store chooser lists all under 500ms
- ✅ Each store clickable

## Security Tests

### Session Isolation

1. User A fills form (but doesn't submit OTP)
2. User B accesses `/candidato/formulario/` in same browser (new session)
3. ✅ User B gets fresh form
4. ✅ User B doesn't see User A's responses

### CSRF Protection

1. Submit form
2. ✅ CSRF token validated
3. ✅ Attacker can't submit cross-domain

### Phone Verification

1. Submit form with phone "11999999999"
2. OTP sent to that phone only
3. ✅ No OTP sent to email (unless provided)
4. ✅ Identity linked to verified phone

## Template Tests

### Tailwind Styling

- [ ] Store chooser: Orange borders on hover
- [ ] Action chooser: Smooth transitions on selection
- [ ] Custom form: All inputs styled consistently
- [ ] Dark mode: Test with `prefers-color-scheme`
- [ ] Mobile: Test on phone-sized browser

### Accessibility

- [ ] Labels linked to inputs (`for=` attribute)
- [ ] Required fields marked with `*`
- [ ] Error messages red and visible
- [ ] Tab navigation works
- [ ] No keyboard traps

## Integration Tests

### With Existing Systems

1. **OTP Service**:
   - ✅ `request_otp()` called correctly
   - ✅ `verify_otp()` validates code
   - ✅ Phone normalized consistently

2. **Identity Resolution**:
   - ✅ `resolve_or_create_identity()` creates new identity
   - ✅ `CandidateProfile` linked correctly
   - ✅ Handles duplicate emails/phones

3. **Tenant Isolation**:
   - ✅ Responses isolated to tenant schema
   - ✅ Cross-tenant queries fail safely

## Browser Testing Checklist

- [ ] Chrome/Chromium (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile Safari (iPhone)
- [ ] Chrome Android

## Edge Cases to Test

1. **Browser Back Button**:
   - Fill form
   - Submit → redirected to OTP
   - Click back
   - ✅ Form still has data? (depends on session)

2. **Timeout**:
   - Fill form, wait 15 minutes
   - Submit
   - ✅ Error or re-ask for entry point

3. **Duplicate Submission**:
   - Submit form twice quickly
   - ✅ Only one response created

4. **Inactive Store**:
   - Set `StoreSignupConfiguration.is_active=False`
   - Try to access `/candidato/formulario/` with that store
   - ✅ Error or redirect

## Known Issues / TODOs

### Phase 4: RBAC Enforcement
- [ ] Store sees ONLY bilateral-interested candidates
- [ ] `LojistaRelationDetailView` constraints

### Phase 5: Admin Question Validation
- [ ] Prevent screening-type questions
- [ ] Whitelist only practical topics
- [ ] Audit log for admin changes

### Phase 6: E2E Tests
- [ ] Selenium/Playwright test suite
- [ ] Full flow: signup → match → interest → contact

## Test Results Template

```markdown
## Test Session: [Date & Time]

**Tester**: [Name]  
**Browser**: [Chrome/Firefox/Safari + version]  
**Entry Point**: [ID]  
**Store**: [Name]  

### Passed Tests
- [ ] Store chooser displays correctly
- [ ] Action chooser shows both options
- [ ] Form renders all question types
- [ ] Phone validation works
- [ ] OTP sends successfully
- [ ] Profile created in DB
- [ ] Answers saved with responses

### Failed Tests
- [ ] [Issue description + screenshot]

### Notes
[Any observations or improvements]
```

## Quick Test Command

```bash
# Setup
cd /Users/franco/Dev/matchco-platform/matchco
/Users/franco/Dev/matchco-platform/.venv/bin/python manage.py runserver 0.0.0.0:8000

# In browser:
# http://localhost:8000/matchco/entrada/4d584a8a-6bf2-4f90-8910-23cc50e356a5/
```

Then follow Path A (Store Chooser → Action Chooser → Form).

---

**Next Steps**: Phase 4 (RBAC enforcement) and Phase 5 (Admin validation) ready to implement.
