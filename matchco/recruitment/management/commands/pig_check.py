"""PIG — Privacy Implementation Gate (SISTEMA_MATCHCO_CANONICO §9, §17).

Verifica se todos os pré-requisitos LGPD e operacionais estão prontos.
Retorna exit code 0 = PASS, 1 = FAIL. Serve como gate de deploy.

Uso:
    python manage.py pig_check
    python manage.py pig_check --strict     # falha se qualquer item pendente
"""
from django.conf import settings
from django.core.management.base import BaseCommand


class Check:
    def __init__(self, code, title, ok, detail=''):
        self.code = code
        self.title = title
        self.ok = ok
        self.detail = detail


def _run_checks():
    checks = []

    # 1. DPO identificado
    dpo = getattr(settings, 'MATCHCO_DPO_EMAIL', '')
    checks.append(Check(
        'PIG-01', 'DPO com e-mail válido',
        bool(dpo) and 'example' not in dpo,
        detail=dpo or 'não definido',
    ))

    # 2. Controller nomeado
    ctrl = getattr(settings, 'MATCHCO_CONTROLLER_NAME', '')
    checks.append(Check(
        'PIG-02', 'Nome legal do controlador',
        bool(ctrl) and 'pendente' not in ctrl.lower(),
        detail=ctrl,
    ))

    # 3. Canal de direitos por e-mail (não app)
    rights = getattr(settings, 'MATCHCO_RIGHTS_EMAIL', '')
    checks.append(Check(
        'PIG-03', 'Canal de direitos LGPD por e-mail',
        bool(rights) and 'example' not in rights,
        detail=rights,
    ))

    # 4. Registro de processadores completo
    reg = getattr(settings, 'MATCHCO_PROCESSOR_REGISTER', [])
    pending = [p for p in reg if 'PENDENTE' in str(p.get('dpa_ref', ''))]
    checks.append(Check(
        'PIG-04', 'Registro de processadores completo (DPA)',
        len(reg) > 0 and not pending,
        detail=f'{len(reg)} entradas · {len(pending)} pendentes' if reg else 'vazio',
    ))

    # 5. Ledger append-only ativo (testa que Manager bloqueia UPDATE)
    from recruitment.models import Ledger, LedgerAppendOnlyError
    try:
        Ledger.objects.filter(pk='00000000-0000-0000-0000-000000000000').update(event_type='X')
        checks.append(Check('PIG-05', 'Ledger append-only', False,
                           'UPDATE não foi bloqueado!'))
    except LedgerAppendOnlyError:
        checks.append(Check('PIG-05', 'Ledger append-only', True, 'UPDATE/DELETE bloqueados'))

    # 6. Retenção RT-01..06 executável
    from recruitment.services import apply_retention_policy
    try:
        apply_retention_policy(dry_run=True)
        checks.append(Check('PIG-06', 'RT-01..06 executável', True, 'dry-run ok'))
    except Exception as e:
        checks.append(Check('PIG-06', 'RT-01..06 executável', False, str(e)))

    # 7. Gate de idade 18+ ativo
    from recruitment.services import enforce_age_gate, AgeGateFailure
    from datetime import date, timedelta
    try:
        enforce_age_gate(date.today() - timedelta(days=365 * 10))
        checks.append(Check('PIG-07', 'Gate de idade 18+', False, 'menor passou!'))
    except AgeGateFailure:
        checks.append(Check('PIG-07', 'Gate de idade 18+', True, 'menor bloqueado'))

    # 8. Consent granular disponível
    from recruitment.models import CandidateConsent
    granular = len([
        c for c in CandidateConsent.PURPOSE_CHOICES
        if c[0].startswith('circulation_') or c[0].startswith('visibility_')
    ])
    checks.append(Check(
        'PIG-08', 'Consent granular (circulation + visibility)',
        granular >= 6, detail=f'{granular} purposes granulares',
    ))

    # 9. Página pública de privacidade + direitos + processadores
    from django.urls import reverse, NoReverseMatch
    routes = ['recruitment_public:privacy_policy', 'recruitment_public:privacy_rights',
              'recruitment_public:privacy_processors']
    missing = []
    for r in routes:
        try:
            reverse(r)
        except NoReverseMatch:
            missing.append(r)
    checks.append(Check(
        'PIG-09', 'Páginas públicas de privacidade',
        not missing, detail=(f'faltando: {missing}' if missing else 'ok'),
    ))

    # 10. RC-01..05 obrigatório no encerramento (código do model)
    from recruitment.models import ResponseClass
    checks.append(Check(
        'PIG-10', 'RC-01..05 codificado',
        len(ResponseClass.ALL) == 5,
    ))

    # 11. PIAG: todos EntryPoint ACTIVE têm HTTPS e activation_tested_at
    from recruitment.models import EntryPoint
    bad = [
        ep for ep in EntryPoint.objects.filter(state=EntryPoint.STATE_ACTIVE)
        if not ep.can_activate()
    ]
    checks.append(Check(
        'PIG-11 (PIAG)', 'EntryPoints ACTIVE atendem PIAG mínimo',
        not bad, detail=f'{len(bad)} EntryPoints ACTIVE com PIAG quebrado',
    ))

    return checks


class Command(BaseCommand):
    help = 'PIG — Privacy Implementation Gate. Verifica LGPD e operacional.'

    def add_arguments(self, parser):
        parser.add_argument('--strict', action='store_true',
                          help='Exit 1 se qualquer item falhar')

    def handle(self, *args, **opts):
        checks = _run_checks()
        passed = 0
        failed = 0
        for c in checks:
            if c.ok:
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ {c.code}  {c.title}  · {c.detail}'
                ))
                passed += 1
            else:
                self.stdout.write(self.style.ERROR(
                    f'  ✗ {c.code}  {c.title}  · {c.detail}'
                ))
                failed += 1

        self.stdout.write('')
        if failed == 0:
            self.stdout.write(self.style.SUCCESS(
                f'PIG PASS · {passed}/{len(checks)} ok'
            ))
            return
        summary = self.style.ERROR(
            f'PIG FAIL · {failed} pendências, {passed} ok'
        )
        self.stdout.write(summary)
        if opts['strict']:
            raise SystemExit(1)
