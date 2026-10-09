"""No-op adapters: recruitment's basic flow does not require other apps."""

from .contracts import AssessmentRequest, AssessmentResult, FileRef, NotificationRequest, PersonRef


class NullIdentityAdapter:
    def resolve_person(self, *, email: str, cpf: str = ''):
        return None

    def register_candidate(self, *, candidate_id: int, email: str):
        return PersonRef(external_id=str(candidate_id), email=email)


class NullAssessmentAdapter:
    def request(self, request: AssessmentRequest):
        return AssessmentResult(assessment_id=request.assessment_id, status='not_configured')


class NullNotificationAdapter:
    def send(self, request: NotificationRequest):
        # Fallback: usa Django e-mail se configurado.
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                subject=request.subject,
                message=request.body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@matchco.example'),
                recipient_list=[request.recipient],
                fail_silently=True,
            )
            return True
        except Exception:
            return False

    def send_sms(self, *, recipient, body):
        """Delega para provider configurado via MATCHCO_SMS_PROVIDER."""
        try:
            from .providers.registry import get_sms_provider
            provider = get_sms_provider()
            if provider is None:
                return False
            return provider.send_sms(recipient=recipient, body=body)
        except Exception:
            return False


class NullFileAdapter:
    def store(self, *, name: str, content_type: str, content: bytes):
        return FileRef(external_id='', name=name, content_type=content_type)

    def delete(self, file_ref: FileRef):
        return False


class NullAIMatchingAdapter:
    def explain(self, *, candidate_id: int, position_id: int, features: dict):
        return {'status': 'not_configured', 'factors': features}
