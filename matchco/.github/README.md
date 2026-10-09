# GitHub Issues & Development Tracking

This directory contains the centralized issue tracking system for Talk Learning Platform development.

## Files

- **`issues.json`** - Machine-readable issue database with 28 problems, dependencies, and effort estimates
- **`ISSUES_TRACKER.md`** - Human-readable summary with timeline, priority levels, and dependency graphs

## Issue Structure

Each issue includes:
- **ID** (001-028) - Unique identifier
- **Priority** - CRITICAL, HIGH, MEDIUM, LOW
- **Title** - Clear, action-oriented description
- **Acceptance Criteria** - Testable completion requirements
- **Estimated Hours** - Development effort
- **Dependencies** - Which issues must complete first
- **Feature** - Which system component (Content Sharing, Completion Tracking, etc.)
- **Phase** - Development phase and week
- **Status** - not_started, in_progress, pending_decision, completed

## Priority Levels

**CRITICAL (7):** Blocking other work, must start immediately
- Storage decision for video
- Content Sharing core models & API
- Completion Tracking Level 1 foundations

**HIGH (6):** Important features that depend on CRITICAL
- Manager UIs, dashboards, notifications
- Quiz enhancements

**MEDIUM (13):** Advanced features for later phases
- Level 2/3 Completion Tracking
- Video player, compliance, analytics

**LOW (2):** Optional/nice-to-have
- Advanced dashboards, email integration

## Timeline

- **Weeks 1-2:** CRITICAL issues (45h) - Foundation
- **Weeks 2-3:** HIGH issues (43h) - UIs & Polish
- **Weeks 3-4:** MEDIUM early items (38h) - Level 2 foundations
- **Weeks 4-5:** MEDIUM late items (44h) - Level 3 & compliance
- **Week 5+:** LOW items (20h) - Analytics & notifications

**Total:** 28 issues, ~203 hours, 5-6 weeks

## How to Create GitHub Issues

When the GitHub remote is configured:

```bash
# Option 1: Create issues from JSON (requires jq)
jq -r '.issues[] | "\(.priority): [\(.id)] \(.title)"' .github/issues.json | while read line; do
  gh issue create --title "$line"
done

# Option 2: Create manually from ISSUES_TRACKER.md
# Copy each issue and create via:
gh issue create --title "PRIORITY: [ID] Title" \
  --body "Description and acceptance criteria" \
  --label "priority-tag"
```

## Linking to Git

Before creating issues on GitHub, ensure:

1. GitHub repository is created at https://github.com/francopoleo/talk
2. Remote is configured:
   ```bash
   git remote add origin https://github.com/francopoleo/talk.git
   git branch -M main
   git push -u origin main
   ```
3. Issues can then be created via `gh` CLI

## Tracking Progress

As work progresses:

1. Update issue status in `issues.json`
2. Update EXECUTION_PLAN.md weekly with progress
3. Link EXECUTION_PLAN issues to GitHub issue numbers
4. Use GitHub projects for sprint tracking

## Decoupling from Documentation

This system shifts from token-heavy documentation reading to GitHub Issues as source of truth:

- **Before:** Tokens spent reading scattered markdown files
- **After:** Tokens spent solving actual problems, tracking in Git

## Key Decision Points

**#007 - Storage Decision** (BLOCKING)
- Decision needed: YouTube only vs S3 only vs Hybrid
- Affects: Video player, compliance, cost
- Timeline: Must decide before Week 3

## Questions?

See:
- `ISSUES_TRACKER.md` - Full issue breakdown with timelines
- `EXECUTION_PLAN.md` (root) - High-level phases and project status
- `issues.json` - Raw data for automation

---

**Generated:** 2026-07-27  
**Status:** Ready for GitHub Issues creation  
**Maintenance:** Update weekly as work progresses
