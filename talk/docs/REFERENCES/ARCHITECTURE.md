# 🏗️ System Architecture

**For:** Architects, Senior Developers  
**Level:** Advanced

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Talk Learning Platform               │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐         ┌──────────────┐              │
│  │  Student     │         │   Manager    │              │
│  │  Portal      │         │   Console    │              │
│  │  (Public)    │         │  (Auth)      │              │
│  └──────┬───────┘         └──────┬───────┘              │
│         │                        │                      │
│         └────────────┬───────────┘                      │
│                      │                                  │
│              ┌───────▼────────┐                         │
│              │  Django App    │                         │
│              │  (Port 8000)   │                         │
│              └───────┬────────┘                         │
│                      │                                  │
│         ┌────────────┼────────────┐                     │
│         │            │            │                    │
│    ┌────▼──┐   ┌────▼──┐   ┌────▼───┐                 │
│    │ Users │   │Courses│   │ Quiz   │                 │
│    │ Auth  │   │ Mods  │   │ Track  │                 │
│    └───────┘   └───────┘   └────────┘                 │
│         │            │            │                    │
│         └────────────┼────────────┘                     │
│                      │                                  │
│              ┌───────▼────────┐                         │
│              │  PostgreSQL    │                         │
│              │  Database      │                         │
│              └────────────────┘                         │
│                                                           │
│  ┌──────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ AWS S3       │  │ Email Svc   │  │ Cache (Redis)   │
│  │ (Videos)     │  │ (Notifications)  │ (Sessions)  │
│  └──────────────┘  └─────────────┘  └─────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Frontend (Django Templates + Tailwind)

**Student Portal:**
- Course browser
- Quiz player
- Progress tracking
- Certificate view

**Manager Console:**
- Course CRUD
- Module management
- User management
- Analytics dashboard

**Technologies:**
- Django templates (server-rendered)
- Tailwind CSS (styling)
- Flowbite components (pre-built)
- Vanilla JavaScript (minimal)

### 2. Backend (Django REST)

**Core Apps:**
- `accounts` - User authentication & profiles
- `courses` - Course/module/content models
- `console` - Manager UI & API
- `students` - Student portal & quiz taking
- `learning` - Progress tracking & completion
- `configuration` - Organization & permissions
- `publishing` - Content publishing workflow

**Key Features:**
- Multi-tenant (organization-based)
- RBAC (role-based access control)
- Session-based authentication
- Organization context middleware

### 3. Database (PostgreSQL)

**Main Tables:**
```
accounts_user ..................... User profiles
accounts_organization ............. Multi-tenant orgs
accounts_membership ............... User-org relationships

courses_course .................... Course definitions
courses_module .................... Course modules
courses_content ................... Content (text/video/file)
courses_quiz ...................... Quiz definitions
courses_question .................. Quiz questions
courses_answer .................... Quiz answers

learning_progress ................. Student progress
learning_modulecompletion ......... Completion tracking
learning_audit .................... Audit trail

publishing_* ....................... Publishing workflow
configuration_* ................... Settings & permissions
```

### 4. External Services

**AWS S3:**
- Video storage
- File attachments
- Certificate PDFs
- Backups

**Email Service:**
- User invitations
- Password resets
- Course notifications
- Certificate delivery

**Cache (Redis):**
- Session storage
- Rate limiting
- Query cache (future)

---

## Data Flow

### User Registration Flow

```
1. User visits portal
   ↓
2. Click "Sign Up"
   ↓
3. Enter email + password
   ↓
4. Django creates User + Organization (multi-tenant)
   ↓
5. Email verification sent
   ↓
6. User clicks email link
   ↓
7. Account activated → Login
```

### Course Enrollment Flow

```
1. Student browses courses
   ↓
2. Click "Enroll"
   ↓
3. Django creates Enrollment record
   ↓
4. Redirect to course player
   ↓
5. JavaScript starts progress tracking
   ↓
6. Content loads (text/video/quiz)
```

### Completion Tracking Flow

```
1. Student completes content
   ↓
2. JavaScript sends completion event
   ↓
3. Django records ModuleCompletion
   ↓
4. Calculates overall progress %
   ↓
5. If 100%: Generate certificate
   ↓
6. Send email with certificate PDF
```

---

## Security Architecture

### Authentication
- Email/password (salted + hashed)
- Session-based (Django sessions)
- Optional: 2FA (future)
- Password reset via email

### Authorization
- Role-based (RBAC): Admin, Manager, Student
- Organization-level filtering (multi-tenant)
- Content access validation
- API permission checks

