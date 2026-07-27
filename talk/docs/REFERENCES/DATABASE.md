# 🗄️ Database Schema

**For:** Backend developers, DBAs  
**Level:** Advanced

---

## Overview

Talk uses **PostgreSQL 13+** with Django ORM.

**Key Principles:**
- Multi-tenant (organization isolation)
- RBAC (role-based access)
- Audit trail (all changes logged)
- Data integrity (constraints, indexes)

---

## Core Models

### User Management

```python
# accounts/models.py

class User(AbstractUser):
    """User account - global across all orgs"""
    email           # Unique email
    phone           # Optional phone
    full_name       # First + last name
    avatar_url      # Profile picture
    is_active       # Soft delete flag
    created_at      # Account creation
    updated_at      # Last update
    
    # Related
    memberships     # FK → Membership
    courses_created # FK → Course
    
    Indexes: email, created_at

class Organization(models.Model):
    """Multi-tenant organization"""
    name            # Company name
    slug            # URL-friendly name
    logo_url        # Company logo
    domain          # Custom domain (optional)
    settings        # JSONField (branding, etc)
    is_active       # Soft delete
    created_at      # Creation date
    
    # Related
    users           # M2M → User via Membership
    courses         # FK → Course
    
    Indexes: slug, domain

class Membership(models.Model):
    """User-Org relationship"""
    user            # FK → User
    organization    # FK → Organization
    role            # Choice: admin, manager, student
    is_primary      # Primary org for user
    joined_at       # Join date
    
    Unique: (user, organization)
    Indexes: user, organization, role
```

### Course Management

```python
# courses/models.py

class Course(models.Model):
    """Course definition"""
    organization    # FK → Organization (multi-tenant)
    title           # Course title
    description     # Course description
    banner_url      # Course banner image
    category        # Course category
    is_published    # Published status
    created_at      # Creation date
    updated_at      # Last update
    
    # Related
    modules         # Reverse FK → Module
    enrollments     # Reverse FK → Enrollment
    
    Indexes: organization, is_published, created_at

class Module(models.Model):
    """Course module"""
    course          # FK → Course
    title           # Module title
    description     # Module description
    order           # Module sequence (1, 2, 3...)
    is_published    # Published status
    
    # Related
    contents        # Reverse FK → Content
    
    Indexes: course, order

class Content(models.Model):
    """Course content (text, video, file)"""
    module          # FK → Module
    content_type    # Choice: text, video, file, quiz
    title           # Content title
    description     # Content description
    order           # Content sequence
    
    # Type-specific fields
    text_content    # For content_type='text'
    video_url       # For content_type='video'
    file_url        # For content_type='file'
    file_size       # File size in bytes
    
    # Metadata
    duration_minutes # For video
    created_at
    updated_at
    
    Indexes: module, content_type

class Quiz(models.Model):
    """Quiz definition"""
    organization    # FK → Organization
    title           # Quiz title
    description     # Quiz description
    min_score       # Passing score (0-100)
    attempts_allowed # Max attempts (-1 = unlimited)
    time_limit_minutes # Max time per attempt
    created_at
    updated_at
    
    # Related
    questions       # Reverse FK → Question
    
    Indexes: organization, created_at

class Question(models.Model):
    """Quiz question"""
    quiz            # FK → Quiz
    question_type   # Choice: multiple_choice, true_false, short_answer, multiple_correct
    text            # Question text
    order           # Question sequence
    
    # Related
    answers         # Reverse FK → Answer
    
    Indexes: quiz, order

class Answer(models.Model):
    """Quiz answer option"""
    question        # FK → Question
    text            # Answer text
    is_correct      # Correct answer flag
    order           # Answer sequence
    
    Indexes: question, order
```

### Learning & Progress

```python
# learning/models.py

class Enrollment(models.Model):
    """Course enrollment"""
    user            # FK → User
    course          # FK → Course
    organization    # FK → Organization (denormalized for query speed)
    enrolled_at     # Enrollment date
    completed_at    # Completion date (null if incomplete)
    status          # Choice: enrolled, in_progress, completed, expired
    
    Indexes: user, course, organization, status
    Unique: (user, course)

class ModuleProgress(models.Model):
    """Student progress in a module"""
    user            # FK → User
    module          # FK → Module
    organization    # FK → Organization (denormalized)
    
    # Progress tracking
    progress_percent # 0-100%
    status          # Choice: not_started, in_progress, completed
    
    # Content-specific tracking
    text_scrolled_percent    # 0-100%
    video_watched_percent    # 0-100%
    quiz_passed              # Boolean
    
    # Time tracking
    started_at      # When student started
    completed_at    # When student completed
    time_spent_seconds # Total time spent
    last_accessed_at # Last access time
    
    Indexes: user, module, organization
    Unique: (user, module)

class QuizAttempt(models.Model):
    """Student quiz attempt"""
    user            # FK → User
    quiz            # FK → Quiz
    organization    # FK → Organization
    
    # Attempt data
    started_at      # When started
    completed_at    # When completed
    score           # Final score (0-100)
    passed          # Boolean (score >= min_score)
    time_minutes    # Time spent
    attempt_number  # Attempt #1, #2, etc
    
    # Related
    responses       # Reverse FK → QuizResponse
    
    Indexes: user, quiz, passed, created_at

class QuizResponse(models.Model):
    """Student's answer to a question"""
    attempt         # FK → QuizAttempt
    question        # FK → Question
    
    # Answer data
    selected_answer # FK → Answer (for multiple choice)
    text_answer     # Text answer (for short answer)
    is_correct      # Whether correct
    
    Indexes: attempt, question
```

