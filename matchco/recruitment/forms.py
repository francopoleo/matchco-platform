from django import forms
from django.utils.translation import gettext_lazy as _

from .models import EntryPoint, CanonicalCatalog, CanonicalTerm


# ---------------------------------------------------------------------------
# Porta Match — signup canônico curto (Fase A1)
# ---------------------------------------------------------------------------

from datetime import date
from .models import CandidateConsent


class MatchcoSignupForm(forms.Form):
    """Signup MatchCo — Perfil curto de 6 campos + gate 18+ + consent granular.

    Ver FLUXO_COMPLETO_CLIENTE.md §4.2 e SISTEMA_MATCHCO_CANONICO §2.
    """

    # Identidade mínima
    first_name = forms.CharField(label=_('Nome'), max_length=120)
    last_name = forms.CharField(label=_('Sobrenome'), max_length=120)
    mobile = forms.CharField(
        label=_('Celular (validaremos por SMS)'), max_length=30,
        widget=forms.TextInput(attrs={'placeholder': '(11) 90000-0000'}),
    )
    email = forms.EmailField(label=_('E-mail'))
    birth_date = forms.DateField(
        label=_('Data de nascimento'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    # Os seis do Perfil MatchCo (§4.2 do FLUXO_COMPLETO_CLIENTE)
    where_neighborhoods = forms.CharField(
        label=_('Onde consegue trabalhar — bairros ou região'),
        widget=forms.TextInput(attrs={
            'placeholder': _('Ex: Pinheiros, Vila Madalena, Perdizes'),
        }),
    )
    cep = forms.CharField(
        label=_('CEP de referência da residência'), max_length=9, required=False,
        widget=forms.TextInput(attrs={'inputmode': 'numeric', 'placeholder': '00000-000'}),
    )
    when_days = forms.MultipleChoiceField(
        label=_('Quando — dias disponíveis'),
        choices=[
            ('mon', _('Seg')), ('tue', _('Ter')), ('wed', _('Qua')),
            ('thu', _('Qui')), ('fri', _('Sex')), ('sat', _('Sáb')), ('sun', _('Dom')),
        ],
        widget=forms.CheckboxSelectMultiple,
    )
    when_period = forms.ChoiceField(
        label=_('Turno preferido'),
        choices=[
            ('morning', _('Manhã')), ('afternoon', _('Tarde')),
            ('evening', _('Noite')), ('any', _('Qualquer')),
        ],
    )
    what_function_terms = forms.MultipleChoiceField(
        label=_('O quê gostaria de fazer'),
        required=True,
        choices=(),
        widget=forms.MultipleHiddenInput(),
    )
    interest_mode = forms.ChoiceField(
        label=_('Como você se relaciona com essas funções?'),
        choices=[
            ('want', _('Quero trabalhar com isso')),
            ('learn', _('Tenho interesse em aprender')),
            ('consider', _('Aceito avaliar uma oportunidade')),
        ],
    )
    experience = forms.ChoiceField(
        label=_('Nível de experiência'),
        choices=[
            ('first_job', _('Primeiro emprego')),
            ('some', _('Já trabalhei em algo parecido')),
            ('experienced', _('Tenho experiência na área')),
        ],
    )
    experience_contexts = forms.MultipleChoiceField(
        label=_('Onde você já trabalhou ou teve contato?'),
        required=False,
        choices=[
            ('clothing', _('Loja de roupas')),
            ('shoes', _('Loja de calçados')),
            ('accessories', _('Loja de acessórios')),
            ('home', _('Loja de casa e decoração')),
            ('supermarket', _('Supermercado')),
            ('pharmacy', _('Farmácia')),
            ('food_restaurant', _('Restaurante ou lanchonete')),
            ('food_bakery', _('Padaria ou cafeteria')),
            ('services', _('Serviços ou recepção')),
            ('shopping_operations', _('Operação de shopping')),
            ('other', _('Outro segmento')),
        ],
        widget=forms.MultipleHiddenInput,
    )
    work_format = forms.ChoiceField(
        label=_('Formato'),
        choices=[
            ('fixo', _('Fixo')), ('temporario', _('Temporário')),
            ('ambos', _('Qualquer um')),
        ],
    )
    can_start = forms.DateField(
        label=_('Quando pode começar'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    # Consent granular — o candidato marca escopos de circulação.
    consent_store = forms.BooleanField(
        required=False,
        label=_('Aparecer para a loja que escaneei'),
    )
    consent_shopping = forms.BooleanField(
        required=False,
        label=_('Aparecer para outras lojas do mesmo shopping'),
    )
    consent_network = forms.BooleanField(
        required=False,
        label=_('Aparecer para outras unidades da mesma rede'),
    )
    consent_radius = forms.BooleanField(
        required=False,
        label=_('Aparecer para lojas num raio próximo do meu bairro'),
    )
    consent_transactional = forms.BooleanField(
        required=True,
        label=_('Aceito receber avisos por SMS/e-mail quando surgir oportunidade compatível'),
    )
    accept_privacy = forms.BooleanField(
        required=True,
        label=_('Li e concordo com a Política de Privacidade'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        terms = CanonicalTerm.objects.filter(
            catalog__status=CanonicalCatalog.STATUS_PUBLISHED,
            term_type=CanonicalTerm.TYPE_FUNCTION,
            active=True,
        ).select_related('catalog').prefetch_related('aliases').order_by(
            'catalog__code', '-catalog__version', 'label',
        )
        seen_codes = set()
        choices = []
        self.function_options = []
        for term in terms:
            if term.code in seen_codes:
                continue
            seen_codes.add(term.code)
            choices.append((str(term.pk), term.label))
            self.function_options.append({
                'value': str(term.pk),
                'label': term.label,
                'search': ' '.join([
                    term.label,
                    *(alias.alias for alias in term.aliases.all() if alias.active),
                ]),
            })
        self.fields['what_function_terms'].choices = choices
        self.experience_context_options = [
            {'value': value, 'label': str(label)}
            for value, label in self.fields['experience_contexts'].choices
        ]

    def clean_birth_date(self):
        bd = self.cleaned_data['birth_date']
        today = date.today()
        age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
        if age < 18:
            raise forms.ValidationError(_(
                'Nesta versão da plataforma, apenas maiores de 18 anos criam Perfil.'
            ))
        return bd

    def clean(self):
        cleaned = super().clean()
        # Pelo menos um escopo de circulação é obrigatório — se não, não faz
        # sentido criar o Perfil (o candidato não aparece em lugar nenhum).
        if not any(cleaned.get(k) for k in (
            'consent_store', 'consent_shopping', 'consent_network', 'consent_radius'
        )):
            raise forms.ValidationError(_(
                'Escolha ao menos um escopo para aparecer (loja, shopping, rede ou raio).'
            ))
        return cleaned

    CONSENT_MAP = {
        'consent_store': CandidateConsent.PURPOSE_CIRCULATION_STORE,
        'consent_shopping': CandidateConsent.PURPOSE_CIRCULATION_SHOPPING,
        'consent_network': CandidateConsent.PURPOSE_CIRCULATION_NETWORK,
        'consent_radius': CandidateConsent.PURPOSE_CIRCULATION_RADIUS,
        'consent_transactional': CandidateConsent.PURPOSE_TRANSACTIONAL_MESSAGING,
    }


class EntryPointForm(forms.ModelForm):
    """Editable public-entry configuration, scoped by the console view."""

    class Meta:
        model = EntryPoint
        fields = (
            'label', 'kind', 'scope_store', 'mode', 'experience_template',
            'brand_name', 'brand_logo_url', 'headline', 'subheadline',
            'accent_color', 'purpose', 'audience', 'audience_role',
            'program_name', 'campaign_name', 'channel_name', 'program',
            'participant_free',
        )
        widgets = {'subheadline': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        self.fields['scope_store'].queryset = (
            self.fields['scope_store'].queryset.filter(
                company__organization=organization, active=True,
            ) if organization else self.fields['scope_store'].queryset.none()
        )
        self.fields['program'].queryset = (
            self.fields['program'].queryset.filter(
                organization=organization, status='active',
            ) if organization else self.fields['program'].queryset.none()
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                'class',
                'block w-full rounded-md border border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading',
            )

    def save(self, commit=True):
        entry_point = super().save(commit=False)
        from .territory import configure_entry_point_territory
        configure_entry_point_territory(entry_point, persist=False)
        if commit:
            entry_point.save()
        return entry_point
