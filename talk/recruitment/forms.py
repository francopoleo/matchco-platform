from django import forms
from django.utils.translation import gettext_lazy as _

from .models import CandidateProfile, Position, Offer


class CandidateSignupForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'cep', 'address', 'city', 'state',
            'bio', 'experience_years', 'linkedin_url', 'interested_in',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, organization=None, store=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        self.store = store
        if store:
            self.initial['preferred_store'] = store
        for name, field in self.fields.items():
            css = 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} {css}'.strip()

    def clean(self):
        cleaned = super().clean()
        if self.organization and cleaned.get('email'):
            exists = CandidateProfile.objects.filter(
                organization=self.organization,
                email=cleaned['email'],
            ).exists()
            if exists:
                raise forms.ValidationError(
                    _('You are already registered as a candidate for this organization.'),
                )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.organization:
            instance.organization = self.organization
        if commit:
            instance.save()
        return instance


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = [
            'business_unit', 'job_function',
            'title', 'description', 'requirements',
            'cep', 'city', 'state',
            'salary_min', 'salary_max', 'active',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'requirements': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization

        if organization:
            self.fields['business_unit'].queryset = self.fields['business_unit'].queryset.filter(
                company__organization=organization,
                active=True,
            )

        if self.instance.pk and self.instance.business_unit:
            self.fields['job_function'].queryset = self.fields['job_function'].queryset.filter(
                company=self.instance.business_unit.company,
                channels=self.instance.business_unit.channel,
            ).distinct()
        else:
            self.fields['job_function'].queryset = self.fields['job_function'].queryset.none()

    def clean(self):
        cleaned = super().clean()
        business_unit = cleaned.get('business_unit')
        job_function = cleaned.get('job_function')

        if business_unit and job_function:
            if job_function.company != business_unit.company:
                raise forms.ValidationError(
                    _('Job function must belong to the same company as the business unit.')
                )

            if business_unit.channel and job_function.channels.exists():
                if not job_function.channels.filter(pk=business_unit.channel.pk).exists():
                    raise forms.ValidationError(
                        _('Job function "{name}" is not valid for channel "{channel}".').format(
                            name=job_function.name,
                            channel=business_unit.channel.name,
                        )
                    )

        return cleaned


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['position', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['position'].queryset = Position.objects.filter(
                organization=organization,
                active=True,
            )
