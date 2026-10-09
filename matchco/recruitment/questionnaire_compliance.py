"""--- Phase 5: Question Compliance Validation ---

Validates questionnaire questions against whitelist of allowed topics
to prevent screening-type questions (education, salary, age, etc.)
and ensure focus on practical job-related skills.

Reference: SISTEMA_MATCHCO_CANONICO §3.11 (Compliance)
"""

import re
from typing import Dict, List, Optional

MAX_QUESTIONS = 6

# --- WHITELIST: Topics we allow ---
ALLOWED_TOPIC_PATTERNS = [
    # Availability & Schedule
    r'(disponibilidade|horário|turno|início|data|quando|hours?|schedule)',
    r'(noturno|diurno|integral|part.?time|tempo integral|período)',

    # Experience & Skills
    r'(experiência|experiencia|skills?|habilidade|competência|competencia)',
    r'(trabalhou|trabalhar|atuou|atuação|prática|pratico|conhecimento)',
    r'(sistema|software|ferramenta|tool|máquina|maquina|equipamento)',

    # Practical Knowledge
    r'(caixa|point.?of.?sale|pdv|pos|register|registrador)',
    r'(reposição|reposicao|estoque|inventory|armazem|warehouse)',
    r'(vendas?|sales?|atendimento|atender|customer|cliente)',
    r'(limpeza|cleaning|organização|organizacao|organizado)',
    r'(segurança|seguranca|safety|safety.?procedures)',

    # Personal Qualities (only practical ones)
    r'(comunicação|comunicacao|comunicar|falar|speaking)',
    r'(pontualidade|pontuali|on.?time|arrive)',
    r'(responsável|responsavel|reliability|confiável|confiavel)',
    r'(trabalho em equipe|team.?work|teamwork|cooperação|cooperacao)',

    # Transport & Mobility
    r'(transporte|transport|carro|car|motorcycle|moto|bike)',
    r'(habilitação|habilitacao|cnh|driving|license|carteira)',
    r'(mobilidade|mobility|deslocamento)',

    # Certifications (practical only)
    r'(certificado|certificate|curso|course|treinamento|training)',
    r'(primeiros.?socorros|first.?aid|cpr)',
]

# --- BLACKLIST: Topics we explicitly forbid ---
FORBIDDEN_TOPIC_PATTERNS = [
    # Age & Birth
    r'(idade|age|nascimento|date.?of.?birth|data de nascimento)',
    r'(nasceu|born|birthday|aniversário|aniversario)',

    # Education Level (screening indicator)
    r'(escolaridade|education|school|escola|ensino|fundamental|médio|medio)',
    r'(superior|universit|college|formação|formacao|grau|degree)',
    r'(diploma|enem|vestibular|profissional)',

    # Religion & Belief
    r'(religião|religiao|religioso|crença|crenca|fé|fe|deus|god)',
    r'(spiritual|faith)',

    # Sexual Orientation & Gender Identity
    r'(orientação sexual|genero|gender|lgbtq|lgbtqia)',

    # Marital & Family Status
    r'(casado|married|solteiro|single|divorciado|divorced)',
    r'(filhos?|children|family|familiar|paternidade|maternity)',
    r'(cônjuge|conjuge|spouse)',

    # Political Opinion
    r'(política|political|voto|vote|partido|party|ideologia|ideology)',

    # Salary & Financial
    r'(salário|salary|wage|remuneração|remuneracao|ganho|income)',
    r'(benefício|beneficio|vale|voucher|auxílio|auxilio)',

    # Health & Disability
    r'(saúde|saude|health|doença|doenca|médic|medic|deficiência|deficiencia)',
    r'(alergia|allergy|medicament|medicação|medicacao)',

    # Race & Ethnicity
    r'(raça|raca|race|etnia|ethnic|cor|color|origens?|origins?)',

    # Criminal Record
    r'(criminal|crime|antecedente|convict|preso|prison)',

    # Personal Appearance
    r'(altura|height|peso|weight|aparência|aparencia|tatuagem|tatuage)',
    r'(piercing|cabelo|hair|físico|fisico|beleza|beauty)',

    # Lifestyle Choices
    r'(bebida|drink|álcool|alcohol|fumo|smoking|droga|drug)',
    r'(convicção|conviccao|moral|valores|values)',

    # Genetic Information
    r'(genético|genetic|dna|gene)',
]


