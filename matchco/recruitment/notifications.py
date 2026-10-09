"""Eventos de notificação da Porta Match.

Cada função abaixo dispara uma mensagem via NotificationPort. O provedor
real (SMS/WhatsApp/e-mail) fica no adapter registrado em
`integrations.registry`. Aqui só o conteúdo canônico.

Ver ROADMAP_CONFORMIDADE Rodada B.
"""
import logging

from .integrations import get_notification_port
from .integrations.contracts import NotificationRequest

logger = logging.getLogger(__name__)


def _send(recipient, subject, body, metadata=None):
    if not recipient:
        return False
    try:
        return get_notification_port().send(NotificationRequest(
            recipient=recipient, subject=subject, body=body,
            metadata=metadata or {},
        ))
    except Exception:
        logger.exception('notification adapter failed for %s', subject)
        return False


def notify_new_opportunity(*, candidate, opportunity):
    """Candidato tem uma nova necessidade compatível no feed."""
    subject = f'Nova oportunidade próxima: {opportunity.title}'
    body = (
        f'Olá, {candidate.first_name}.\n\n'
        f'Uma loja do seu território precisa de alguém para '
        f'{opportunity.job_function.name if opportunity.job_function else opportunity.title}.\n'
        f'Você não precisa se candidatar — só dizer se tem interesse.\n\n'
        f'Ver oportunidade: /candidato/oportunidades/'
    )
    return _send(candidate.email, subject, body,
                 metadata={'kind': 'new_opportunity',
                           'opportunity_id': opportunity.pk})


def notify_match(*, relation):
    """MATCH: interesse dos dois lados. Avisa candidato e (via canal separado) o empregador."""
    candidate = relation.candidate
    opp = relation.opportunity
    subject = f'MATCH — a loja também demonstrou interesse'
    body = (
        f'Olá, {candidate.first_name}.\n\n'
        f'A loja quer conversar sobre "{opp.title}". Quando o contato for '
        f'liberado, você receberá o telefone.\n'
    )
    return _send(candidate.email, subject, body,
                 metadata={'kind': 'match', 'relation_id': str(relation.pk)})


def notify_contact_enabled(*, relation, contact_channel):
    """Contato liberado — envia telefone do outro lado a cada parte."""
    candidate = relation.candidate
    subject = 'Contato liberado — a loja tem seu número.'
    body = (
        f'Olá, {candidate.first_name}.\n\n'
        f'A loja recebeu seu contato. Você deve receber uma mensagem em breve. '
        f'Se preferir, entre em contato direto.\n'
    )
    return _send(candidate.email, subject, body,
                 metadata={'kind': 'contact_enabled', 'relation_id': str(relation.pk)})


def notify_response_sla_pending(*, employer_email, count):
    """Avisa empregador que há Relations MATCHED sem resposta."""
    subject = f'{count} match(es) aguardando sua resposta'
    body = (
        f'Você tem {count} match(es) no MatchCo que ainda não receberam '
        f'resposta. Interesse merece resposta — mesmo que negativa. Sem ela, '
        f'você não pode declarar novas necessidades.\n'
    )
    return _send(employer_email, subject, body,
                 metadata={'kind': 'response_sla', 'count': count})


def notify_certification_expiring(*, candidate, cert_name, valid_until):
    """Avisa candidato 30 dias antes de certificação expirar."""
    subject = f'Sua certificação {cert_name} expira em breve'
    body = (
        f'Olá, {candidate.first_name}.\n\n'
        f'Sua certificação "{cert_name}" vence em {valid_until:%d/%m/%Y}. '
        f'Renove para continuar visível para oportunidades que a exijam.\n'
    )
    return _send(candidate.email, subject, body,
                 metadata={'kind': 'cert_expiring', 'cert': cert_name})


def notify_signal_reconfirm(*, candidate, signal_key, signal_label):
    """Sinal F1/F2 stale — pede reconfirmação ao candidato."""
    subject = 'Confirme sua disponibilidade no MatchCo'
    body = (
        f'Olá, {candidate.first_name}.\n\n'
        f'Faz um tempo que você não confirma "{signal_label}". '
        f'Passe rapidinho para atualizar antes que a próxima oportunidade '
        f'compatível apareça.\n'
    )
    return _send(candidate.email, subject, body,
                 metadata={'kind': 'signal_reconfirm', 'signal': signal_key})
