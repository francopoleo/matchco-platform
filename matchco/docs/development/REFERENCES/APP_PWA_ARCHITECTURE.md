# MatchCo PWA App Architecture (/app/)

**Last Updated:** October 3, 2026
**Version:** 1.0.0
**Status:** Production Ready

## Overview

The `/app/` namespace is a complete Progressive Web App (PWA) interface for authenticated users. It provides a responsive, mobile-first experience with full offline support and PWA capabilities.

## URL Structure

All app routes are under the `app:` namespace and require authentication + organization selection.

```
/app/                              Dashboard with stats
/app/profile/                      User profile view
/app/profile/edit/                 Edit profile
/app/settings/                     Account settings & preferences
/app/courses/                      My courses list
/app/courses/<id>/                 Course details
/app/courses/<id>/play/            Video player & lessons
/app/courses/<id>/progress/        Progress tracking
/app/feed/                         News & updates feed
/app/trails/                       Learning paths (trilhas)
/app/wiki/                         Knowledge base (Wiki)
/app/matches/                      User matches/connections
/app/matches/<id>/                 Match detail & chat
/app/recruitment/                  Recruitment dashboard
/app/recruitment/candidates/       Candidate list
/app/recruitment/positions/        Open positions
/app/help/                         Help center
/app/help/<topic>/                 Help topic page
/app/notifications/                Notifications center
```

## Architecture Components

### Views (`matchco/app_views.py`)

**Base Class:**
- `AppBaseView` - Ensures authentication & organization context
  - Checks `selected_organization` in dispatch()
  - Injects organization & user in context
  - Redirects to organization selector if not set

**Main Views:**
1. `AppDashboardView` - Overview with stats
2. `AppProfileView` / `AppProfileEditView` - User profile management
3. `AppSettingsView` - Account settings
4. `AppCoursesView` - Course listing
5. `AppCourseDetailView` - Course information
6. `AppCoursePlayerView` - Video player
7. `AppCourseProgressView` - Learning progress
8. `AppFeedView` - News feed (publications with kind='feed')
9. `AppTrailsView` - Learning paths (TrailAssignment data)
10. `AppWikiView` - Knowledge base (publications with kind='wiki')
11. `AppMatchesView` / `AppMatchDetailView` - User connections
12. `AppRecruitmentView` - Recruitment hub
13. `AppCandidatesView` - Candidate management
14. `AppPositionsView` - Job positions
15. `AppHelpView` / `AppHelpTopicView` - Help system
16. `AppNotificationsView` - Notification center

### URL Configuration (`matchco/app_urls.py`)

- Namespace: `app:`
- All views are class-based (Generic/TemplateView)
- Integrated with Django's auth system

### Templates (`matchco/matchco/templates/app/`)

**Layout:**
- `base.html` - Main app shell with navbar, sidebar, responsive layout

**Feature Templates:**
- `dashboard.html` - Dashboard with KPIs
- `profile/view.html` - Profile display
- `profile/edit.html` - Profile editor
- `settings.html` - Settings & preferences
- `courses/list.html` - Courses grid
- `courses/detail.html` - Course info
- `courses/player.html` - Video player
- `courses/progress.html` - Progress tracker
- `feed.html` - Publication feed
- `trails.html` - Learning paths
- `wiki.html` - Knowledge base articles
- `matches/list.html` - Matches grid
- `matches/detail.html` - Match detail with chat UI
- `recruitment/dashboard.html` - Recruitment overview
- `recruitment/candidates.html` - Candidate table
- `recruitment/positions.html` - Positions list
- `help/index.html` - Help center with 6 categories
- `help/topic.html` - Individual help topic
- `notifications.html` - Notification center

## Navigation

### Sidebar Navigation
Located in `matchco/templates/ui/sidebar.html`, displays 6 main sections:
1. Dashboard
2. Courses
3. Feed
4. Matches
5. Recruitment
6. Help

**Navigation Menu (from `matchco/core/menu.py`):**
- All authenticated users see: Courses, Trails, Feed, Wiki, Matches, Profile, Notifications, Help
- Menu items require authentication and are injected via context processor

### Smart Routing

**SmartHomeView (`cep/views.py`):**
- Anonymous users → `/login/`
- Admin users → `/console/`
- Auth users without org → `/select-organization/`
- Auth users with org → `/app/dashboard/`

## Data Integration

### Publications (Feed & Wiki)
**Source:** `publishing.models.Publication`
- Feed items: `status='published', kind='feed'`
- Wiki articles: `status='published', kind='wiki'`

