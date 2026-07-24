from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

UserModel = get_user_model()


class UserSignupCreationForm(UserCreationForm):
    class Meta:
        model = UserModel
        fields = ('username', 'first_name', 'last_name', 'mobile', 'password1', 'password2')

    indication_code = forms.CharField(required=False, label=_('Invitation code'))
