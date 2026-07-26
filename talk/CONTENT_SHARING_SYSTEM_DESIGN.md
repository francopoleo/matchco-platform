# Content Sharing & Distribution System - Comprehensive Design Document

## Executive Summary

A production-ready system for managers to share curated content packages (single items or groups like trails) directly to users or audience groups. Features include:
- Direct sharing to individuals or audience-filtered groups
- Multi-content packages (like trails but ephemeral)
- Engagement tracking and analytics
- User acknowledgement workflows
- Forward/redistribute capabilities
- Permission-based access control

**Total Value**: Enables Q&A resolution with content, reduces support tickets, increases content engagement

---

## HIGH-LEVEL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ADMIN/MANAGER INTERFACE                          │
│  (Django Admin + Console Views for Content Sharing)                  │
└────────────────────────┬────────────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
          v                             v
┌────────────────────────┐   ┌────────────────────────┐
│  ContentSharePackage   │   │  Audience Resolution   │
│  (New Model)           │   │  (Existing System)     │
└────────────┬───────────┘   └────────────┬───────────┘
             │                             │
             │      ┌──────────────────────┘
             │      │
             v      v
    ┌──────────────────────────┐
    │ ContentShareEvent        │
    │ (Track Distribution)     │
    └────────────┬─────────────┘
                 │
    ┌────────────┴─────────────┐
    │                          │
    v                          v
┌──────────────────────┐  ┌──────────────────────┐
│ UserNotification     │  │ ContentEvent         │
│ (Notification Hub)   │  │ (Analytics)          │
└──────────┬───────────┘  └──────────┬───────────┘
           │                         │
           │    ┌────────────────────┘
           │    │
           v    v
    ┌────────────────────────┐
    │ USER DASHBOARD         │
    │ - Shared Content List  │
    │ - Engagement Tracking  │
    │ - Search/Filter        │
    └────────────────────────┘
```

---

## DATABASE SCHEMA

### 1. ContentSharePackage (Core Model)

The primary entity for sharing content collections:

```python
class ContentSharePackage(models.Model):
    # Metadata
    title                    # "Q3 Compliance Training"
    description              # Why this content is being shared
    slug                     # URL-friendly identifier
    organization             # FK to Organization (tenancy)
    
    # Content bundle
    content_items            # M2M through ContentShareItem
    is_learning_trail        # Boolean: ordered by position
    
    # Audience targeting
    audience_policy          # FK to AudiencePolicy (optional)
    explicit_recipients      # M2M through ExplicitRecipient
    
    # Metadata
    created_by              # FK to User (manager)
    shared_at               # DateTimeField (distribution timestamp)
    expires_at              # DateTimeField (optional)
    is_pinned               # Boolean (show at top)
    
    # Settings
    requires_acknowledgement # Boolean
    track_engagement        # Boolean
    allow_distribution      # Boolean (can users forward?)
    notify_manager_on_open  # Boolean
    
    metadata                # JSONField (custom tags, source)
    created_at              # auto_now_add
    updated_at              # auto_now
```

### 2. ContentShareItem (Items in Package)

Individual content within a package:

```python
class ContentShareItem(models.Model):
    package                 # FK to ContentSharePackage
    content_type            # GenericForeignKey to support:
    object_id               # - Course
    content_object          # - Publication
                            # - Document
                            # - File
                            # - Quiz
    
    position                # PositiveIntegerField (trail order)
    title_override          # Optional display name
    description_override    # Optional context
    required                # Boolean (must complete)
    created_at              # auto_now_add
```

**Supported Content Types**: Course, Publication, Document, File, Quiz, ContentTrail (nested)

### 3. ExplicitRecipient (Direct Recipients)

Track individual users who received shares:

```python
class ExplicitRecipient(models.Model):
    package                 # FK to ContentSharePackage
    recipient_user          # FK to User
    invited_by              # FK to User (who shared)
    invited_at              # DateTimeField
    
    acknowledged_at         # DateTimeField (when confirmed)
    read_at                 # DateTimeField (first view)
    last_read_at            # DateTimeField (most recent)
    forward_count           # PositiveIntegerField
```

### 4. ContentShareEvent (Engagement Analytics)

Immutable event stream for analytics:

```python
class ContentShareEvent(models.Model):
    CHOICES = (
        ('shared', 'Package Shared'),
        ('received', 'Package Received'),
        ('opened', 'Package Opened'),
        ('acknowledged', 'Package Acknowledged'),
        ('item_opened', 'Item Opened'),
        ('item_completed', 'Item Completed'),
        ('forwarded', 'Package Forwarded'),
    )
    
    package                 # FK to ContentSharePackage
    recipient               # FK to User
    event_type              # CharField choices
    content_item            # FK to ContentShareItem (nullable)
    occurred_at             # DateTimeField
    metadata                # JSONField (session, IP, source)
