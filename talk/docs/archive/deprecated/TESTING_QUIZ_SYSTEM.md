# 🧪 Quiz System Testing Guide

## Pre-Testing Setup

### 1. Create Organization & User (if needed)

```python
# In Django shell
from organizations.models import Organization
from django.contrib.auth import get_user_model

User = get_user_model()

# Create organization
org = Organization.objects.create(
    name="Hospital Central",
    slug="hospital-central"
)

# Create user with staff permissions
user = User.objects.create_user(
    email="admin@hospital.com",
    password="testpass123",
    is_staff=True,
    is_superuser=True
)
```

### 2. Generate Hospital Sample Data

```bash
python manage.py create_hospital_sample_data 1 --user-id <USER_ID>
```

This creates:
- Course: "Segurança do Paciente e Protocolos Hospitalares"
- 3 Modules with realistic content
- 3 Quizzes with 7 questions
- Real hospital education scenarios

---

## 🎯 Test Scenarios

### SCENARIO 1: Complete Quiz Creation Flow

#### Expected Path:
```
Console → Course Editor → Select Course → Module Card → "Add Quiz"
→ Quick Quiz Form → Quiz Created → Quiz Editor → Add Questions
→ Question Editor → Add Answers → Back to Quiz Editor
```

#### Step-by-Step Test:

**1. Navigate to Course Editor**
- [ ] Go to `/console/course-editor/`
- [ ] Should see "Course Editor" header
- [ ] Should see list of courses
- ✅ Expected: Courses displayed with create button

**2. Open Course**
- [ ] Click on existing course (or create one)
- [ ] Should see "Course Editor Detail" page
- [ ] Should see modules list
- ✅ Expected: Professional card layout with proper padding

**3. Add Quiz**
- [ ] In a module card, click "Add Quiz" button (or click on module)
- [ ] Should navigate to Quick Quiz Form
- [ ] Fill form:
  - Title: "Quiz: Protocolos de Segurança"
  - Type: Select "Formative"
  - Required Score: 70
  - Mark as Required: Yes
- [ ] Click "Create Quiz"
- ✅ Expected: Quiz created, redirects to Quiz Editor

**4. Quiz Editor Page**
- [ ] Should see quiz header: "Quiz: Protocolos de Segurança"
- [ ] Should see 4-column stats:
  - Questions: 0
  - Type: Formative
  - Passing: 70%
  - Required: ✓
- [ ] Should see "Questions" section
- [ ] Should see "No questions yet" message
- [ ] Should see "Add First Question" button
- ✅ Expected: Clean, professional interface with clear CTAs

**5. Add First Question**
- [ ] Click "Add First Question" or "+ Add Question"
- [ ] Fill Question Form:
  - Question Type: "Multiple Choice"
  - Question Text: "Qual é o primeiro passo na higiene de mãos?"
  - Explanation: "O passo inicial é remover jóias e relógios."
- [ ] Click "Add Question"
- ✅ Expected: Redirects back to Quiz Editor with question in list

**6. Verify Question Added**
- [ ] Should see question in list:
  - Q1: "Qual é o primeiro passo na higiene de mãos?"
  - Type: "Multiple Choice"
  - 0 answers
  - Status: "⚠️ Missing answers"
- ✅ Expected: Question displayed with status indicator

**7. Add Answers**
- [ ] Click "Edit" on the question
- [ ] Should see Question Form on left, Answers panel on right
- [ ] Answers panel should show "No answers yet" + "Add Answer" button
- [ ] Click "Add Answer"
- [ ] Add first answer:
  - Text: "Remover jóias e relógios"
  - Mark as correct: ✓ (checked)
  - Click "Add Answer"
- ✅ Expected: Redirects back to question form, answer appears in panel

**8. Add More Answers**
- [ ] Repeat "Add Answer" for:
  - "Colocar luvas" (not correct)
  - "Usar álcool gel" (not correct)
  - "Lavar com sabonete" (not correct)
- [ ] Each should appear in answers panel
- [ ] Should see ✓ mark on correct answer
- ✅ Expected: All answers listed, one marked as correct

**9. Back to Quiz Editor**
- [ ] Click "Back" or "Save Changes"
- [ ] Should return to Quiz Editor
- [ ] Question should now show:
  - Status: "✓ Complete" (green badge)
  - Answers: "4 answers"
- ✅ Expected: Question marked as complete

**10. Add Second Question (Different Type)**
- [ ] Click "+ Add Question"
- [ ] Fill form:
  - Type: "True/False"
  - Text: "Verdadeiro ou Falso: Luvas substituem a necessidade de lavar as mãos?"
  - Explanation: "Falso. Mãos sob luvas podem estar contaminadas."
