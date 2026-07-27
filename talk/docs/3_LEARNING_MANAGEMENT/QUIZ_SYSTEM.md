# 🎓 Quiz & Assessment System

**Status:** ✅ PRODUCTION READY v2.0

Complete documentation for creating, managing, and evaluating quizzes within the Talk Learning Platform.

---

## 📋 Quick Reference URLs

| Action | URL | Access |
|--------|-----|--------|
| List quizzes | `/console/quizzes/` | Manager |
| Quiz editor (add questions) | `/console/quizzes/<id>/editor/` | Manager |
| Create question | `/console/quizzes/<id>/questions/new/` | Manager |
| Edit question | `/console/quizzes/<id>/questions/<qid>/edit/` | Manager |
| Add answer | `/console/quizzes/<id>/questions/<qid>/answers/new/` | Manager |
| Student takes quiz | `/students/quiz/<id>/take/` | Student |
| View result | `/students/quiz/<id>/result/<aid>/` | Student |
| Attempt history | `/students/quiz/<id>/attempts/` | Student |

---

## 🏗️ Architecture Overview

```
Talk Learning Platform
├── Course Management
│   └── CourseEditorDetailView
│       ├── Course → Modules (N:1)
│       └── Module → Content (N:1)
│           ├── Text
│           ├── Video
│           ├── File
│           └── Quiz ← THIS SYSTEM
│
├── Quiz Management (Console)
│   ├── QuizListView
│   ├── QuizDetailView (Statistics)
│   ├── QuizEditorView (Manage Questions) ← MAIN EDIT INTERFACE
│   │   ├── QuestionCreateView
│   │   ├── QuestionUpdateView
│   │   ├── QuestionDeleteView
│   │   ├── AnswerCreateView
│   │   ├── AnswerUpdateView
│   │   └── AnswerDeleteView
│   └── QuizAttemptsView
│
└── Student Interface
    ├── QuizTakeView
    ├── QuizSubmitView
    ├── QuizResultView
    └── QuizAttemptsView (History)
```

---

## 📁 File Structure

### Templates (Console Management)
- **quiz_list.html** - All quizzes with search & filter
- **quiz_editor.html** - Main page to manage questions ⭐
- **quiz_detail.html** - Statistics and configuration
- **quiz_form.html** - Create/edit quiz settings
- **question_form.html** - Create/edit question with answers panel
- **answer_form.html** - Create/edit individual answers
- **quiz_confirm_delete.html** - Delete confirmation
- **question_confirm_delete.html** - Delete confirmation
- **answer_confirm_delete.html** - Delete confirmation

### Views (Django)
- **console/quiz_console_views.py** - All quiz management views
- **console/course_editor_views.py** - Course & module management

### Models (courses/models.py)
- **Quiz** - Main quiz model with settings
- **Question** - Individual questions with type & explanation
- **Answer** - Answer options with correct flag
- **UserQuizAttempt** - Attempt history per user
- **UserAnswer** - Individual user answers and scores

---

## 🎯 Main Features

### Quiz Management (Console)
✅ Create quizzes with:
- Title & description
- Quiz type (formative/exam/certification)
- Passing score (0-100%)
- Required/optional flag
- Multiple attempt settings
- Time limit in minutes
- Feedback type
- Question shuffling

✅ Organize questions:
- Add/edit/delete questions
- 4 question types (multiple choice, true/false, short answer, multiple correct)
- Question explanations (shown after submission)
- Answer management with correct flag validation

✅ View analytics:
- Question count
- Student attempts
- Pass rate
- Average scores

### Student Interface
✅ Take quizzes:
- Browse questions in order or shuffled
- Select/type answers based on question type
- See timer if time limit exists
- Submit all answers at once

✅ View results:
- Score in percentage
- Correct/incorrect count
- Per-question breakdown
- Answer explanations
- Retry if permitted

---

## 🚀 Step-by-Step Usage Guide

