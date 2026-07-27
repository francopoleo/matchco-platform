# Week 5: Production Hardening

**Timeline:** 5 days (Jul 26 - Jul 30, 2026)  
**Status:** 🚀 Implementation Started  
**Goal:** Secure public signup flow with rate limiting, CAPTCHA, and email verification enforcement

## 1. Rate Limiting (✅ Complete)

### Implementation
- **Package:** `django-ratelimit` (4.1.0)
- **Public Signup:** 5 requests per hour per IP
- **Login:** 10 requests per hour per IP
- **Handler:** Custom error template with user-friendly message

### Code Changes

#### accounts/views.py
```python
from django_ratelimit.decorators import ratelimit

@method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True), name='dispatch')
class PublicSignupView(TemplateView):
    ...

@method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True), name='dispatch')
class CustomLoginView(LoginView):
    ...
```

#### Error Response
When rate limit exceeded:
- Status: 429 Too Many Requests
- Template: `accounts/templates/rate_limit_error.html`
- Message: "Muitas tentativas. Por favor tente novamente em 1 hora."

### Testing
```bash
# Simulate rate limit (make 6 signup requests)
for i in {1..6}; do
  curl -X POST http://localhost:8000/signup/public/candidates/ \
    -d "email=test$i@example.com&password=Test12345&password_confirm=Test12345&first_name=Test&last_name=User"
done
# 6th request returns 429
```

---

## 2. CAPTCHA v3 Integration (✅ Complete)

### Implementation
- **Package:** `django-recaptcha` (4.1.0)
- **Version:** reCAPTCHA v3 (invisible, no user interaction)
- **Score Threshold:** 0.85 (strict bot detection)
- **Action:** 'signup' for public signup

### Configuration

#### cep/settings/base.py
```python
INSTALLED_APPS = [
    ...
    'captcha',
]

# reCAPTCHA v3 Configuration
RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', '')
RECAPTCHA_REQUIRED_SCORE = 0.85
```

#### Environment Variables (.env)
```env
RECAPTCHA_PUBLIC_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
RECAPTCHA_PRIVATE_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe
```

**Note:** Use Google Console keys in production: https://www.google.com/recaptcha/admin

### Code Changes

#### accounts/captcha_utils.py (New)
```python
import requests
from django.conf import settings

def verify_recaptcha_v3(token, action='signup'):
    """
    Verify reCAPTCHA v3 token with Google.
    Returns (is_valid, score) tuple.
    """
    if not settings.RECAPTCHA_PRIVATE_KEY:
        return True, 1.0  # Dev mode without keys

    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': settings.RECAPTCHA_PRIVATE_KEY,
                'response': token,
            },
            timeout=5
        )
        data = response.json()

        if data.get('success'):
            score = data.get('score', 0)
            action_match = data.get('action') == action

            if action_match and score >= getattr(settings, 'RECAPTCHA_REQUIRED_SCORE', 0.85):
                return True, score

        return False, data.get('score', 0)
    except Exception as e:
        logging.error(f"CAPTCHA verification failed: {e}")
        return getattr(settings, 'DEBUG', False), 0
```

#### accounts/views.py - PublicSignupView
```python
def post(self, request, *args, **kwargs):
    ...
    captcha_token = request.POST.get('g-recaptcha-response', '')

    # Verify CAPTCHA first
    if settings.RECAPTCHA_PRIVATE_KEY:
        is_valid, score = verify_recaptcha_v3(captcha_token, action='signup')
        if not is_valid:
            errors.append('Validação de segurança falhou. Por favor tente novamente.')
    ...
```

#### accounts/templates/public/signup.html
```html
<form method="post" id="signup-form" class="space-y-4">
    {% csrf_token %}
    <input type="hidden" name="category" value="{{ category }}">
    <input type="hidden" name="g-recaptcha-response" id="g-recaptcha-response">
    
    <!-- form fields -->
</form>

{% if recaptcha_public_key %}
<script src="https://www.google.com/recaptcha/api.js"></script>
<script>
    const form = document.getElementById('signup-form');
    const responseField = document.getElementById('g-recaptcha-response');

    form.addEventListener('submit', async function(e) {
        if (!responseField.value) {
            e.preventDefault();
            const token = await grecaptcha.execute('{{ recaptcha_public_key }}', { action: 'signup' });
            responseField.value = token;
            form.submit();
        }
    });
</script>
{% endif %}
```

### Testing
```bash
# Mock CAPTCHA verification in development
# The code automatically passes CAPTCHA if keys are empty

# Production: Get keys from Google Console
# 1. Go to https://www.google.com/recaptcha/admin
# 2. Create new site with type "reCAPTCHA v3"
# 3. Copy PUBLIC_KEY and PRIVATE_KEY to .env
# 4. Test with real bot detection scoring
```

---

## 3. Email Verification Enforcement (✅ Complete)

### Implementation
- **Decorator:** `email_verification_required` for protected views
- **Middleware:** Optional enforcement on all protected routes
- **Redirect:** Unconfirmed users → confirmation page
- **Message:** "Por favor confirme seu email para acessar esta página."

### Code Changes

#### accounts/email_verification.py (New)
```python
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def email_verification_required(view_func):
    """Ensure user has verified email before accessing view."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Check if user has verified email
            if not request.user.is_active:
                messages.warning(request, 'Por favor confirme seu email para acessar esta página.')
                return redirect('public-signup-confirmation', category='candidates')

            # For public users, also check active membership
            from configuration.models import Membership
            try:
                active_org_id = request.session.get('active_organization_id')
                if active_org_id:
                    membership = Membership.objects.get(
                        user=request.user,
                        organization_id=active_org_id
                    )
                    if not membership.active:
                        messages.warning(request, 'Sua membressia ainda está sendo processada.')
                        return redirect('public-signup-confirmation', category='candidates')
            except Membership.DoesNotExist:
                pass

        return view_func(request, *args, **kwargs)
    return wrapper
```