### Data Protection
- HTTPS only (TLS 1.2+)
- CSRF tokens on all forms
- SQL injection prevention (Django ORM)
- XSS protection (template escaping)
- Rate limiting on APIs

### Compliance
- LGPD: Data retention, right-to-delete
- HIPAA: Audit logging, access controls
- GDPR: Data export, consent tracking

---

## Performance Optimization

### Caching Strategy
```
├─ HTTP Cache (browser): Static assets
├─ Query Cache (Redis): Database queries
├─ Session Cache (Redis): User sessions
└─ Full Page Cache (nginx): Public pages
```

### Database Optimization
- Indexing on frequently queried fields
- Partitioning for large tables (future)
- Query optimization (select_related, prefetch_related)
- Database connection pooling

### Frontend Optimization
- Lazy loading (images, videos)
- Code splitting (separate JS bundles)
- Minification (CSS, JS)
- CDN for static files (future)

---

## Scalability

### Horizontal Scaling
```
Load Balancer (ALB)
    ↓
Multiple Django instances (Auto-scaling)
    ↓
PostgreSQL read replicas
    ↓
Redis cluster
```

### Vertical Scaling
- Increase instance size (CPU, RAM)
- Optimize queries
- Add caching layers

### Future Improvements
- Microservices (separate services per domain)
- GraphQL (flexible queries)
- Message queues (async tasks)
- CDN (video distribution)

---

## Deployment Architecture

```
GitHub Repo (Source)
    ↓
CI/CD Pipeline (GitHub Actions)
    ↓
Docker Image Build
    ↓
Push to ECR (AWS)
    ↓
Blue-Green Deployment
    ├─ Blue (old) - Active
    └─ Green (new) - Testing
    ↓
Load Balancer Switch
    ↓
Production (AWS EC2)
    ├─ App servers (2-3)
    ├─ PostgreSQL RDS
    ├─ S3 storage
    └─ CloudFront CDN
```

---

## Monitoring & Observability

```
Application
    ↓
├─ Error tracking (Sentry)
├─ Performance monitoring (Datadog)
├─ Log aggregation (ELK/CloudWatch)
└─ APM (Application Performance Monitoring)
    ↓
Dashboards (Grafana/Datadog)
    ↓
Alerts (Slack, PagerDuty)
```

---

## API Architecture

### REST API Structure
```
/api/
├── /v1/
│   ├── /auth/ (login, logout, password reset)
│   ├── /users/ (CRUD)
│   ├── /courses/ (CRUD + enroll)
│   ├── /modules/ (CRUD)
│   ├── /quizzes/ (CRUD + submit)
│   └── /progress/ (tracking)
└── /v2/ (future)
```

### Authentication
```
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password"
}
→ Response: {"access_token": "...", "user": {...}}
```

### Rate Limiting
- 100 requests/minute per user (authenticated)
- 20 requests/minute per IP (public)
- Returns 429 when exceeded

---

## Error Handling

### Error Codes
```
200 OK - Success
201 Created - Resource created
400 Bad Request - Invalid input
401 Unauthorized - Authentication required
403 Forbidden - Permission denied
404 Not Found - Resource not found
429 Too Many Requests - Rate limit
500 Internal Server Error - Server error
```

### Logging
```
All errors logged with:
- Timestamp
- User ID
- Request path
- Error message
- Stack trace (dev only)
```

---

## Testing Strategy

### Unit Tests
- Models (save, validation)
- Serializers (data transformation)
- Utilities (helpers)

### Integration Tests
- API endpoints (request/response)
- Database transactions
- Authentication flows

### E2E Tests
- User journeys (signup → course → quiz)
- Cross-browser (Chrome, Firefox, Safari)
- Mobile (iOS, Android)

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend** | Django | 4.2+ |
| **Language** | Python | 3.12+ |
| **Database** | PostgreSQL | 13+ |
| **Cache** | Redis | 6.0+ |
| **Frontend** | Django Templates | 4.2 |
| **CSS** | Tailwind CSS | 3.x |
| **Components** | Flowbite | 1.x |
| **Deployment** | Docker | 20.10+ |
| **Cloud** | AWS (EC2, RDS, S3) | - |
| **CI/CD** | GitHub Actions | - |

---

## Development Workflow

```
Feature Branch → Unit Tests → Integration Tests 
    → Code Review → E2E Tests → Merge → Deploy
```

See `/docs/GUIDES/02_DEVELOPMENT_WORKFLOW.md` for details.

---

**Related:** `DATABASE.md`, `API.md`, `/docs/GUIDES/`