### PART 1: CREATE COURSE & MODULE

#### 1. Open Course Editor
```
Console → Course Editor
or navigate to: /console/course-editor/
```

#### 2. Create or Select Course
- Click existing course OR click "+ New Course"
- Fill title and description

#### 3. Add Module (if needed)
```
Button: "+ New Module"
Fill:
  - Title: "Module 1: Introduction"
  - Description: "Basic concepts" (optional)
```

---

### PART 2: ADD QUIZ TO MODULE

#### 1. Click "+ Add Quiz" on Module
```
You'll see a quick quiz form
```

#### 2. Fill Quiz Settings
```
Required fields:
  • Title*: "Quiz: Patient Safety Protocols"
  • Passing Score*: 70 (0-100)

Optional fields:
  • Description
  • Type: Formative / Exam / Certification
  • Required: ☑ Mark if mandatory
  • Time Limit: minutes (leave empty for no limit)
```

#### 3. Click "Create Quiz"
```
✓ Quiz created with correct owner
✓ Organization auto-set
✓ Redirects to Quiz Editor
✓ Content linked to module
```

---

### PART 3: ADD QUESTIONS

#### 1. You're Now in Quiz Editor
```
Page: Quizzes & Tests → [Quiz Name] → Add Questions
```

#### 2. Click "+ Add Question"
```
Fill:
  • Question Type*: 
      - Multiple Choice
      - True/False
      - Short Answer
      - Multiple Correct (select multiple answers)
  
  • Question Text*: "What is the first step in hand hygiene?"
  
  • Explanation: "Appears after submission" (optional)
```

#### 3. Click "Add Question"
```
✓ Question created
✓ Redirects to question editor
✓ Answers panel appears on right
```

---

### PART 4: ADD ANSWERS

#### 1. In Answers Panel (Right Side)
```
Click: "+ Add Answer"
```

#### 2. Fill Answer
```
Fields:
  • Answer Text*: "Remove jewelry and watches"
  • Correct: ☑ Mark if this is the correct answer
```

#### 3. Click "Add Answer"
```
Answer appears in list
```

#### 4. Add More Answers
```
Repeat for each option (typically 4 for multiple choice)
```

#### 5. Validation Rules
```
✓ Required: At least 1 answer marked as correct
✓ For M. Choice: Typically 4 options
✓ For True/False: Exactly 2 options
```

---

## 📊 Data Models

```python
class Quiz(models.Model):
    organization = ForeignKey(Organization)
    owner = ForeignKey(User)
    title = CharField
    overview = TextField
    quiz_type = Choice(['formative', 'exam', 'certification'])
    required_score_to_pass = IntegerField (0-100)
    is_required = BooleanField
    allow_multiple_attempts = BooleanField
    max_attempts = IntegerField (null=True)
    time_limit_minutes = IntegerField (null=True)
    shuffle_questions = BooleanField
    created_at = DateTimeField
    updated_at = DateTimeField

class Question(models.Model):
    quiz = ForeignKey(Quiz)
    question_type = Choice([
        'multiple_choice',
        'true_false',
        'short_answer',
        'multiple_correct'
    ])
    text = TextField
    explanation = TextField (optional)
    order = IntegerField
    created_at = DateTimeField
    
    def has_correct_answer(self):
        return self.answers.filter(correct=True).exists()

class Answer(models.Model):
    question = ForeignKey(Question)
    text = CharField
    correct = BooleanField
    order = IntegerField
    created_at = DateTimeField

class UserQuizAttempt(models.Model):
    user = ForeignKey(User)
    quiz = ForeignKey(Quiz)
    attempt_number = IntegerField
    score = IntegerField (percentage)
    passed = BooleanField
    time_spent_seconds = IntegerField
    started_at = DateTimeField
    submitted_at = DateTimeField
    
class UserAnswer(models.Model):
    attempt = ForeignKey(UserQuizAttempt)
    question = ForeignKey(Question)
    selected_answer = ForeignKey(Answer, null=True)
    selected_text = CharField (for short answer)
    is_correct = BooleanField
    points_earned = IntegerField
```

