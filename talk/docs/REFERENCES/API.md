# 🔌 REST API Reference

**For:** Backend developers, frontend developers, API consumers  
**Base URL:** `https://talk.io/api/v1`  
**Version:** 1.0

---

## Authentication

All requests require authentication via session cookie or bearer token.

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response: 200 OK
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "student"
  }
}
```

### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer {token}

Response: 200 OK
{
  "message": "Logged out successfully"
}
```

---

## Users API

### List Users (Admin only)

```http
GET /api/v1/users/?organization_id=1&role=student&limit=20&offset=0
Authorization: Bearer {token}

Response: 200 OK
{
  "count": 150,
  "next": "/api/v1/users/?limit=20&offset=20",
  "results": [
    {
      "id": 1,
      "email": "student@example.com",
      "full_name": "Jane Smith",
      "avatar_url": "https://...",
      "organization_id": 1,
      "role": "student",
      "joined_at": "2026-07-01T10:00:00Z"
    }
  ]
}
```

### Get User Profile

```http
GET /api/v1/users/{user_id}/
Authorization: Bearer {token}

Response: 200 OK
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "avatar_url": "https://...",
  "phone": "+1-555-0100",
  "memberships": [
    {
      "organization_id": 1,
      "organization_name": "Acme Corp",
      "role": "student",
      "is_primary": true
    }
  ]
}
```

### Update User Profile

```http
PATCH /api/v1/users/me/
Authorization: Bearer {token}
Content-Type: application/json

{
  "full_name": "John Smith",
  "phone": "+1-555-0200"
}

Response: 200 OK
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Smith",
  "phone": "+1-555-0200"
}
```

---

## Courses API

### List Courses

```http
GET /api/v1/courses/?organization_id=1&is_published=true&limit=20
Authorization: Bearer {token}

Response: 200 OK
{
  "count": 42,
  "results": [
    {
      "id": 1,
      "title": "Patient Safety 101",
      "description": "Learn patient safety protocols...",
      "banner_url": "https://...",
      "category": "safety",
      "module_count": 5,
      "is_published": true,
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

### Get Course Details

```http
GET /api/v1/courses/{course_id}/
Authorization: Bearer {token}

Response: 200 OK
{
  "id": 1,
  "title": "Patient Safety 101",
  "description": "Complete course description...",
  "banner_url": "https://...",
  "category": "safety",
  "modules": [
    {
      "id": 10,
      "title": "Module 1: Basics",
      "order": 1,
      "contents": [
        {
          "id": 100,
          "type": "text",
          "title": "Introduction",
          "order": 1
        }
      ]
    }
  ],
  "enrollment_count": 234,
  "is_published": true
}
```

### Create Course

```http
POST /api/v1/courses/
Authorization: Bearer {token}
Content-Type: application/json

{
  "organization_id": 1,
  "title": "New Course",
  "description": "Course description...",
  "category": "safety"
}

Response: 201 Created
{
  "id": 99,
  "title": "New Course",
  "description": "Course description...",
  "is_published": false,
  "created_at": "2026-07-27T10:00:00Z"
}
```

---

## Enrollment API

### Enroll in Course

```http
POST /api/v1/courses/{course_id}/enroll/
Authorization: Bearer {token}

Response: 200 OK
{
  "enrollment_id": 50,
  "course_id": 1,
  "user_id": 5,
  "status": "enrolled",
  "enrolled_at": "2026-07-27T10:00:00Z"
}
```

### List My Enrollments

```http
GET /api/v1/users/me/enrollments/?limit=20
Authorization: Bearer {token}

Response: 200 OK
{
  "results": [
    {
      "id": 50,
      "course_id": 1,
      "course_title": "Patient Safety 101",
      "status": "in_progress",
      "progress_percent": 45,
      "enrolled_at": "2026-07-01T10:00:00Z"
    }
  ]
}
```

---

## Quiz API

### Get Quiz

```http
GET /api/v1/quizzes/{quiz_id}/
Authorization: Bearer {token}

Response: 200 OK
{
  "id": 20,
  "title": "Safety Quiz",
  "description": "Test your knowledge...",
  "min_score": 70,
  "time_limit_minutes": 30,
  "question_count": 10,
  "questions": [
    {
      "id": 1,
      "type": "multiple_choice",
      "text": "What is patient safety?",
      "order": 1,
      "answers": [
        {
          "id": 1,
          "text": "Answer A",
          "order": 1
        }
      ]
    }
  ]
}
```

### Submit Quiz

```http
POST /api/v1/quizzes/{quiz_id}/submit/
Authorization: Bearer {token}
Content-Type: application/json

{
  "responses": [
    {
      "question_id": 1,
      "selected_answer_id": 2
    },
    {
      "question_id": 2,
      "text_answer": "Short answer text"
    }
  ]
}

