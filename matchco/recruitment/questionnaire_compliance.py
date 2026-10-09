"""Commercial guardrails for contextual candidate questions."""

import re

from django.core.exceptions import ValidationError


MAX_QUESTIONS = 6
ALLOWED_FIELD_TYPES = {
    'text', 'textarea', 'single_choice', 'multiple_choice', 'boolean', 'date',
}
FORBIDDEN_TERMS = (
    'escolaridade', 'formação acadêmica', 'formacao academica', 'currículo',
    'curriculo', 'pretensão salarial', 'pretensao salarial', 'salário',
    'salario', 'remuneração', 'remuneracao', 'excel', 'power bi', 'sap',
    'último emprego', 'ultimo emprego', 'tempo de experiência',
    'tempo de experiencia', 'certificação', 'certificacao',
)


def validate_question_definition(*, label, field_type):
    normalized = re.sub(r'\s+', ' ', (label or '').strip().lower())
    if any(term in normalized for term in FORBIDDEN_TERMS):
        raise ValidationError(
            'Use uma pergunta prática ligada à necessidade real; não crie triagem ou currículo.'
        )
    if field_type not in ALLOWED_FIELD_TYPES:
        raise ValidationError(
            'Use texto, escolha, sim/não ou data para perguntas contextuais.'
        )
