# 💻 Development Workflow

**For:** Developers working on features  
**Time:** 5 minutes (quick reference)

---

## Branch Strategy

```
main (production)
├── feature/#001-description (your branch)
├── bugfix/#050-description
└── hotfix/#999-urgent
```

**Pattern:** `{type}/{issue-number}-{short-description}`

---

## Typical Development Flow

### 1. Pick an Issue

From GitHub Issues (#001-044):
```bash
gh issue view 001
# Or see: https://github.com/francopoleo/matchco-platform/issues
```

### 2. Create Feature Branch

```bash
git checkout -b feature/#001-description
```

**Naming:**
- `feature/#001` - New feature
- `fix/#050` - Bug fix
- `docs/#036` - Documentation
- `refactor/#100` - Code cleanup

### 3. Develop & Test

```bash
# Make changes
git add .
git commit -m "feat: #001 description of change"

# Run tests
docker exec matchco-app python manage.py test

# Check code quality
docker exec matchco-app python manage.py check
```

### 4. Push & Create PR

```bash
git push origin feature/#001

# Create PR (auto-links to issue)
gh pr create --title "Resolve #001" --body "Closes #001"
```

### 5. Review & Merge

```bash
# View PR
gh pr view

# Merge (closes issue automatically)
gh pr merge --squash
```

---

## Commit Message Format

**Good:**
```
feat: #001 add content sharing model

Add ContentSharePackage model with FK to company,
status tracking, and expiration logic.
```

**Bad:**
```
fixed stuff
updates
work in progress
```

**Format:** `{type}: #{issue} {description}`

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code cleanup
- `test:` - Test addition
- `chore:` - Maintenance

---

## Testing

### Run All Tests
```bash
docker exec matchco-app python manage.py test
```

### Run Specific Test
```bash
docker exec matchco-app python manage.py test courses.tests.QuizTest
```

### With Coverage
```bash
docker exec matchco-app coverage run --source='.' manage.py test
docker exec matchco-app coverage report
```

### By App
```bash
# Test specific app
docker exec matchco-app python manage.py test courses
docker exec matchco-app python manage.py test console
docker exec matchco-app python manage.py test students
```

**Target:** >80% coverage

---

## Code Review Checklist

Before submitting PR:

- [ ] Issue #XXX is linked in PR description
- [ ] Tests pass: `python manage.py test`
- [ ] Code follows style guide
- [ ] No new warnings/errors
- [ ] Comments added for complex logic
- [ ] Database migrations created (if needed)
- [ ] Documentation updated (if needed)

---

## Common Workflows

### Adding a New Feature

```bash
git checkout -b feature/#001-new-feature
# ... code ...
git commit -m "feat: #001 add feature"
gh pr create --title "Resolve #001"
```

### Fixing a Bug

```bash
git checkout -b fix/#050-bug-name
# ... code ...
git commit -m "fix: #050 description"
gh pr create --title "Resolve #050"
```

### Hotfix (Production)

```bash
git checkout -b hotfix/#999-urgent
# ... urgent fix ...
git commit -m "hotfix: #999 description"
gh pr create --title "HOTFIX #999" --label "critical"
gh pr merge --squash  # Merge immediately
```

---

## Useful Commands

```bash
# See current branch
git branch

# List all branches
git branch -a

# Delete local branch
git branch -d feature/#001

# Push and set upstream
git push -u origin feature/#001

# See commit history
git log --oneline

# Undo last commit (not pushed)
git reset --soft HEAD~1

# Stash changes
git stash
git stash pop
```

---

## Getting Help

- **Issue context:** `gh issue view #001`
- **Workflow questions:** `.github/GITHUB_WORKFLOW.md`
- **Architecture:** `REFERENCES/ARCHITECTURE.md`
- **Database:** `REFERENCES/DATABASE.md`
- **API:** `REFERENCES/API.md`

---

**Next:** See `03_TESTING.md` for detailed testing guide