```

### Relationships to Existing Models

- Uses existing `UserNotification` for delivery
- Uses existing `AudiencePolicy` + `Membership` for targeting
- Uses existing `ManagementAssignment` for permission checks
- Integrates with existing notification delivery system

---

## PERMISSION MODEL

### Who Can Share?

```
- Superusers (unrestricted)
- Users with 'sharing.create_share_package' permission
- ManagementAssignment with role='audience_manager' at org level
- Organization admins
```

### Who Can Receive?

```
- Explicitly listed in ExplicitRecipient, OR
- Matches AudiencePolicy via Membership
- Shares respecting organization hierarchy
```

### Content-Specific Rules

```
- Course: Edit permission OR owner
- Publication: Edit permission OR author
- Document: Manage permission OR owner
```

### Who Can Manage?

```
- Superusers
- Creator (within 1 hour grace period)
- ManagementAssignment with appropriate role
```

---

## API ENDPOINTS

### Manager Actions

```
POST   /console/sharing/create/
       Create new share package

GET    /console/sharing/<id>/edit/
       Editable form (within 1 hour of creation)

GET    /console/sharing/<id>/
       View package details and recipient status

GET    /console/sharing/
       List all packages (with filters, search)

POST   /console/sharing/<id>/revoke/
       Revoke package from all recipients

POST   /console/sharing/<id>/pin/
       Pin/highlight for recipients

GET    /console/sharing/<id>/analytics/
       Detailed engagement analytics

POST   /api/v1/sharing/
       Create share via REST API (for automation)

GET    /api/v1/sharing/<id>/analytics/
       JSON analytics for dashboards
```

### User Actions

```
GET    /dashboard/shares/
       List all received packages (paginated, filtered)

GET    /dashboard/shares/<id>/
       View package details with items

POST   /dashboard/shares/<id>/acknowledge/
       Mark as acknowledged (if required)

POST   /dashboard/shares/<id>/forward/
       Forward to colleagues (if allowed)

GET    /dashboard/shares/search/
       Full-text search packages
```

### Notification Integration

When a package is shared, creates UserNotification:

```python
UserNotification.objects.create(
    user=recipient,
    title="New content shared with you",
    message=package.title,
    url=f'/dashboard/shares/{package.id}/',
    priority=package.importance or 'routine',
)
```

---

## IMPLEMENTATION PHASES

### Phase 1: MVP (2-3 weeks)
**Core sharing functionality**
- Models: ContentSharePackage, ContentShareItem, ExplicitRecipient
- Django admin interface
- Simple manager console (create share form)
- User dashboard (list received packages)
- Notification integration
- Basic analytics (counts)

**Value**: Users can immediately start sharing content to colleagues

---

### Phase 2: Enhanced UI & Analytics (2 weeks)
**Better UX and visibility**
- Advanced dashboard (search, filter, sort)
- ContentShareEvent model for detailed tracking
- Analytics view with timelines, heatmaps
- Acknowledgement workflows
- Pin/highlight feature
- Revoke functionality

**Value**: Managers can see what's working, make data-driven decisions

---

### Phase 3: Advanced Distribution (2-3 weeks)
**Enable ecosystem sharing**
- Forward/redistribute permissions
- Nested sharing tree (track original source)
- Bulk share actions
- Scheduled sharing
- Recurring shares (weekly digest)

**Value**: Viral adoption, peer-to-peer knowledge sharing

---

### Phase 4: Smart Targeting (3-4 weeks)
**Reduce manual work**
- Response-based sharing (answer question → auto-send content)
- Recommendation engine (suggest recipients)
- A/B testing (version comparison)
- Automated reports
- Webhook integration for third-party systems

**Value**: Proactive, efficient content distribution

---

### Phase 5: Enterprise Features (2-3 weeks)
**Compliance and governance**
- Sharing templates (reusable configs)
- Approval workflows
- Immutable audit trail
- Compliance reports
- Rate limiting
- Banned recipient lists

**Value**: Enterprise-grade trust and governance

---

## KEY DESIGN DECISIONS

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| GenericForeignKey for items | Supports all content types, extensible | Slightly complex queries |
| Separate from ContentTrail | Shares are ad-hoc, time-bound; trails are long-term curriculum | Some logic duplication |
| Both audience + explicit recipients | Bulk targeting + one-offs | More complex permission logic |
| Soft delete / expiration | Preserve audit trail, allow recovery | Database rows accumulate |
| Event-based not change-based | Better audit, separate concerns | More table rows |
| 1-hour edit grace period | Catch mistakes before wide spread | Users must create new version to edit |
| No forwarding in MVP | Simplify initial release | May miss viral adoption |

---

## SECURITY CONSIDERATIONS

1. **XSS in descriptions**: Use bleach/Django escape
2. **CSRF**: Django csrf_token in forms, JWT for API
3. **Unauthorized shares**: Permission checks in views, filtered querysets
4. **Event tampering**: No update endpoint on events (immutable)
5. **Recipient enumeration**: Aggregate counts only, no user lists without permission
6. **Rate limiting**: 100 shares/hour per user
7. **Sensitive content**: Add sensitivity tag, audit all access
8. **File uploads**: Don't allow in descriptions, only reference existing files

---

## SCALABILITY NOTES

| Scenario | Solution |
|----------|----------|
| 1000 shares/day | Batch notification creation via Celery |
| 100k recipients per share | Use audience_policy, not explicit recipients; bulk_create() |
| Millions of events | Time-series DB or archival job for old events |
| Real-time dashboards | WebSocket updates via Django Channels |
| Full-text search (1M packages) | PostgreSQL FTS or integrate Elasticsearch |

---

## DATABASE INDEXING

```python
# ContentSharePackage
Index(fields=('organization', 'shared_at'))
Index(fields=('organization', 'is_pinned', '-shared_at'))
Index(fields=('created_by', 'created_at'))

