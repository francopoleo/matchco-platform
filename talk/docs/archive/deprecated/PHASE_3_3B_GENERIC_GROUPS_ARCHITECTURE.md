# Phase 3.3B: Generic Hierarchical Group System Architecture

**Date:** 2026-07-26  
**Status:** Design Complete → Implementation Starting  
**Scope:** Refactor Phase 3.2 group system to be generic and reusable like company hierarchy  
**Timeline:** 5 weeks (Weeks 1-5 of current sprint)

---

## Core Principle

**All group types (parents, alumni, departments, custom) use identical underlying structure with only labels and configuration changing.** No specialized views, no specialized management commands, no specialized logic per group type.

### Reference Pattern: Company Hierarchy

```
Organization → Company → BusinessUnit → OperationalUnit
│
└─ Labels: OrganizationTerminology (configurable per org)
└─ Management: Django admin inlines only
└─ Scope: Membership stores FKs to all levels
```

### Proposed Pattern: Group Hierarchies

```
Organization → GroupHierarchyType → GroupNode (hierarchical)
│                                      ├─ Level 1 (root)
│                                      ├─ Level 2 (parent: Level 1)
│                                      └─ Level 3 (parent: Level 2)
│
├─ Labels: GroupHierarchyTerminology (like OrganizationTerminology)
├─ Management: Django admin inlines only
├─ Scope: UserGroupMembership stores FK to GroupNode (any level)
└─ Linking: UserGroupMembership.linked_user for relationships (parent→student, manager→report)
```

---

## Entity Models

### 1. GroupHierarchyType
Defines each hierarchy type (parents, alumni, departments) per organization.

```python
class GroupHierarchyType(models.Model):
    organization = ForeignKey(Organization)
    code = SlugField  # 'parents', 'alumni', 'departments'
    name = CharField  # 'Parent-Student Hierarchy'
    description = TextField
    max_levels = IntegerField(default=3)
    allow_links = BooleanField(default=False)  # Can use linked_user field
    auto_create_on = CharField(blank=True)  # 'graduation', 'none', etc.
    active = BooleanField(default=True)
    
    Constraints:
      unique_together = [['organization', 'code']]
```

### 2. GroupHierarchyTerminology
Configurable labels per hierarchy type (one per GroupHierarchyType).

```python
class GroupHierarchyTerminology(models.Model):
    hierarchy_type = OneToOneField(GroupHierarchyType)
    level_1_label = CharField(default='Group Level 1')
    level_1_description = CharField(blank=True)
    level_2_label = CharField(default='Group Level 2')
    level_2_description = CharField(blank=True)
    level_3_label = CharField(default='Group Level 3')
    level_3_description = CharField(blank=True)
```

### 3. GroupNode
Replaces UserGroup. Parent-child hierarchy like Company→BU→OU.

```python
class GroupNode(models.Model):
    hierarchy_type = ForeignKey(GroupHierarchyType)
    parent_node = ForeignKey('self', null=True, blank=True, related_name='children')
    name = CharField(max_length=200)
    code = CharField(max_length=100, blank=True)
    description = TextField(blank=True)
    level = IntegerField()  # Computed from parent chain
    position = PositiveIntegerField(default=0)
    metadata = JSONField(default=dict, blank=True)  # graduation_year, etc.
    active = BooleanField(default=True)
    
    Constraints:
      unique_together = [['hierarchy_type', 'parent_node', 'code']]
    
    Methods:
      get_level()  # Traverse to root to compute level
      get_root()   # Get root node of this hierarchy
      get_ancestors()  # Parents up to root
```

### 4. UserGroupMembership
Replaces GroupMembership. Users linked to group nodes (any level).

```python
class UserGroupMembership(models.Model):
    user = ForeignKey(User)
    group_node = ForeignKey(GroupNode)  # The scope (can be any level)
    role = CharField(choices=[admin, member, viewer])
    status = CharField(choices=[active, pending, inactive])
    linked_user = ForeignKey(User, null=True, blank=True)  # For parent→student
    joined_at = DateTimeField(auto_now_add=True)
    created_by = ForeignKey(User, null=True, blank=True)
    
    Constraints:
      unique_together = [['user', 'group_node', 'linked_user']]
```

### 5. GroupNodeAccess
Replaces GroupAccess. Content permissions per group node.

```python
class GroupNodeAccess(models.Model):
    group_node = ForeignKey(GroupNode)
    content_type = CharField(max_length=50)  # trail, course, publication, organization
    object_id = IntegerField(null=True, blank=True)  # Specific content ID or null for all
    access_level = CharField(max_length=20)  # view, view_progress, download, manage
    created_by = ForeignKey(User, null=True, blank=True)
    
    Constraints:
      unique_together = [['group_node', 'content_type', 'object_id']]
```

