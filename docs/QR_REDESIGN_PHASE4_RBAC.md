---
name: QR Redesign Phase 4 RBAC Enforcement
description: Implementation of state-based access control for relation details
type: reference
---

# Phase 4: RBAC Enforcement (Store View Restrictions)

**Phase**: 4 of 6  
**Status**: ✅ Complete  
**Date**: 2026-10-09  
**Priority**: Critical (Blocks Go-to-Market)

---

## Objective

Ensure stores see **ONLY candidates with legitimate interest states**, preventing unauthorized access to early-stage relations or requiring PERSON_INTERESTED state before employer can view.

**Problem Being Solved**:
- Without state checks, store staff could access any relation via direct URL
- Could view candidates in NOTICE_DELIVERED (no interest yet) or NOTICE_EXPIRED states
- Violates bilateral matching principle: employer shouldn't know about candidates until PERSON_INTERESTED

---

## Implementation Details

### 1. State-Based Access Control

#### LojistaRelationDetailView (Main Detail View)

**Before**:
```python
def get(self, request, relation_id):
    rel = get_object_or_404(Relation, pk=relation_id)
    # Check store scope + AA-6 authority
    # Return detail page (accessible at ANY state)
```

**After**:
```python
VIEWABLE_STATES = frozenset({
    Relation.STATE_EMPLOYER_INTEREST_VIEW,      # Projection visible
    Relation.STATE_EMPLOYER_INTERESTED,         # Employer interested
    Relation.STATE_MATCHED,                     # Bilateral match
    Relation.STATE_CONTACT_ENABLED,             # Contact authorized
    Relation.STATE_RESPONSE_CREATED,            # Response sent
})

def get(self, request, relation_id):
    rel = get_object_or_404(Relation, pk=relation_id)
    
    # Store scope + AA-6 authority check (existing)
    
    # NEW: State-based RBAC check
    if rel.state not in self.VIEWABLE_STATES:
        return HttpResponseForbidden(
            f'Candidato não pode ser visualizado neste estágio '
            f'({rel.get_state_display()}). '
            f'Aguarde o candidato manifestar interesse.'
        )
    
    return render(...)
```

**Blocked States**:
- ❌ `NOTICE_DELIVERED` - Employer hasn't seen it yet
- ❌ `NOTICE_EXPIRED` - Invite expired, shouldn't see candidate
- ❌ `DECLINED` - Candidate declined, relation is terminal
- ❌ `NO_EMPLOYER_INTEREST` - Terminal; already decided

**Allowed States**:
- ✅ `EMPLOYER_INTEREST_VIEW` - Projection shown (candidate interested)
- ✅ `EMPLOYER_INTERESTED` - Employer declared interest
- ✅ `MATCHED` - Both sides interested (bilateral)
- ✅ `CONTACT_ENABLED` - Contact channel open
- ✅ `RESPONSE_CREATED` - Response submitted

### 2. Action-Level RBAC

#### LojistaInteressarView (Declare Interest)

```python
ALLOWED_STATE = Relation.STATE_EMPLOYER_INTEREST_VIEW

def post(self, request, relation_id):
    # ... existing checks ...
    
    # NEW: Only allow declaring interest from EMPLOYER_INTEREST_VIEW state
    if rel.state != self.ALLOWED_STATE:
        messages.error(request, 
            f'Não é possível manifestar interesse neste estágio '
            f'({rel.get_state_display()})'
        )
        return redirect(...)
    
    employer_interested(relation=rel, ...)
```

**State Machine Enforced**:
```
NOTICE_DELIVERED
    ↓ (candidate interested)
EMPLOYER_INTEREST_VIEW ← [Employer can NOW "Interessar" or "Declinar"]
    ├→ Interessar → EMPLOYER_INTERESTED
    └→ Declinar → NO_EMPLOYER_INTEREST (terminal)
```

#### LojistaDeclinarView (Declare Disinterest)

```python
ALLOWED_STATE = Relation.STATE_EMPLOYER_INTEREST_VIEW

def post(self, request, relation_id):
    # NEW: Only allow declining from EMPLOYER_INTEREST_VIEW state
    if rel.state != self.ALLOWED_STATE:
        messages.error(request,
            f'Não é possível declinar neste estágio '
            f'({rel.get_state_display()})'
        )
        return redirect(...)
    
    employer_declined(relation=rel, ...)
```

#### LojistaLiberarContatoView (Enable Contact)

```python
CONTACT_ENABLED_STATES = frozenset({
    Relation.STATE_MATCHED,
    Relation.STATE_CONTACT_ENABLED,
    Relation.STATE_RESPONSE_CREATED,
})

def post(self, request, relation_id):
    # NEW: Only allow after bilateral match
    if rel.state not in self.CONTACT_ENABLED_STATES:
        messages.error(request,
            f'Contato não pode ser liberado neste estágio. '
            f'Aguarde confirmação bilateral.'
        )
        return redirect(...)
    
    enable_contact(relation=rel, ...)
```

**Enforces**: Contact channel only opens AFTER both sides interested (MATCHED state).