def check_question_compliance(label: str, field_type: str) -> Dict:
    """Check if a question complies with whitelist.

    Args:
        label: Question text
        field_type: Type of question (text, boolean, etc.)

    Returns:
        Dict with compliance status
    """
    label_lower = label.lower()

    # Check forbidden first (hard stop)
    for pattern in FORBIDDEN_TOPIC_PATTERNS:
        if re.search(pattern, label_lower, re.IGNORECASE):
            return {
                'compliant': False,
                'risk_level': 'forbidden',
                'reason': f'Pergunta violates compliance policy: possível discriminação',
                'requires_ops_approval': True,
            }

    # Check if matches allowed list
    matches_allowed = any(
        re.search(pattern, label_lower, re.IGNORECASE)
        for pattern in ALLOWED_TOPIC_PATTERNS
    )

    if not matches_allowed:
        # Doesn't match allowed list - requires ops review
        return {
            'compliant': False,
            'risk_level': 'medium',
            'reason': 'Pergunta não reconhecida na lista padrão - requer aprovação operacional',
            'requires_ops_approval': True,
        }

    # Matched allowed list - approved
    return {
        'compliant': True,
        'risk_level': 'low',
        'reason': '',
        'requires_ops_approval': False,
    }


def validate_question_definition(label: str, field_type: str) -> None:
    """Validate question definition (existing function, kept for compatibility)."""
    if not label or len(label.strip()) == 0:
        raise ValueError('Pergunta não pode estar vazia')

    if len(label) > 240:
        raise ValueError('Pergunta muito longa (máximo 240 caracteres)')

    if field_type not in [
        'text', 'textarea', 'single_choice', 'multiple_choice',
        'boolean', 'number', 'date', 'file', 'scale'
    ]:
        raise ValueError(f'Tipo de pergunta inválido: {field_type}')


def get_compliance_warnings(label: str) -> List[str]:
    """Get all compliance warnings for a question (for admin UI)."""
    warnings = []
    label_lower = label.lower()

    # Check for suspicious patterns
    suspicious_patterns = {
        r'(formação|formacao|education)': 'Menção a educação/formação - revisar se é screening',
        r'(salary|salário|salario)': 'Pergunta sobre salário - não permitido',
        r'(age|idade)': 'Pergunta sobre idade - não permitido',
        r'(casad|married|solteiro)': 'Pergunta sobre estado civil - não permitido',
    }

    for pattern, warning_msg in suspicious_patterns.items():
        if re.search(pattern, label_lower, re.IGNORECASE):
            warnings.append(warning_msg)

    # Check for vague questions
    if len(label.split()) < 3:
        warnings.append('Pergunta muito curta - considere ser mais específico')

    if '?' not in label:
        warnings.append('Pergunta não termina com "?" - revisar formato')

    return warnings


def audit_question_change(
    question,
    action: str,
    user,
    old_value: Optional[Dict] = None,
    new_value: Optional[Dict] = None,
    change_reason: str = '',
) -> None:
    """Log a question change to audit trail."""
    from .models import QuestionAuditLog

    # Determine if change is compliance-flagged
    compliance_flag = False
    compliance_reason = ''

    if action in ['created', 'updated'] and new_value:
        label = new_value.get('label', '')
        compliance_result = check_question_compliance(label, new_value.get('field_type', 'text'))
        if compliance_result['requires_ops_approval']:
            compliance_flag = True
            compliance_reason = compliance_result['reason']

    QuestionAuditLog.objects.create(
        question=question,
        action=action,
        user=user,
        organization=question.template.organization,
        old_value=old_value or {},
        new_value=new_value or {},
        change_reason=change_reason,
        compliance_flag=compliance_flag,
        compliance_flag_reason=compliance_reason,
    )