---

## Configuration Examples

### Example 1: Parent-Student Hierarchy

**GroupHierarchyType:**
- Code: `parents`
- Name: `Parent-Student Relationship`
- Allow Links: `True`
- Max Levels: `1` (flat)

**GroupHierarchyTerminology:**
- Level 1: `Parents Group`

**Data:**
- Root GroupNode: "Parents of All Students" (level 1, parent=null)
- UserGroupMembership: Maria (parent) → Parents Group, linked_user=João (student)
- GroupNodeAccess: Parents Group → trail (João's assigned trail) → view_progress

**Admin Flow:**
1. Create GroupHierarchyType "parents" with allow_links=True
2. Admin creates root GroupNode "Parents Group"
3. Admin adds UserGroupMembership: Maria → Parents Group, linked_user=João
4. Maria can now see João's progress (via access rules on Parents Group)

**No Code:** No ParentStudentLinkingView, no specialized form.

---

### Example 2: Alumni Hierarchy with Auto-Create

**GroupHierarchyType:**
- Code: `alumni`
- Name: `Alumni by Graduation Year`
- Allow Links: `False`
- Max Levels: `2` (year → subgroup)
- Auto Create On: `graduation`
- Metadata: `{graduation_year_field: 'year'}`

**GroupHierarchyTerminology:**
- Level 1: `Graduation Year`
- Level 2: `Alumni Cohort`

**Data (auto-created on graduation signal):**
- GroupNode Level 1: "2024 Graduates" (level 1, parent=null)
- GroupNode Level 2: "2024 - Remote" (level 2, parent=2024 Graduates)
- UserGroupMembership: Carlos (alumni) → 2024 Graduates, role=viewer
- GroupNodeAccess: 2024 Graduates → trail (past courses) → view

**Admin Flow:**
1. Configure GroupHierarchyType "alumni" with auto_create_on='graduation'
2. When user graduates (signal trigger), auto-create year node and add membership
3. Admins can further organize with Level 2 cohorts if needed

**No Code:** No convert_alumni command, just signal handler.

---

### Example 3: Department Hierarchy (Multi-Level)

**GroupHierarchyType:**
- Code: `departments`
- Name: `Department Organization`
- Max Levels: `3`
- Allow Links: `False`

**GroupHierarchyTerminology:**
- Level 1: `Department`
- Level 2: `Team`
- Level 3: `Subteam`

**Data:**
```
HR Department (L1, parent=null)
  ├─ Recruiting Team (L2, parent=HR)
  │   └─ Senior Recruiting (L3, parent=Recruiting Team)
  └─ Payroll Team (L2, parent=HR)

Sales Department (L1, parent=null)
  └─ Enterprise Sales (L2, parent=Sales)
```

**Memberships:**
- Alice → HR Department, role=admin (manages all HR)
- Bob → Recruiting Team, role=admin (manages recruiting only)
- Charlie → Senior Recruiting, role=member

**Access:** Each node can have its own access rules to content.

**Admin Flow:**
1. Create GroupHierarchyType "departments" with max_levels=3
2. Create Level 1 nodes (HR, Sales)
3. Create Level 2 nodes under each (set parent_node)
4. Create Level 3 nodes as needed
5. Add members via inline forms

**Fully Hierarchical:** No limit to depth, no specialized code.

---

## Migration from Phase 3.2

### Phase 3.2 → 3.3B Mapping

| Phase 3.2 | Phase 3.3B | Notes |
|-----------|-----------|-------|
| UserGroup | GroupHierarchyType + GroupNode (L1) | UserGroup.name → GroupNode.name, UserGroup.slug → parent node |
| GroupMembership | UserGroupMembership | Direct rename, same fields |
| GroupAccess | GroupNodeAccess | Direct rename, same fields |
| ParentStudentLinkingView | Removed | Use admin inline to add memberships |
| AlumniDashboardView | Removed | Use generic dashboard filtering by hierarchy type |
| convert_alumni command | Signal handler | Auto-create via GroupHierarchyType.auto_create_on |

### Data Migration Steps

1. Create GroupHierarchyType for each unique UserGroup.group_type
2. Create root GroupNode for each UserGroup
3. Copy GroupMembership → UserGroupMembership (group_node = root node)
4. Copy GroupAccess → GroupNodeAccess (group_node = root node)
5. Soft-delete old tables (add archived flag)

---

## Admin Interface Design

### Nested Inline Structure

```
GroupHierarchyTypeAdmin
├─ list_view: name, code, organization, active, edit
│
└─ detail_view:
    ├─ [Edit Basic Info] (name, code, description)
    ├─ [Edit Terminology] (inline OneToOne)
    ├─ [Manage Nodes] (inline ForeignKey, filtered by hierarchy_type)
    │   ├─ GroupNode L1 (root nodes, parent__isnull=True)
    │   ├─ GroupNode L2 (children of L1, shown nested if possible)
    │   └─ GroupNode L3 (children of L2)
    │
    └─ GroupNodeAdmin
       ├─ list_view: name, hierarchy, level, parent, position
       │
       └─ detail_view:
           ├─ [Edit Node Info] (name, code, level, metadata)
           ├─ [Manage Members] (inline UserGroupMembership)
           │   └─ Columns: user, linked_user, role, status
           └─ [Manage Access] (inline GroupNodeAccess)
               └─ Columns: content_type, object_id, access_level
```

### Admin Search & Filtering

**GroupHierarchyTypeAdmin:**
- Filter by: organization, active, code
- Search: name, description, code

**GroupNodeAdmin:**
- Filter by: hierarchy_type, level, parent_node, active
- Search: name, code

**UserGroupMembershipAdmin:**
- Filter by: group_node__hierarchy_type, role, status
- Search: user__email, group_node__name

---

## No Specialized Views

❌ **Removed:**
- `console.views.ParentStudentLinkingView`
- `console.views.AlumniDashboardView`
- `learning.management.commands.convert_alumni`
- Related URLs: `/console/groups/parent-student/`, `/console/groups/alumni/`

✅ **Instead:**
1. **Admin creates hierarchies and memberships** via Django admin inlines
2. **Generic dashboards** filter by hierarchy_type and group_node (not specialized per type)
3. **Signal handlers** auto-create groups based on GroupHierarchyType.auto_create_on
4. **ORM queries** handle relationships (no specialized logic needed)

---

## Implementation Timeline

| Week | Tasks | Status |
|------|-------|--------|
| 1 | Create new models + admin + data migration | → Starting now |
| 2 | Testing + parallel run with Phase 3.2 data | → Testing |
| 3 | Remove old views/URLs + content access integration | → Integration |
| 4 | Deprecate Phase 3.2 models + monitor | → Monitoring |
| 5 | Buffer for edge cases + documentation | → Cleanup |

---

## Success Criteria

✅ All group types (parents, alumni, departments, custom) use identical models  
✅ No specialized views or management commands  
✅ Labels and structure configurable via GroupHierarchyTerminology  
✅ Hierarchical organization supported (arbitrary depth)  
✅ User linking (parent→student, manager→direct report) via linked_user FK  
✅ Content access rules per group node (GroupNodeAccess)  
✅ Admin interface allows full CRUD of hierarchies  
✅ Data migrated from Phase 3.2 without loss  
✅ All tests passing (26+ from Phase 3.2, new tests for hierarchies)  
✅ Zero specialized code per group type  

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Parent-Child FK vs Flat Levels** | Parent-child allows arbitrary depth; aligns with company hierarchy pattern |
| **GroupHierarchyType + Terminology** | Separates configuration (terminology) from data (hierarchy), like OrganizationTerminology |
| **UserGroupMembership.group_node** | Points to any level (L1, L2, L3); scope is inherited from node's position |
| **linked_user FK optional** | Generic field; only used when allow_links=True; supports all relationship types |
| **Auto-create via signal** | No specialized commands; metadata + signal handler handle all auto-creation scenarios |
| **No Dashboard Views** | Use generic filters (group_node__hierarchy_type__code='alumni'); admins see all via admin |

---

## Files Modified/Created

### New Files
- `configuration/models.py` → +5 models (GroupHierarchyType, Terminology, GroupNode, UserGroupMembership, GroupNodeAccess)
- `configuration/admin.py` → +5 admin classes + inlines
- `configuration/migrations/0015_*.py` → Data migration from Phase 3.2
- `configuration/signals.py` → Auto-create handlers

### Modified Files
- `console/views.py` → Remove ParentStudentLinkingView, AlumniDashboardView
- `console/urls.py` → Remove `/groups/parent-student/`, `/groups/alumni/` routes
- `learning/management/commands/convert_alumni.py` → Deprecate (replace with signal)
- `home/views.py` → Update content filtering to use GroupNode instead of UserGroup

### Deprecated Files
- `configuration/models.py` → UserGroup, GroupMembership, GroupAccess (soft-delete via archived flag)
- `configuration/tests/test_group_flows.py` → Phase 3.2 tests (replace with generic hierarchy tests)

---

## Next: Implementation Starts Week 1

Move to: [IMPLEMENTATION_WEEK1.md]