### Learning Paths (Trails)
**Source:** `students.models.TrailAssignment`
- Filtered by `user=request.user`
- Shows progress, status, objectives

### Courses
**Source:** `courses.models.Course`
- User enrollments tracked
- Progress via quiz/lesson completion

## Responsive Design

**Breakpoints:**
- Mobile: Hidden sidebar, hamburger menu
- Tablet (sm): 640px+
- Desktop (lg): 1024px+

**Key Features:**
- Fixed navbar (z-50) with organization selector
- Fixed sidebar (z-40, 264px wide)
- Mobile backdrop overlay for menu toggle
- Breadcrumb navigation
- Dark mode support with Tailwind CSS
- HTMX integration ready for SPA behavior

## Authentication & Authorization

**Requirements:**
1. User must be authenticated (`LoginRequiredMixin`)
2. Organization must be selected (checked in `AppBaseView.dispatch()`)
3. Session context includes:
   - `selected_organization`
   - `active_organization_id`
   - `user_role`

**Redirects:**
- Missing organization → `/select-organization/`
- Not authenticated → `/login/`

## PWA Features

**Service Worker:** `matchco/core/pwa.py`
- Offline-first caching strategy
- Push notification support

**Manifest:** `cep/static/ui/manifest.webmanifest`
- App name, icons, theme color

**Support:**
- Add to home screen on mobile
- Works offline (cached routes)
- Push notifications ready

## Internationalization (i18n)

All templates use Django's `{% trans %}` tags for translation:
- Portuguese (pt-br) - Default
- English translations prepared
- Template filters: `{% load i18n %}`

## Common Issues & Solutions

### Organization Not Selected
**Error:** Redirects to organization selector
**Solution:** Select organization from dropdown, then return to app

### Menu Items Not Showing
**Cause:** User lacks required permissions
**Solution:** Check `auth=True` requirement in menu items; ensure user is authenticated

### Publication Not Showing in Feed
**Check:**
- `status='published'` (not 'draft' or 'review')
- `kind='feed'` (for feed) or `kind='wiki'` (for wiki)

### Route Not Found
**Check:**
1. URL name is correct: `app:dashboard` (with colon)
2. View is imported in `app_urls.py`
3. Route is registered in `urlpatterns`

## Performance Considerations

1. **Database Queries:** Use `select_related()` and `prefetch_related()`
2. **Caching:** Publication list queries should be cached
3. **Pagination:** Feed should paginate after 10 items
4. **Images:** Use responsive image tags with srcset
5. **Static Files:** Use versioned CSS/JS files

## Future Enhancements

- [ ] Real-time notifications via WebSocket
- [ ] Chat/messaging system for matches
- [ ] Course video streaming optimization
- [ ] Offline content synchronization
- [ ] Mobile app wrapper (Capacitor/Cordova)
- [ ] Analytics integration
- [ ] A/B testing framework

## Development Guidelines

### Adding New Pages
1. Create view in `app_views.py` extending `AppBaseView`
2. Create template in `app/` folder
3. Add route to `app_urls.py`
4. Add menu item in `matchco/core/menu.py` if user-facing
5. Update this documentation

### Template Conventions
- Use double quotes for `{% trans %}` strings (to support contractions like "you've")
- Always extend `app/base.html`
- Include breadcrumb block
- Use consistent padding: `px-4 sm:px-6 lg:px-8`
- Dark mode classes for all colors

### Database Filtering
- Always filter by organization context
- Use `selected_organization(request)` helper
- Apply user permissions checks in views

## Related Files

- **URL Config:** `app_urls.py`, `app_views.py`
- **Templates:** `matchco/templates/app/`, `matchco/templates/ui/base.html`
- **Navigation:** `matchco/core/menu.py`, `matchco/core/context_processors.py`
- **Auth:** `cep/views.py` (SmartHomeView)
- **Routing:** `cep/urls.py` (main entry point)

## Testing Checklist

- [ ] All routes accessible with authenticated user
- [ ] Navbar toggles sidebar on mobile
- [ ] User menu shows correct profile info
- [ ] Organization selector works
- [ ] Dark mode toggle works
- [ ] Feed displays published articles
- [ ] Wiki shows knowledge base
- [ ] Trails show user assignments
- [ ] Breadcrumbs display correctly
- [ ] Responsive design on mobile/tablet/desktop
- [ ] Service worker active (offline support)
