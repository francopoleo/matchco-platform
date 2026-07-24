from django import forms

from .models import BusinessUnit


class BusinessUnitModelAdminForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        fields = '__all__'