- [ ] Click "Add Question"
- [ ] Add answers:
  - "Verdadeiro" (not correct)
  - "Falso" (correct)
- ✅ Expected: True/False question with 2 answers

**11. Delete Answer Test**
- [ ] Go back to first question
- [ ] In answers panel, click "Delete" on one answer
- [ ] Should confirm deletion
- [ ] Answer should be removed
- ✅ Expected: Smooth deletion with confirmation

**12. Delete Question Test**
- [ ] Go to Quiz Editor
- [ ] Click "Delete" on a question
- [ ] Should show confirmation dialog
- [ ] Dialog shows question text
- [ ] Should warn: "All answers and user responses will be deleted"
- [ ] Click "Delete"
- ✅ Expected: Question removed from list

---

### SCENARIO 2: Quiz Statistics & Navigation

#### Test Quiz Detail Page

**1. Navigate to Quiz Detail**
- [ ] From Quiz Editor, click "View Statistics" button
- [ ] Or: Go to `/console/quizzes/<id>/`
- ✅ Expected: Different page showing stats, not editor

**2. Check Stats Display**
- [ ] Should show stats cards:
  - Questions: (count)
  - Total Attempts: (count)
  - Passed: (count)
  - Avg Score: (average)
- [ ] Should show Configuration section
- [ ] Should list all questions
- ✅ Expected: Read-only view of quiz

**3. Navigate Back**
- [ ] Click "Back to Quiz Editor"
- [ ] Should return to `/console/quizzes/<id>/editor/`
- [ ] Not to quiz list
- ✅ Expected: Proper navigation flow

---

### SCENARIO 3: Multi-Quiz Management

#### Test Managing Multiple Quizzes

**1. Go to Quizzes List**
- [ ] Navigate to `/console/quizzes/`
- [ ] Should see "Quizzes & Tests" header
- [ ] Should see table with all quizzes
- [ ] Should have search functionality
- ✅ Expected: Professional table layout

**2. Quiz Actions**
- [ ] Each quiz row has actions:
  - "View" → Quiz Detail
  - "Edit" → Edit settings
  - "Attempts" → View student attempts
- ✅ Expected: All actions clickable and functional

**3. Create New Quiz**
- [ ] Click "+ New Quiz"
- [ ] Should open full quiz form (not quick form)
- [ ] Should have all settings available
- ✅ Expected: Standalone quiz creation

---

### SCENARIO 4: Responsive Design Testing

#### Mobile Testing

**1. Test on Mobile Size (320px width)**

In browser DevTools, set viewport to iPhone size:

**Course Editor Detail**
- [ ] Padding looks correct (not too wide, not cramped)
- [ ] Module cards stack properly
- [ ] Buttons are touchable (not too small)
- [ ] Text is readable
- ✅ Expected: Mobile-optimized layout

**Quiz Editor**
- [ ] Stats cards show in 2-column grid
- [ ] Questions list is readable
- [ ] Action buttons are visible
- [ ] No horizontal scroll
- ✅ Expected: All content visible without scroll

**Question Form**
- [ ] Form fields fill width properly
- [ ] Answers panel appears below on mobile
- [ ] No overlapping elements
- ✅ Expected: Stacked layout on mobile

**2. Test on Tablet (768px)**
- [ ] 2-3 column layouts work
- [ ] Spacing is comfortable
- [ ] Still no horizontal scroll
- ✅ Expected: Tablet-optimized

**3. Test on Desktop (1920px)**
- [ ] Full 4-column stats
- [ ] 2-column question/answers layout
- [ ] Maximum widths respected (max-w-7xl)
- [ ] Proper spacing between elements
- ✅ Expected: Desktop-optimized

---

### SCENARIO 5: Dark Mode Testing

**1. Enable Dark Mode**
- [ ] In browser settings or HTML class
- [ ] Add `dark` class to html element
- ✅ Expected: All colors invert properly

**2. Check Elements**
- [ ] Text readable (white on dark gray)
- [ ] Cards visible (dark gray background)
- [ ] Buttons visible (color contrast OK)
- [ ] Badges visible
- [ ] Form inputs visible
- ✅ Expected: Full dark mode support

---

### SCENARIO 6: Permissions & Security

**1. Test Manager Only Access**
- [ ] Log in as non-manager user
- [ ] Try accessing `/console/quizzes/`
- ✅ Expected: Redirect to permission denied or login

