# 🚀 GitHub Workflow - Talk Learning Platform

**Single source of truth:** GitHub Issues + PRs + Commits  
**Token reduction:** No scattered docs, everything in Git

---

## 📋 Quick Start

### 1️⃣ When You Find a Bug/Feature
```bash
# Option A: Via CLI (fastest)
gh issue create --title "[bug|feature]: Description" \
  --body "Steps to reproduce or feature details" \
  --label "bug" # or "critical,high,low"

# Option B: Via GitHub Web
https://github.com/francopoleo/talk/issues/new
```

### 2️⃣ Development Workflow
```bash
# Get issue details
gh issue view 123

# Create feature branch (links to issue)
git checkout -b fix/#123-short-description

# Code + Test + Commit
git add .
git commit -m "fix: #123 description of change"

# Push to remote
git push origin fix/#123

# Create PR (auto-links to issue)
gh pr create --title "Resolve #123" --body "Closes #123"

# Review + Merge (closes issue automatically)
gh pr merge 123 --squash
```

### 3️⃣ Communication
```
Issue #123
├── Description (initial problem)
├── Comment #1: "Working on this, found X"
├── Comment #2: "Solution: did Y instead of Z"
├── Comment #3: "Tested on mobile/desktop ✅"
└── PR #456 → Merged → Issue closes automatically
```

---

## 🏷️ Labels (Already Defined)

Use these when creating issues:

| Label | When | Example |
|-------|------|---------|
| `critical` | Blocks other work | #007 Video storage decision |
| `high` | Important but not blocking | #008 Manager UI |
| `bug` | Something broken | #050 Login fails on mobile |
| `low` | Nice-to-have | #027 Analytics dashboard |

**Apply multiple:** `critical,high` or `bug,high`

```bash
# With labels
gh issue create --title "[bug]: Login timeout" --label "bug,high"
```

---

## 📊 GitHub Project (Manual Setup Required)

**Create here:** https://github.com/francopoleo/talk/projects

### Board Columns (Set up manually):
1. **🔴 Backlog** (all new issues)
2. **🟡 Ready** (critical + next sprint)
3. **🟠 In Progress** (working on)
4. **🟢 Testing** (PR created)
5. **✅ Done** (merged)

**Add issues to project:**
```bash
# Can link issues manually on GitHub web
# OR use CLI (if project supports it)
```

---

## 🔄 PR Template (Auto-filled)

When creating PR, use this template:

```markdown
## What changed?
Closes #123

## Why?
Brief explanation

## How to test?
- [ ] Step 1
- [ ] Step 2

## Screenshots (if UI change)
[If applicable]
```

**Auto-generate:**
```bash
gh pr create --title "Resolve #123" --body "Closes #123"
```

---

## 📈 Status Tracking (Minimal)

**Weekly update only:**

Update `/docs/EXECUTION_PLAN.md`:
```markdown
## Status (Week of 2026-07-27)

- #001-006 (Critical): 40% done
  - #001: ✅ Done
  - #002: 🟡 In Progress
  - #003-006: 🔲 Not Started

- Next: #007 decision + #008 starts
```

**That's it.** Everything else lives in GitHub Issues.

---

## 🎯 Reducing Tokens

### ❌ DON'T
- Read docs to understand a feature
- Search scattered markdown files
- Ask me to explain old decisions

### ✅ DO
- Check issue #XXX for context
- Read PR comments for decisions
- Search GitHub Issues/Discussions

**Why?** 
- Issue #001 = complete context + history
- PR #456 = decision trail + testing notes
- Git commit = immutable audit log

---

## 🏗️ Architecture Questions?

Use **GitHub Discussions** instead of docs:

```bash
# Create discussion
gh discussion create --title "Should we use YouTube + S3 for videos?" \
  --body "Pros/cons: ..."
```

Then link from issues:
```
#007 (Video Storage Decision)
See Discussion: #D-42 for pros/cons analysis
```

---

## 🔐 Access & Permissions

- **Issues:** Anyone can view
- **PRs:** Anyone can review
- **Merge:** You (admin)
- **Push:** Only main branch (via PR)

---

## 📱 Mobile-Friendly Commands

```bash
# Check PR status
gh pr list --state all

# See open issues  
gh issue list

# Get issue details (includes comments)
gh issue view 123

# Comment on issue/PR
gh issue comment 123 --body "Fixed on my branch"
```

---

## 🚨 Emergency/Hotfix

If production breaks:

```bash
# Create hotfix branch
git checkout -b hotfix/#999-urgent-fix

# Fast fix + commit
git commit -m "hotfix: #999 urgent description"

# Push + PR
git push origin hotfix/#999
gh pr create --title "HOTFIX: #999" --label "critical"

# Merge immediately
gh pr merge 999
```

---

## 📝 Documentation

### What lives where:

| Type | Location | Why |
|------|----------|-----|
| Active features | GitHub Issues #001-028 | Single source of truth |
| Phase status | `/docs/EXECUTION_PLAN.md` | Weekly update only |
| UI standards | `/docs/2_ARCHITECTURE/FLOWBITE_DESIGN_SYSTEM.md` | Rarely changes |
| Decisions | GitHub Discussions | Conversation trail |
| Setup/deploy | GitHub Wiki (future) | Runbooks only |
| Legacy docs | `/docs_archived/` | Reference if needed |

---

## ⚡ Productivity Tips

1. **Create issue immediately** → No lost context
2. **Link in code** → `Closes #123` in commit
3. **Use labels** → Filter `is:open label:critical`
4. **Automate PR** → `gh pr create` 1 line
5. **Skip long meetings** → Issue + comments = async discussion

---

## 🔗 Quick Links

- **Issues:** https://github.com/francopoleo/talk/issues
- **PRs:** https://github.com/francopoleo/talk/pulls
- **Projects:** https://github.com/francopoleo/talk/projects
- **Discussions:** https://github.com/francopoleo/talk/discussions
- **Current Issues:** `.github/ISSUES_TRACKER.md`

---

**Last Updated:** 2026-07-27  
**Owner:** Development Team  
**Read Time:** 5 min  
**Practice Time:** 2 min