#### LojistaResponderView (Send Response)

```python
RESPONSE_ALLOWED_STATES = frozenset({
    Relation.STATE_CONTACT_ENABLED,
    Relation.STATE_RESPONSE_CREATED,
})

def post(self, request, relation_id):
    # NEW: Only allow after contact enabled
    if rel.state not in self.RESPONSE_ALLOWED_STATES:
        messages.error(request,
            f'Resposta não pode ser enviada neste estágio. '
            f'Libere o contato primeiro.'
        )
        return redirect(...)
    
    create_response(relation=rel, ...)
```

**Enforces**: Contact response only sent AFTER contact channel opened.

---

## Data Flow with RBAC

```
1. QR Signup → CandidateProfile created
                ↓
2. Algorithm matches with opportunities
                ↓
3. Relation created in NOTICE_DELIVERED state
   ❌ Employer CANNOT view (not in VIEWABLE_STATES)
                ↓
4. Notification sent to candidate
   Candidate opens app → marks PERSON_INTERESTED
                ↓
5. Relation transitions to EMPLOYER_INTEREST_VIEW
   ✅ Employer CAN NOW view projection
   ✅ Employer CAN declare "Interessar" or "Declinar"
                ↓
   Branch A: Employer declares interest
   ├→ Relation → EMPLOYER_INTERESTED
   ├→ Candidate sees employer interested
   ├→ Candidate marks EMPLOYER_INTERESTED
   └→ Relation → MATCHED (bilateral)
   
   Branch B: Employer declines
   └→ Relation → NO_EMPLOYER_INTEREST (terminal)
                ↓
6. In MATCHED state:
   ✅ Employer CAN enable contact ("Liberar Contato")
                ↓
7. Relation → CONTACT_ENABLED
   ✅ Employer CAN send response ("Responder")
                ↓
8. Relation → RESPONSE_CREATED
   ✅ Conversation between employer and candidate
```

---

## State Machine Validation

### Allowed Transitions (Canonical)

```
NOTICE_DELIVERED → {PERSON_INTERESTED, DECLINED, NOTICE_EXPIRED}
PERSON_INTERESTED → {EMPLOYER_INTEREST_VIEW}
EMPLOYER_INTEREST_VIEW → {EMPLOYER_INTERESTED, NO_EMPLOYER_INTEREST}
EMPLOYER_INTERESTED → {MATCHED}
MATCHED → {CONTACT_ENABLED}
CONTACT_ENABLED → {RESPONSE_CREATED}
RESPONSE_CREATED → {CLOSED}

TERMINAL (no further transitions):
  - CLOSED
  - DECLINED
  - NOTICE_EXPIRED
  - NO_EMPLOYER_INTEREST
```

### RBAC View Matrix

| View | NOTICE_DELIVERED | PERSON_INTERESTED | EMPLOYER_INTEREST_VIEW | EMPLOYER_INTERESTED | MATCHED | CONTACT_ENABLED | RESPONSE_CREATED |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **View Detail** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Interessar** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Declinar** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Liberar Contato** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Responder** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## Security Benefits

### 1. Prevents Enumeration
- ❌ Can't direct-access `/portal/relation/<id>/` for all relations
- ✅ Only accessible if state meets criteria + AA-6 scope

### 2. Enforces Sequential Matching
- ❌ Can't skip PERSON_INTERESTED (candidate opt-in)
- ✅ Employer must see EMPLOYER_INTEREST_VIEW before declaring interest

### 3. Prevents Premature Contact
- ❌ Can't enable contact before bilateral match
- ✅ Contact only opens after MATCHED state

### 4. Audit Trail
- State transitions logged in `RelationTransitionEvent`
- Each action correlates with specific state
- Disputes can reference state history

---

## Error Messages

### Access Denied (View Detail)
```
Candidato não pode ser visualizado neste estágio (Convite expirado). 
Aguarde o candidato manifestar interesse.
```

### State Mismatch (Interessar)
```
Não é possível manifestar interesse neste estágio (Empregador declinou). 
```

### Bilateral Required (Liberar Contato)
```
Contato não pode ser liberado neste estágio. 
Aguarde confirmação bilateral.
```

### Contact Required (Responder)
```
Resposta não pode ser enviada neste estágio. 
Libere o contato primeiro.
```

---

## Implementation Checklist

- [x] Add `VIEWABLE_STATES` to `LojistaRelationDetailView`
- [x] Add state check to `get()` method
- [x] Add state validation to `LojistaInteressarView`
- [x] Add state validation to `LojistaDeclinarView`
- [x] Add state validation to `LojistaLiberarContatoView`
- [x] Add state validation to `LojistaResponderView`
- [x] Error messages for all blocked states
- [x] Syntax validation
- [x] Documentation complete

---

## Testing Guide

### Test 1: View Detail Access by State