Response: 200 OK
{
  "attempt_id": 100,
  "quiz_id": 20,
  "score": 85,
  "passed": true,
  "correct_count": 8,
  "total_questions": 10,
  "time_minutes": 22,
  "feedback": "Excellent work!"
}
```

### Get Quiz Attempts

```http
GET /api/v1/users/me/quiz-attempts/?quiz_id=20
Authorization: Bearer {token}

Response: 200 OK
{
  "results": [
    {
      "id": 100,
      "quiz_id": 20,
      "score": 85,
      "passed": true,
      "attempt_number": 1,
      "completed_at": "2026-07-27T10:00:00Z"
    }
  ]
}
```

---

## Progress API

### Get Module Progress

```http
GET /api/v1/modules/{module_id}/progress/
Authorization: Bearer {token}

Response: 200 OK
{
  "user_id": 5,
  "module_id": 10,
  "progress_percent": 67,
  "status": "in_progress",
  "contents": [
    {
      "id": 100,
      "type": "text",
      "title": "Introduction",
      "status": "completed"
    },
    {
      "id": 101,
      "type": "video",
      "title": "Tutorial",
      "status": "in_progress",
      "watched_percent": 45
    },
    {
      "id": 102,
      "type": "quiz",
      "title": "Quiz",
      "status": "not_started"
    }
  ]
}
```

### Record Content Progress

```http
POST /api/v1/contents/{content_id}/progress/
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "video",
  "progress_percent": 95,
  "time_minutes": 15
}

Response: 200 OK
{
  "content_id": 101,
  "progress_percent": 95,
  "completed": true,
  "message": "Content marked as complete"
}
```

---

## Analytics API

### Get Enrollment Stats (Manager only)

```http
GET /api/v1/courses/{course_id}/analytics/enrollments/?organization_id=1
Authorization: Bearer {token}

Response: 200 OK
{
  "course_id": 1,
  "total_enrolled": 150,
  "completed": 120,
  "completion_rate": 80.0,
  "in_progress": 25,
  "not_started": 5,
  "avg_time_minutes": 245
}
```

### Get User Progress Report (Manager only)

```http
GET /api/v1/users/{user_id}/progress-report/?organization_id=1
Authorization: Bearer {token}

Response: 200 OK
{
  "user_id": 5,
  "user_email": "student@example.com",
  "courses": [
    {
      "course_id": 1,
      "course_title": "Patient Safety 101",
      "progress_percent": 100,
      "status": "completed",
      "completed_at": "2026-07-27T10:00:00Z",
      "certificate_url": "https://..."
    }
  ]
}
```

---

## Error Handling

### Error Response Format

```http
Response: 400 Bad Request
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "email": ["Invalid email format"],
      "password": ["Password too short"]
    }
  }
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful request |
| 201 | Created | Resource created |
| 204 | No Content | Delete successful |
| 400 | Bad Request | Invalid data |
| 401 | Unauthorized | Authentication failed |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal error |

---

## Rate Limiting

### Limits

```
Authenticated users: 100 requests/minute
Public endpoints: 20 requests/minute per IP
Burst allowed: Up to 10 requests/second
```

### Response Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1690425600
```

### When Limit Exceeded

```http
Response: 429 Too Many Requests
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "You have exceeded the rate limit",
    "retry_after": 30
  }
}
```

---

## Pagination

### Query Parameters

```http
GET /api/v1/courses/?limit=20&offset=0

limit: Items per page (default: 20, max: 100)
offset: Starting position (default: 0)
```

### Response Format

```json
{
  "count": 150,
  "next": "/api/v1/courses/?limit=20&offset=20",
  "previous": null,
  "results": [...]
}
```

---

## Filtering

### Query Examples

```http
# Filter by status
GET /api/v1/courses/?is_published=true

# Filter by date range
GET /api/v1/enrollments/?created_after=2026-01-01&created_before=2026-12-31

# Filter by multiple fields
GET /api/v1/quizzes/?organization_id=1&min_score=70
```

---

## Webhook Events (Future)

```
Planned events:
- course.published
- enrollment.completed
- quiz.submitted
- certificate.issued
- user.created
```

---

## API Changelog

### v1.0 (Current)
- Initial API release
- Authentication, users, courses, quizzes, progress

### v1.1 (Planned)
- Content sharing endpoints
- Advanced analytics
- Batch operations

### v2.0 (Planned)
- GraphQL support
- Webhooks
- OAuth 2.0

---

## Example: Complete Quiz Flow

```python
# 1. Login
POST /api/v1/auth/login
→ Get token

# 2. Get course
GET /api/v1/courses/1/
→ Get modules and content

# 3. Enroll in course
POST /api/v1/courses/1/enroll/

# 4. Get quiz
GET /api/v1/quizzes/20/
→ Get questions

# 5. Submit quiz
POST /api/v1/quizzes/20/submit/
→ Get score

# 6. View certificate (if passed)
GET /api/v1/users/me/certificates/
```

---

**Related:** `ARCHITECTURE.md`, `DATABASE.md`, `/docs/GUIDES/`
