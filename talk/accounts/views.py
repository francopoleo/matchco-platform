from django.urls import reverse_lazy
from django.views import generic
from django.http import HttpResponseRedirect
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ImproperlyConfigured
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from .forms import UserSignupCreationForm
from gamification.utils import create_gamification_report_item
from gamification.models import GamificationReport
from user_management.models import RegistrationRequest
from .emailing import send_registration_emails


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


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        res = super(CustomLoginView, self).form_valid(form)
        user = form.get_user() or self.request.user
        event = 'login'
        if self.is_first_login(user, event) is False:
            create_gamification_report_item(user, event)
        
        return res

    def is_first_login(self, user, event):
        gr = GamificationReport.objects.filter(type_event=event, user=user)

        return True if gr else False


class PublicLandingView(TemplateView):
    template_name = 'registration/landing.html'


class RegistrationPendingView(TemplateView):
    template_name = 'registration/pending.html'
