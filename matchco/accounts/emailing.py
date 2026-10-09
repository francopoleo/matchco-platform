import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_registration_emails(registration):
    user = registration.user
    invitation = registration.invitation_code
    try:
        send_mail(
            'Recebemos sua solicitação de acesso ao MatchCo',
            f'Olá, {user.first_name or user.username}.\n\nRecebemos sua solicitação para acessar o ambiente {invitation.organization.name}. Um gestor irá conferir seus dados e liberar o acesso.\n\nVocê receberá uma nova mensagem quando a análise for concluída.',
            settings.MATCHCO_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
        if settings.REGISTRATION_REVIEW_EMAIL:
            send_mail(
                f'Nova solicitação de acesso · {invitation.organization.name}',
                f'Usuário: {user.get_full_name() or user.username}\nE-mail: {user.email}\nCódigo: {invitation.code}\nOrganização: {invitation.organization.name}',
                settings.MATCHCO_FROM_EMAIL,
                [settings.REGISTRATION_REVIEW_EMAIL],
                fail_silently=True,
            )
    except Exception:
        logger.exception('Could not send registration emails for request %s', registration.pk)


def send_registration_decision_email(registration):
    user = registration.user
    approved = registration.status == registration.APPROVED
    subject = 'Seu acesso ao MatchCo foi aprovado' if approved else 'Atualização da sua solicitação de acesso ao MatchCo'
    message = (
        f'Olá, {user.first_name or user.username}.\n\n'
        + ('Seu acesso foi aprovado. Você já pode entrar no MatchCo com seu e-mail e senha.' if approved else 'Sua solicitação de acesso não foi aprovada neste momento. Entre em contato com a organização que enviou o código para obter mais informações.')
    )
    send_mail(subject, message, settings.MATCHCO_FROM_EMAIL, [user.email], fail_silently=True)