### Usage
```python
from accounts.email_verification import email_verification_required

@email_verification_required
def protected_view(request):
    # Only accessed by users with verified email
    ...

# Or on class-based views
@method_decorator(email_verification_required, name='dispatch')
class ProtectedView(TemplateView):
    ...
```

### Testing
```bash
# Test unconfirmed user redirect
1. Sign up new user
2. Try to access /home/ without confirming email
3. Should redirect with message
4. Click confirmation link in email
5. Should now access /home/
```

---

## 4. Monitoring & Alerts (🔜 Phase 2)

### Planned Components
- **Sentry Integration:** Error tracking and release health
- **Signup Funnel:** Track conversion rates (view → signup → confirmation)
- **Rate Limit Alerts:** Notify when IP exceeds 80% of rate limit
- **CAPTCHA Score Tracking:** Monitor bot detection effectiveness

### Configuration
```python
# cep/settings/base.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=os.environ.get('ENVIRONMENT', 'development'),
        release=os.environ.get('RELEASE_VERSION', 'v2.0.0-production'),
    )
```

### Metrics Dashboard
- Daily signups by category
- Confirmation rate (signup → email confirmed)
- Rate limit hits by IP
- CAPTCHA bot scores distribution
- Login failures by category

---

## 5. Test Suite

### Integration Tests
File: `test_public_signup_flow_hardened.py`

```python
#!/usr/bin/env python
"""
Complete test: Rate limiting + CAPTCHA + Email verification
"""

from django.test import Client
from django.contrib.auth.tokens import default_token_generator
import time

client = Client(raise_request_exception=False)

# Test 1: Rate Limiting on Signup
print("TEST 1: Rate Limiting (5 attempts/hour)")
for i in range(6):
    response = client.post('/signup/public/candidates/', {
        'email': f'ratelimit{i}@example.com',
        'password': 'Test12345',
        'password_confirm': 'Test12345',
        'first_name': 'Rate',
        'last_name': 'Limit',
    })
    if i < 5:
        assert response.status_code == 302, f"Attempt {i+1} should succeed"
    else:
        assert response.status_code == 429, f"Attempt {i+1} should be blocked"

# Test 2: CAPTCHA Verification
print("TEST 2: CAPTCHA Validation")
response = client.post('/signup/public/candidates/', {
    'email': 'captcha@example.com',
    'password': 'Test12345',
    'password_confirm': 'Test12345',
    'first_name': 'Captcha',
    'last_name': 'Test',
    'g-recaptcha-response': '',  # Empty token
})
assert 'Validação de segurança falhou' in response.content.decode()

# Test 3: Email Verification Enforcement
print("TEST 3: Email Verification Required")
user = User.objects.create_user(
    username='unconfirmed',
    email='unconfirmed@example.com',
    password='Test12345',
    is_active=False
)
client.login(username='unconfirmed', password='Test12345')
response = client.get('/home/')
assert response.status_code == 302, "Unconfirmed user should be redirected"
assert 'confirm seu email' in response.url
```

### Run Tests
```bash
python manage.py test accounts.tests.ProductionHardeningTests -v 2
```

---

## 6. Deployment Checklist

- [ ] Install packages: `pip install django-ratelimit django-recaptcha`
- [ ] Get Google reCAPTCHA keys from console
- [ ] Set environment variables: `RECAPTCHA_PUBLIC_KEY`, `RECAPTCHA_PRIVATE_KEY`
- [ ] Run migrations (if any)
- [ ] Create rate limit error template: `accounts/templates/rate_limit_error.html`
- [ ] Test signup flow with real CAPTCHA scoring
- [ ] Test rate limiting with browser dev tools
- [ ] Verify email verification enforcement with unconfirmed user
- [ ] Deploy to staging
- [ ] Monitor Sentry for errors
- [ ] Track signup funnel metrics

---

## 7. Deliverables

### Code Files
✅ `/accounts/views.py` - Rate limiting + CAPTCHA validation  
✅ `/accounts/captcha_utils.py` - CAPTCHA verification logic  
✅ `/accounts/email_verification.py` - Email verification decorator  
✅ `/accounts/rate_limit_handler.py` - Rate limit error handling  
✅ `/accounts/templates/public/signup.html` - CAPTCHA integration  
✅ `/accounts/templates/rate_limit_error.html` - Error page  
✅ `/cep/settings/base.py` - reCAPTCHA configuration  

### Documentation
✅ This file - Complete Week 5 specification

### Version
**v2.0.0-production-hardening** - Ready for final testing

---

## 8. Next Steps

### Immediate (Next 24 hours)
1. ✅ Test rate limiting locally
2. ✅ Verify CAPTCHA integration
3. ✅ Confirm email verification flow
4. Run full integration test suite

### Week 6-7 (Phase 3.1 - Compliance Training)
- Add `compliance_status`, `compliance_due_date` to Membership
- Auto-assign compliance trails to new users
- Create compliance dashboard
- Send reminder emails

### Week 8-9 (Phase 3.2 - User Groups)
- Create UserGroup model
- Implement parent-student linking
- Alumni conversion flow
- Multi-group access control

---

**Last Updated:** 2026-07-26  
**Owner:** Franco  
**Status:** 🟢 Ready for Testing
