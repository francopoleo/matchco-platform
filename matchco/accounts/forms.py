from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from user_management.models import InvitationCode

UserModel = get_user_model()


class UserSignupCreationForm(UserCreationForm):
    class Meta:
        model = UserModel
        fields = ('username', 'first_name', 'last_name', 'mobile', 'password1', 'password2')

    indication_code = forms.CharField(required=True, label=_('Invitation code'))

    def clean_indication_code(self):
        value = self.cleaned_data['indication_code'].strip().upper()
        invitation = InvitationCode.objects.filter(code__iexact=value).select_related('organization').first()
        if not invitation or not invitation.available:
            raise ValidationError(_('Código de indicação inválido, expirado ou já utilizado.'))
        self.invitation_code = invitation
        return invitation.code
