from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from configuration.models import Membership


class Command(BaseCommand):
    help = 'Send email reminders for overdue or soon-due compliance training'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days ahead to consider "due soon" (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what emails would be sent without sending'
        )

    def handle(self, *args, **options):
        days_threshold = options.get('days', 7)
        dry_run = options.get('dry_run', False)

        self.send_compliance_reminders(days_threshold, dry_run)

    def send_compliance_reminders(self, days_threshold, dry_run):
        """Send email reminders for overdue or soon-due compliance training"""

        due_soon_date = timezone.now() + timedelta(days=days_threshold)

        memberships = Membership.objects.filter(
            compliance_status__in=['pending', 'in_progress'],
            compliance_due_date__lte=due_soon_date,
        ).select_related('user', 'organization')

        sent_count = 0
        overdue_count = 0

        for membership in memberships:
            days_remaining = (
                membership.compliance_due_date - timezone.now()
            ).days

            if days_remaining < 0:
                status = 'VENCIDO'
                days_text = f'{abs(days_remaining)} dias atrás'
                overdue_count += 1
                membership.compliance_status = 'overdue'
            else:
                status = f'VENCE EM {days_remaining} DIAS'
                days_text = f'{days_remaining} dias'

            user_name = membership.user.first_name or membership.user.username

            subject = f'Treinamento de Conformidade Necessário: {status}'
            message = f'''Olá {user_name},

Você tem treinamentos de conformidade pendentes na plataforma MatchCo.

Organização: {membership.organization.name}
Status: {status}
Prazo: {membership.compliance_due_date.strftime("%d/%m/%Y às %H:%M")}
Tempo restante: {days_text}

Por favor, acesse o sistema e complete os treinamentos necessários o quanto antes.

A falha em completar o treinamento de conformidade dentro do prazo pode resultar em restrição de acesso.

Atenciosamente,
MatchCo Platform
compliance@matchco.local
'''

            if not dry_run:
                try:
                    send_mail(
                        subject,
                        message,
                        'noreply@matchco.local',
                        [membership.user.email],
                        fail_silently=False,
                    )

                    membership.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Email sent to {membership.user.email} '
                            f'({membership.organization.name}) - {status}'
                        )
                    )

                    sent_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Failed to send email to {membership.user.email}: {str(e)}'
                        )
                    )
            else:
                self.stdout.write(
                    f'[DRY-RUN] Would send email to {membership.user.email} '
                    f'({membership.organization.name}) - {status}'
                )
                sent_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Summary:\n'
                f'  • Emails sent/simulated: {sent_count}\n'
                f'  • Marked as overdue: {overdue_count}'
            )
        )