---

## 🔧 Technical Implementation

### Video Tracking (95% rule)
```javascript
// Mark complete when reaching 95% of duration
video.addEventListener('timeupdate', function() {
    const percent = (video.currentTime / video.duration) * 100;
    if (percent >= 95) {
        markModuleComplete('video', 95);
    }
});
```

### Form Validation
```javascript
function validateForm() {
    const inputs = document.querySelectorAll(
        'input[type="radio"], input[type="checkbox"], input[type="text"]'
    );
    let hasAtLeastOneAnswer = false;
    
    for (let input of inputs) {
        if (input.type === 'text' && input.value.trim() !== '') {
            hasAtLeastOneAnswer = true;
            break;
        } else if ((input.type === 'radio' || input.type === 'checkbox') && input.checked) {
            hasAtLeastOneAnswer = true;
            break;
        }
    }
    
    if (!hasAtLeastOneAnswer) {
        alert('Please answer at least one question.');
        return false;
    }
    
    // Disable button to prevent double submission
    document.getElementById('submit-btn').disabled = true;
    return true;
}
```

### Score Calculation
```python
def calculate_score(attempt):
    total_questions = attempt.quiz.questions.count()
    correct_count = attempt.useranswer_set.filter(is_correct=True).count()
    score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    return int(score)
```

---

## 📝 Question Types

### 1. Multiple Choice
```
Question: "Which is the first step in hand hygiene?"

Options (choose ONE):
○ Remove jewelry and watches (correct ✓)
○ Put on gloves
○ Use alcohol gel
○ Wash with soap
```

### 2. True/False
```
Question: "True or False: Gloves replace the need to wash hands?"

Options (choose ONE):
○ True
○ False (correct ✓)
```

### 3. Short Answer
```
Question: "Name one item that should be removed before hand hygiene."

Answer: _____________________ 
(Matches against correct answer text)
```

### 4. Multiple Correct
```
Question: "Select all correct steps in hand hygiene:"

Options (choose MULTIPLE):
☑ Remove jewelry (correct ✓)
☑ Wet hands with water (correct ✓)
☐ Use only hand sanitizer
☑ Dry hands thoroughly (correct ✓)
```

---

## 👥 Permissions & Access Control

| Action | Manager | Admin | Student |
|--------|---------|-------|---------|
| Create quiz | ✓ | ✓ | ✗ |
| Edit question | ✓ | ✓ | ✗ |
| View answers | ✓ | ✓ | ✓ |
| Take quiz | ✗ | ✗ | ✓ |
| View results | ✓ | ✓ | ✓ |
| View history | ✓ | ✓ | ✓ (own only) |

---

## 📊 Student Experience

### Taking a Quiz

**URL:** `/students/quiz/<id>/take/`

**What student sees:**
1. Quiz header with title & description
2. Info cards:
   - Question count
   - Passing score %
   - Attempt number
   - Time limit (if set)
3. Questions displayed in order
4. Answer options based on question type
5. Submit button at bottom

**Flow:**
```
Start → Answer Questions → Submit → 
Automatic Score → Redirect to Results
```

### Viewing Results

**URL:** `/students/quiz/<id>/result/<attempt_id>/`

**What student sees:**
1. Score in percentage (color-coded: green if passed, red if failed)
2. Breakdown: "You got 6 out of 8 correct"
3. Per-question review:
   - Question text
   - Student's answer
   - Correct answer
   - Explanation (if provided)
4. Retry button (if allowed)
5. Back to course

---

## 🧪 Testing Guide

