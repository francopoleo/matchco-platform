from django.urls import reverse_lazy, reverse
from django.views import generic
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ImproperlyConfigured
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView, View
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django_ratelimit.decorators import ratelimit

from .forms import UserSignupCreationForm
from gamification.utils import create_gamification_report_item
from gamification.models import GamificationReport
from user_management.models import RegistrationRequest, User
from configuration.models import Organization, Membership
from .emailing import send_registration_emails
from .captcha_utils import verify_recaptcha_v3
from cep.core.utils import get_tenant_user


class SignUpView(SuccessMessageMixin, generic.CreateView):
    form_class = UserSignupCreationForm
    success_url = reverse_lazy('registration_pending')
    template_name = 'registration/signup.html'
    success_message = _("User created with success")
    redirect_authenticated_user = False

    @transaction.atomic
    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.indication_code = form.cleaned_data['indication_code']
        user.save()
        registration = RegistrationRequest.objects.create(user=user, invitation_code=form.invitation_code)
        send_registration_emails(registration)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        if not self.success_url:
            raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")
        return str(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        res = super(SignUpView, self).dispatch(request, *args, **kwargs)
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            redirect_to = self.get_success_url()
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your LOGIN_REDIRECT_URL doesn't point to a login page."
                )
            return HttpResponseRedirect(redirect_to)
        return res


@method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True), name='dispatch')
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        res = super(CustomLoginView, self).form_valid(form)
        user = form.get_user() or self.request.user
        event = 'login'
        try:
            if self.is_first_login(user, event) is False:
                create_gamification_report_item(user, event)
        except Exception:
            # Gamification not available in shared schema, skip
            pass

        return res

    def is_first_login(self, user, event):
        try:
            tenant_user = get_tenant_user(user)
            if not tenant_user:
                return True
            gr = GamificationReport.objects.filter(type_event=event, user=tenant_user)
            return True if gr else False
        except Exception:
            return True


class PublicLandingView(TemplateView):
    template_name = 'registration/landing.html'


class RecruitmentLandingView(TemplateView):
    template_name = 'registration/recruitment.html'


class RegistrationPendingView(TemplateView):
    template_name = 'registration/pending.html'


@method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True), name='dispatch')
class PublicSignupView(TemplateView):
    """
    Public signup for external users (candidates, doctors, partners, students).
    Creates User + Auto Membership in public organization.
    """
    template_name = 'public/signup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.kwargs.get('category', self.request.GET.get('category', 'candidates'))

        org_map = {
            'candidates': 'public-candidates',
            'doctors': 'public-doctors',
            'partners': 'public-partners',
            'students': 'public-students',
        }

        context['category'] = category
        context['org_slug'] = org_map.get(category, 'public-candidates')
        context['recaptcha_public_key'] = settings.RECAPTCHA_PUBLIC_KEY

        try:
            org = Organization.objects.get(slug=context['org_slug'])
            context['organization'] = org
            context['page_title'] = f'Join {org.name}'
        except Organization.DoesNotExist:
            context['error'] = 'Organization not found'

        return context

    def post(self, request, *args, **kwargs):
        category = self.kwargs.get('category', request.POST.get('category', 'candidates'))
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        captcha_token = request.POST.get('g-recaptcha-response', '')

        errors = []

        # Verify CAPTCHA first (before other validations)
        if settings.RECAPTCHA_PRIVATE_KEY:
            is_valid, score = verify_recaptcha_v3(captcha_token, action='signup')
            if not is_valid:
                errors.append('Validação de segurança falhou. Por favor tente novamente.')

        if not email or '@' not in email:
            errors.append('Email válido é necessário')

        if len(password) < 8:
            errors.append('Senha deve ter no mínimo 8 caracteres')

        if password != password_confirm:
            errors.append('Senhas não conferem')

        if User.objects.filter(email=email).exists():
            errors.append('Email já registrado')

        if errors:
            return render(request, self.template_name, {
                'errors': errors,
                'category': category,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            }, status=400)

        org_map = {
            'candidates': 'public-candidates',
            'doctors': 'public-doctors',
            'partners': 'public-partners',
            'students': 'public-students',
        }

        try:
            with transaction.atomic():
                username = self._generate_username(email)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=False,
                )

                org = Organization.objects.get(slug=org_map.get(category))
                membership = Membership.objects.create(
                    user=user,
                    organization=org,
                    company=None,
                    role='viewer',
                    active=False,
                    is_primary=True,
                    created_by=None,
                )

                self._send_confirmation_email(user, category)

                return redirect('public-signup-confirmation', category=category)

        except Organization.DoesNotExist:
            errors.append('Organização não encontrada')
            return render(request, self.template_name, {'errors': errors}, status=400)
        except Exception as e:
            errors.append(f'Erro ao registrar: {str(e)}')
            return render(request, self.template_name, {'errors': errors}, status=400)

    def _generate_username(self, email):
        base_username = email.split('@')[0]
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username

    def _send_confirmation_email(self, user, category):
        token = default_token_generator.make_token(user)

        confirmation_url = self.request.build_absolute_uri(
            reverse('public-confirm-email', kwargs={
                'category': category,
                'uid': user.pk,
                'token': token,
            })
        )

        subject = f'Confirme seu email - {category.title()}'
        message = f'''
        Olá {user.first_name or user.username},

        Clique no link abaixo para confirmar seu email e ativar sua conta:
        {confirmation_url}

        Este link expira em 24 horas.

        Att,
        Talk Platform
        '''

        try:
            send_mail(
                subject,
                message,
                'noreply@talk.local',
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't block signup
            import sys
            print(f"Warning: Email failed to send: {e}", file=sys.stderr)
            pass


class PublicConfirmEmailView(View):
    """Confirm email and activate user + membership"""

    def get(self, request, *args, **kwargs):
        uid = kwargs.get('uid')
        token = kwargs.get('token')
        category = kwargs.get('category', 'candidates')

        try:
            user = User.objects.get(pk=uid)

            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()

                org_map = {
                    'candidates': 'public-candidates',
                    'doctors': 'public-doctors',
                    'partners': 'public-partners',
                    'students': 'public-students',
                }

                membership = user.memberships.get(organization__slug=org_map.get(category))
                membership.active = True
                membership.save()

                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)

                return redirect('home')
            else:
                return render(request, 'public/confirm_email.html', {
                    'error': 'Link inválido ou expirado'
                }, status=400)

        except User.DoesNotExist:
            return render(request, 'public/confirm_email.html', {
                'error': 'Usuário não encontrado'
            }, status=404)
        except Membership.DoesNotExist:
            return render(request, 'public/confirm_email.html', {
                'error': 'Membership não encontrada'
            }, status=404)


class PublicSignupConfirmationView(TemplateView):
    """Show confirmation sent page"""
    template_name = 'public/signup_confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = kwargs.get('category', 'candidates')
        return context