### Audit & Compliance

```python
# learning/models.py

class AuditLog(models.Model):
    """Immutable audit trail"""
    user            # FK → User
    organization    # FK → Organization
    action          # Choice: quiz_started, quiz_submitted, video_watched, text_read, cert_issued
    resource_type   # quiz, course, module, etc
    resource_id     # ID of resource
    
    # Details
    details         # JSONField (context-specific data)
    ip_address      # User IP
    user_agent      # Browser/device info
    
    # Metadata
    timestamp       # When action occurred
    
    Indexes: user, action, timestamp
    Note: IMMUTABLE (no updates/deletes)

class Certificate(models.Model):
    """Course completion certificate"""
    user            # FK → User
    course          # FK → Course
    organization    # FK → Organization
    
    # Certificate data
    issued_at       # Issue date
    valid_until     # Expiration date (optional)
    certificate_number # Unique cert number
    pdf_file        # PDF file path (S3)
    
    # Status
    status          # Choice: valid, expired, revoked
    revoked_at      # When revoked (if any)
    
    Indexes: user, course, organization, status
    Unique: (user, course)
```

### Configuration & Permissions

```python
# configuration/models.py

class Role(models.Model):
    """Custom role definitions"""
    organization    # FK → Organization
    name            # Role name (Manager, Instructor, etc)
    permissions     # JSONField (list of permission names)
    
    Indexes: organization

class Permission(models.Model):
    """Application permissions"""
    code            # Permission code (e.g., 'course.create')
    name            # Human-readable name
    description     # Permission description
```

---

## Relationships Diagram

```
User
├── Memberships (M2M) → Organization
├── Enrollments → Course
├── ModuleProgress → Module
├── QuizAttempts → Quiz
└── AuditLogs

Organization
├── Users (via Membership)
├── Courses
├── Quizzes
├── Roles
└── AuditLogs

Course
├── Modules
├── Enrollments
└── Quizzes (separate)

Module
├── Contents (text, video, file)
└── ModuleProgress

Quiz
├── Questions
└── QuizAttempts

Question
└── Answers
```

---

## Indexes Strategy

### High-Priority (Query Performance)

```python
# accounts/models.py
class User:
    indexes = [
        ('email',),  # Login queries
        ('created_at',),  # Dashboard filters
    ]

# courses/models.py
class Enrollment:
    indexes = [
        ('user', 'course'),  # User's courses
        ('organization', 'status'),  # Org dashboards
        ('completed_at',),  # Recent completions
    ]

class ModuleProgress:
    indexes = [
        ('user', 'module'),  # User's progress
        ('organization', 'status'),  # Org analytics
        ('last_accessed_at',),  # Recent activity
    ]

class QuizAttempt:
    indexes = [
        ('user', 'quiz'),  # User's attempts
        ('passed',),  # Filter passed/failed
        ('completed_at',),  # Recent attempts
    ]
```

---

## Constraints

### Unique Constraints

```python
Membership:      (user, organization)
Enrollment:      (user, course)
ModuleProgress:  (user, module)
Certificate:     (user, course)
```

### Foreign Key Constraints

```python
ON DELETE CASCADE:
- Module → Course (delete course → delete modules)
- Content → Module (delete module → delete content)
- Question → Quiz (delete quiz → delete questions)

ON DELETE PROTECT:
- Enrollment → User/Course (prevent accidental deletion)
- AuditLog → User (preserve audit trail)
```

---

## Data Migration Strategy

### Adding a Column

```python
# Step 1: Add column (nullable)
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='moduleProgress',
            name='video_watched_percent',
            field=models.IntegerField(default=0),
        ),
    ]

# Step 2: Backfill data
# Step 3: Make NOT NULL
class Migration(migrations.Migration):
    operations = [
        migrations.AlterField(
            model_name='moduleProgress',
            name='video_watched_percent',
            field=models.IntegerField(),
        ),
    ]
```

### Renaming a Column

```python
# Use RenameField migration
class Migration(migrations.Migration):
    operations = [
        migrations.RenameField(
            model_name='course',
            old_name='description_html',
            new_name='description',
        ),
    ]
```

---

## Backup & Recovery

### Backup Strategy

```bash
# Daily backup to S3
pg_dump -U user talk > backup_$(date +%Y%m%d).sql
aws s3 cp backup_*.sql s3://talk-backups/

# Keep 30-day rolling window
```

### Recovery

```bash
# Restore from backup
psql -U user talk < backup_20260727.sql

# Verify recovery
psql -U user talk -c "SELECT COUNT(*) FROM accounts_user;"
```

---

## Performance Optimization

### Query Optimization

```python
# ❌ WRONG: N+1 query problem
for enrollment in Enrollment.objects.all():
    print(enrollment.user.email)  # 1 + N queries

# ✅ CORRECT: Use select_related
enrollments = Enrollment.objects.select_related('user')
for enrollment in enrollments:
    print(enrollment.user.email)  # 1 query
```

### Denormalization

```python
# Store organization_id in Enrollment for fast filtering
class Enrollment(models.Model):
    organization = ForeignKey(Organization)  # Denormalized
    # Allows filtering by org without joining Course
```

---

## Monitoring Queries

```bash
# Enable query logging
psql -U user talk
talk=# SELECT * FROM pg_stat_statements 
       ORDER BY mean_time DESC LIMIT 10;

# Explain slow query
EXPLAIN ANALYZE SELECT * FROM courses_enrollment
WHERE user_id = 123;
```

---

**Related:** `ARCHITECTURE.md`, `API.md`, `/docs/GUIDES/02_DEVELOPMENT_WORKFLOW.md`