**2. Test Owner Verification**
- [ ] Create quiz as User A
- [ ] Log in as User B
- [ ] Try editing quiz
- ✅ Expected: Permission denied or redirect

**3. Test Organization Filtering**
- [ ] Create quiz in Organization 1
- [ ] Switch to Organization 2
- [ ] Quiz should not appear
- ✅ Expected: Only org-specific quizzes visible

---

### SCENARIO 7: Sample Hospital Data

**1. Generate Data**
```bash
python manage.py create_hospital_sample_data 1
```

**2. Verify Course Created**
- [ ] Should see: "Segurança do Paciente e Protocolos Hospitalares"
- [ ] Should have owner (current user)
- [ ] Should have organization (ID 1)
- ✅ Expected: Course visible in course list

**3. Verify Modules**
- [ ] Should see 3 modules:
  1. Higiene das Mãos e Prevenção de Infecções
  2. Identificação Segura do Paciente
  3. Controle de Infecções Relacionadas à Assistência
- ✅ Expected: All modules visible

**4. Verify Quizzes**
- [ ] Each module should have 1 quiz
- [ ] Go to Quizzes list: should see 3 quizzes
- [ ] Each quiz should have realistic title
- ✅ Expected: Quizzes properly linked

**5. Verify Questions**
- [ ] Each quiz should have 2-3 questions
- [ ] Total should be 7 questions across all quizzes
- [ ] Questions should have realistic medical content
- ✅ Expected: Questions properly created

**6. Verify Answers**
- [ ] Each question should have multiple answers
- [ ] Exactly 1 answer marked as correct per question
- [ ] True/False questions have exactly 2 answers
- ✅ Expected: All answers present and validated

---

## 🐛 Bug Checklist

**Navigation Issues**
- [ ] Back links point to correct pages
- [ ] Quiz Editor is main edit interface
- [ ] No infinite redirects
- [ ] All URLs resolve properly

**Data Issues**
- [ ] Owner set correctly on creation
- [ ] Organization set correctly
- [ ] Question order maintained
- [ ] Answer correct status enforced

**UI Issues**
- [ ] Padding consistent across all pages
- [ ] No broken images/icons
- [ ] Text truncation works properly
- [ ] Status badges display correctly
- [ ] Hover effects work

**Responsive Issues**
- [ ] No horizontal scrolling on mobile
- [ ] Touch targets large enough
- [ ] Text readable at all sizes
- [ ] Images/icons scale properly

**Dark Mode Issues**
- [ ] Text contrast sufficient
- [ ] All elements visible
- [ ] No color bleeding
- [ ] Badges readable

---

## 📊 Test Results Template

```markdown
### Test Run: [Date]

**Tester:** [Name]
**Environment:** [Desktop/Mobile/Tablet] [Browser] [OS]

#### Scenario 1: Quiz Creation
- [ ] PASS / [ ] FAIL
- Notes: ___________

#### Scenario 2: Statistics
- [ ] PASS / [ ] FAIL
- Notes: ___________

#### Scenario 3: Multi-Quiz
- [ ] PASS / [ ] FAIL
- Notes: ___________

#### Scenario 4: Responsive
- [ ] PASS / [ ] FAIL
- Notes: ___________

#### Scenario 5: Dark Mode
- [ ] PASS / [ ] FAIL
- Notes: ___________

#### Scenario 6: Permissions
- [ ] PASS / [ ] FAIL
- Notes: ___________

#### Scenario 7: Sample Data
- [ ] PASS / [ ] FAIL
- Notes: ___________

**Overall:** PASS / FAIL
**Issues Found:** [List any]
**Recommendations:** [Any improvements]
```

---

## 🚀 Performance Testing

### Load Times
- [ ] Quiz Editor loads in < 2s
- [ ] Question Add form loads in < 1s
- [ ] Quiz List loads in < 3s

### Database Queries
- [ ] Quiz Editor uses prefetch_related for questions
- [ ] Quiz List uses select_related for owner/org
- [ ] No N+1 query problems

### Mobile Performance
- [ ] Lighthouse score > 85
- [ ] First Contentful Paint < 2s
- [ ] Cumulative Layout Shift < 0.1

---

## ✅ Sign-Off Checklist

- [ ] All scenarios tested
- [ ] No critical bugs found
- [ ] Mobile responsive working
- [ ] Dark mode working
- [ ] Permissions enforced
- [ ] Sample data generated
- [ ] Performance acceptable
- [ ] Ready for production

**Sign-off Date:** ___________
**Tested By:** ___________
**Approved By:** ___________