# ExplicitRecipient
Index(fields=('recipient_user', '-invited_at'))
Index(fields=('package', 'recipient_user'))

# ContentShareEvent
Index(fields=('package', 'recipient', 'occurred_at'))
Index(fields=('recipient', 'event_type', 'occurred_at'))
Index(fields=('package', 'event_type', 'occurred_at'))
```

---

## COMPETITOR FEATURES TO CONSIDER

**From Slack, Teams, LinkedIn Learning:**

1. **Thread continuity** - Replies/comments on shared content
2. **Rich previews** - Hover to see thumbnails + metadata
3. **Smart scheduling** - Send at optimal time for recipient
4. **Trending/Popular** - What's being shared most in your team
5. **Read receipts** - Real-time "who opened" indicator
6. **User collections** - Non-managers can curate personal packages
7. **Reactions/Voting** - Users upvote useful shares
8. **Smart search** - NLP-powered full-text search
9. **Auto-expire** - Package disappears after all items viewed
10. **Mention/Tag** - "@john you need to see this"

---

## CRITICAL FILES TO CREATE

1. `sharing/models.py` - Core models (ContentSharePackage, ContentShareItem, ExplicitRecipient, ContentShareEvent)
2. `sharing/views.py` - Manager dashboard, API endpoints
3. `sharing/permissions.py` - Permission checks
4. `sharing/admin.py` - Django admin interface
5. `sharing/templates/sharing/` - Manager console templates
6. `sharing/migrations/` - Database migrations
7. `console/views.py` (extend) - Share management UI
8. `home/views.py` (extend) - User dashboard for received packages
9. `home/templates/home/shares/` - Dashboard templates

---

## TESTING STRATEGY

```python
# Unit tests
test_create_package_requires_permission()
test_explicit_recipient_added()
test_audience_policy_resolved()
test_event_recorded_on_open()
test_acknowledgement_recorded()
test_expiration_soft_deletes()

# Integration tests
test_share_to_individual_sends_notification()
test_share_to_audience_resolves_members()
test_analytics_query_performance()

# E2E tests
test_manager_creates_share_sees_analytics()
test_user_receives_notification_opens_content()
test_forward_chain_tracks_original()

# Performance tests
test_share_to_100k_users_completes_in_5s()
test_analytics_queries_sub_500ms()
```

---

## DEPLOYMENT CHECKLIST

- [ ] Database migrations tested on staging
- [ ] Feature flag created (sharing.enabled)
- [ ] Permission groups configured
- [ ] Email templates created
- [ ] Dashboard UI components built
- [ ] API documentation written
- [ ] Admin console forms ready
- [ ] Logging configured for audit trail
- [ ] Monitoring alerts set
- [ ] Docs updated with admin guide
- [ ] Beta testers identified (5-10 managers)
- [ ] Rollback plan documented
- [ ] Performance tested with realistic load

---

## NEXT STEPS

1. **Review this design** with stakeholders
2. **Identify Phase 1 scope** - What's absolutely necessary?
3. **Create Django app** - `python manage.py startapp sharing`
4. **Begin implementation** starting with Phase 1
5. **Set up tests** as you go (TDD approach)
6. **Beta test** with real managers before full launch

---

## Document Version

- **Created**: 2026-07-26
- **Status**: Ready for Implementation Planning
- **Next Review**: After Phase 1 MVP completion
- **Owner**: Architecture & Product Team