### Prerequisites
```bash
# Create organization & user
python manage.py shell
from organizations.models import Organization
from django.contrib.auth import get_user_model

org = Organization.objects.create(name="Test Org", slug="test-org")
User = get_user_model()
user = User.objects.create_user(email="test@test.com", password="test123")
```

### Generate Sample Data
```bash
python manage.py create_hospital_sample_data 1
```

This creates:
- Course: "Patient Safety & Hospital Protocols"
- 3 Modules with realistic content
- 3 Quizzes with 7 questions total
- Real hospital education scenarios

### Test Scenarios

#### ✅ Scenario 1: Complete Quiz Creation
- Navigate to Course Editor
- Create/open course
- Add module
- Create quiz
- Add 3 questions (MC, T/F, Short Answer)
- Add 4 answers per question
- Verify all appears in editor

#### ✅ Scenario 2: Student Quiz Flow
- Log in as student
- Access quiz URL
- Answer all questions
- Submit
- View results with score

#### ✅ Scenario 3: Responsive Design
Test on mobile (320px), tablet (768px), desktop (1920px)
- [ ] No horizontal scroll
- [ ] Touch targets adequate
- [ ] Text readable
- [ ] All buttons visible

#### ✅ Scenario 4: Dark Mode
- [ ] Text contrast OK
- [ ] All elements visible
- [ ] Badges readable

#### ✅ Scenario 5: Permissions
- [ ] Non-managers can't create quizzes
- [ ] Users can't edit other orgs' quizzes
- [ ] Students can only view assigned quizzes

---

## 🐛 Troubleshooting

### Quiz doesn't appear in module
**Solution:**
1. Verify quiz was saved successfully
2. Refresh page (F5)
3. Check quiz belongs to same organization

### Can't add answers to question
**Check:**
1. You're in "Add Answer" mode?
2. Filled "Answer Text" field?
3. At least 1 answer marked as correct?

### Score doesn't calculate
**Check:**
1. At least 1 answer marked correct per question?
2. Student submitted (not just exited)?
3. No JavaScript errors (check browser console)

### Student can't take quiz
**Check:**
1. Quiz published in module?
2. Attempt limit not reached?
3. User enrolled in course?
4. No time-based restrictions?

---

## 🎓 Best Practices

### Quiz Design
- ✅ Keep questions concise and clear
- ✅ Avoid trick questions (use for formative only)
- ✅ Provide explanations for learning
- ✅ Match difficulty to module content
- ✅ Test one concept per question

### Question Writing
- ✅ Use active voice
- ✅ Avoid negatives ("Which is NOT...")
- ✅ Keep options similar length
- ✅ Randomize correct answer position
- ✅ Provide clear wrong options

### Assessment Strategy
- ✅ Formative: Low stakes, immediate feedback
- ✅ Exam: Higher stakes, limited feedback
- ✅ Certification: Highest stakes, detailed feedback
- ✅ Allow multiple attempts for learning
- ✅ Set appropriate passing scores (typically 70-80%)

---

## 📈 Analytics & Reporting

### What Gets Tracked
- ✓ Each question answered
- ✓ Correctness of answer
- ✓ Total score in %
- ✓ Pass/fail status
- ✓ Time spent
- ✓ Attempt number
- ✓ Date and time
- ✓ User identity

### Accessing Data
```
Console → Quizzes & Tests → [Quiz] → Attempts Tab
Shows:
- All student attempts
- Scores and times
- Individual responses
- Pass/fail status
```

---

## 🚀 Production Checklist

Before deploying to production:
- [ ] All quiz types tested
- [ ] Sample quizzes created and validated
- [ ] Student flow tested end-to-end
- [ ] Permissions verified
- [ ] Mobile responsiveness confirmed
- [ ] Dark mode working
- [ ] Database queries optimized
- [ ] Error handling in place
- [ ] Documentation complete
- [ ] Stakeholders trained

---

**Version:** 2.0  
**Last Updated:** 2026-07-27  
**Status:** Production Ready ✅
