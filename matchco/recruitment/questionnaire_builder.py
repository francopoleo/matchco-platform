"""Safe building blocks for an AI-assisted organization setup.

The agent-facing operation creates a draft only. Publication remains an
explicit administrative action, which keeps generated configuration auditable.
"""

from django.db import transaction

from .models import QuestionnaireQuestion, QuestionnaireTemplate
from .questionnaire_compliance import MAX_QUESTIONS, validate_question_definition


BASE_QUESTION_SUGGESTIONS = [
    ('experience', 'Você já realizou alguma atividade parecida com esta necessidade?', 'textarea', [], True),
    ('skills', 'Que tipo de tarefa gostaria de fazer nesta oportunidade?', 'textarea', [], True),
    ('availability', 'Qual é sua disponibilidade de dias e horários?', 'textarea', [], False),
    ('start_date', 'Quando você poderia começar?', 'single_choice', ['Imediatamente', 'Em até 15 dias', 'Em até 30 dias', 'A combinar'], False),
]


@transaction.atomic
def create_questionnaire_draft(organization, brief, *, code=None, name=None):
    """Create the next draft version from a structured organization brief.

    ``brief`` may contain ``market``, ``audience_role``, ``purpose``,
    ``questions`` and any other metadata the calling agent wants to retain.
    Custom questions use ``key``, ``label``, ``field_type``, ``options`` and
    ``required``. No existing version is changed or published.
    """
    brief = brief or {}
    code = code or brief.get('code') or 'ai-setup'
    current = QuestionnaireTemplate.objects.filter(organization=organization, code=code).order_by('-version').first()
    version = (current.version + 1) if current else 1
    template = QuestionnaireTemplate.objects.create(
        organization=organization,
        code=code,
        name=name or brief.get('name') or 'Configuração assistida · rascunho',
        description=brief.get('description', 'Rascunho gerado a partir do briefing da organização.'),
        version=version,
        status=QuestionnaireTemplate.STATUS_DRAFT,
        purpose=brief.get('purpose', QuestionnaireTemplate.PURPOSE_RECRUITMENT),
        audience_role=brief.get('audience_role', ''),
        market=brief.get('market', ''),
        source='ai_draft',
        generation_context=brief,
    )
    questions = brief.get('questions') or [
        {'key': key, 'label': label, 'field_type': field_type, 'options': options, 'required': required}
        for key, label, field_type, options, required in BASE_QUESTION_SUGGESTIONS
    ]
    if len(questions) > MAX_QUESTIONS:
        raise ValueError(f'Um questionário prático pode ter no máximo {MAX_QUESTIONS} perguntas.')
    for order, item in enumerate(questions):
        validate_question_definition(
            label=item.get('label', ''),
            field_type=item.get('field_type', 'text'),
        )
        QuestionnaireQuestion.objects.create(
            template=template,
            key=item['key'],
            label=item['label'],
            help_text=item.get('help_text', ''),
            field_type=item.get('field_type', 'text'),
            options=item.get('options', []),
            conditions=item.get('conditions', {}),
            scoring=item.get('scoring', {}),
            required=bool(item.get('required', False)),
            order=order,
        )
    return template
