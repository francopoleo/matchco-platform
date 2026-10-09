from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordResetForm, UserModel, UserCreationForm, UserChangeForm
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm
from django.contrib.auth import get_user_model

from .models import UserProfile

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    password1 = forms.CharField(
        label=_("Password"),
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )
    email = forms.EmailField(required=False, label=_(''))
    username = forms.EmailField(required=True, label=_('Email'))
    mobile = forms.CharField(required=True, label=_("Mobile"))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if User.USERNAME_FIELD == 'username':
            field = self.fields['username']
            field.regex = r"^[\w.@+-]+$"
            field.help_text = None
            field.error_messages = field.error_messages.copy()
            field.error_messages.update({
                'invalid': _("Adicione um e-mail valido")})

    def save(self):
        res = super(CustomUserCreationForm, self).save()

        if res.email:
            form = PasswordResetForm({'email': res.email})

            assert form.is_valid()
            request = HttpRequest()
            request.META['SERVER_NAME'] = settings.BASE_URL
            request.META['SERVER_PORT'] = settings.SERVER_PORT
            form.save(
                request=request,
                use_https=False,
                from_email=settings.EMAIL_HOST_USER,
                html_email_template_name='registration/password_reset_email.html')
        return res


class CustomUserEditForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User

    first_name = forms.CharField(required=True, label=_('First Name'), disabled=True)
    last_name = forms.CharField(required=True, label=_('Last Name'), disabled=True)
    mobile = forms.CharField(required=True, label=_("Mobile"), disabled=True)
    indication_code = forms.CharField(required=False, label=_("Indication Code"), disabled=True)
    username = forms.EmailField(required=True, label=_('Email'), disabled=True)
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    @property
    def username_field(self):
        return self[User.USERNAME_FIELD]


class UserAvatarForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ('avatar',)