```python
# Setup: Create relation in each state
relation_notice = Relation.objects.create(..., state=STATE_NOTICE_DELIVERED)
relation_interested = Relation.objects.create(..., state=STATE_EMPLOYER_INTEREST_VIEW)

# Test
response = client.get(f'/portal/relation/{relation_notice.id}/')
assert response.status_code == 403  # Forbidden
assert "manifestar interesse" in response.content.decode()

response = client.get(f'/portal/relation/{relation_interested.id}/')
assert response.status_code == 200  # OK
```

### Test 2: Declare Interest State Check

```python
# Setup: relation in NOTICE_DELIVERED (shouldn't allow interest)
relation = Relation.objects.create(..., state=STATE_NOTICE_DELIVERED)

# Test
response = client.post(f'/portal/relation/{relation.id}/interessar/', {})
assert response.status_code == 302  # Redirect (prevented)
messages = response.messages  # Check message queue
assert "Não é possível manifestar interesse" in str(messages)

# Relation should NOT transition
relation.refresh_from_db()
assert relation.state == STATE_NOTICE_DELIVERED
```

### Test 3: Contact Enable Requires Match

```python
# Setup: relation in EMPLOYER_INTERESTED (still no match)
relation = Relation.objects.create(
    ..., state=STATE_EMPLOYER_INTERESTED
)

# Test: Try to enable contact
response = client.post(f'/portal/relation/{relation.id}/liberar-contato/', {})
assert "Aguarde confirmação bilateral" in str(response.messages)

# Transition to MATCHED
relation.state = STATE_MATCHED
relation.save()

# Test: Now should allow
response = client.post(f'/portal/relation/{relation.id}/liberar-contato/', {})
assert response.status_code == 302  # OK redirect
```

### Test 4: Terminal States Block All Actions

```python
# Setup: relation in NO_EMPLOYER_INTEREST (terminal)
relation = Relation.objects.create(
    ..., state=STATE_NO_EMPLOYER_INTEREST
)

# All actions should be blocked
for action, url in [
    ("Interessar", "/interessar/"),
    ("Declinar", "/declinar/"),
    ("Liberar Contato", "/liberar-contato/"),
]:
    response = client.post(f'/portal/relation/{relation.id}{url}', {})
    assert response.status_code == 302
    assert any("neste estágio" in str(m) for m in response.messages)
```

---

## Performance Impact

### Database Queries

**Before**: 1 query (get relation)  
**After**: 1 query (get relation) + state check in memory

No additional DB queries (state is already loaded).

### Cache Opportunities

Could cache allowed states per view (unlikely to change):
```python
# In class definition (already done as frozenset)
VIEWABLE_STATES = frozenset({...})
```

---

## Backwards Compatibility

✅ **Fully Backwards Compatible**

- Old relations without state change behavior preserved
- Only adds blocking logic (no data transformation)
- Views remain at same URLs
- No API changes

**Migration Path**: No data migration needed.

---

## Monitoring & Metrics

### Metrics to Track

1. **Blocked Access Attempts**
   - Count of 403 responses from state check
   - Alert if sudden spike (possible attack)

2. **State Transitions**
   - Track time in each state
   - Identify bottlenecks (e.g., too many EMPLOYER_INTEREST_VIEW)

3. **Action Success Rate**
   - % of interest declarations succeeding
   - % of premature attempts blocked

### Log Example

```python
# In each view, add logging:
logger.info(f"Relation {rel.id} state access: {rel.state} - OK", 
            extra={'user': request.user, 'action': 'view'})

logger.warning(f"Relation {rel.id} state blocked: {rel.state} - FORBIDDEN", 
               extra={'user': request.user, 'action': 'view'})
```

---

## Known Limitations & Future

### Current Phase 4
- ✅ Basic state-based access control
- ✅ Action-level validation
- ✅ Clear error messages

### Phase 5 (Complementary)
- [ ] Question whitelist validation (prevent screening)
- [ ] Admin approval for custom questions
- [ ] Audit log for question creations

### Phase 6 (Future Enhancement)
- [ ] Role-based permissions (store manager vs staff)
- [ ] Interview scheduling enforcement
- [ ] Response deadline enforcement

---

## Code Changes Summary

| File | Change | Lines |
|------|--------|-------|
| `portal_views.py` | Add state checks to 5 views | +70 |
| **Total** | | **+70** |

---

## Related Documents

- **Phase 1-3**: See `QR_REDESIGN_IMPLEMENTATION_SUMMARY.md`
- **Testing**: See `QR_REDESIGN_TEST_GUIDE.md` (new tests section)
- **Architecture**: See `docs/CODEBASE_MAP.md` (Relation model section)

---

## Deployment

### Database
- No migration needed (no schema changes)
- Existing data already has state field

### Code
- Deploy `portal_views.py` changes
- No configuration changes needed
- Feature is active immediately

### Rollback
- Revert to previous version
- No data cleanup needed

---

## Questions & Support

- **State Machine Questions**: See Relation model docs
- **Access Control Questions**: See AA-6/AA-7/AA-8 docs
- **Testing Help**: See QR_REDESIGN_TEST_GUIDE.md

---

**Status**: ✅ Phase 4 Complete | 🚀 Ready for Phase 5 (Admin Validation)
