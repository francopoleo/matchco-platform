# MatchCo — Arquitetura SaaS

Estratégia de domínios, roteamento e deploy para o produto MatchCo.

Última revisão: 2026-09-30.

---

## 1. Princípio: separar marketing do app

**Nunca misture** site institucional com o app. Motivos:

- **Vulnerabilidade**: o app tem CSRF, sessão, LGPD. O site tem SEO, cache
  agressivo, CDN. Ficam em domínios diferentes com políticas diferentes.
- **Deploy independente**: marketing muda toda semana; app tem gate de PIG.
- **SEO**: o Google não deve indexar `/login/` nem `/entrar/`.
- **Comunicação**: `matchco.com/politica-de-privacidade/` é institucional
  (uma para todos); `app.matchco.com/privacidade/` é técnico-legal do produto.

---

## 2. Mapa de domínios

| Domínio | O que serve | Onde hospeda | Público-alvo |
|---|---|---|---|
| `matchco.com` | Site institucional, blog, pricing, cases | Vercel / Webflow / Framer | Prospects, imprensa |
| `www.matchco.com` | Redirect 301 para apex | — | — |
| **`app.matchco.com`** | **O SaaS Django** | GCP/AWS/Fly.io | Candidatos, lojistas, sponsors |
| `qr.matchco.com` | Encurtador de QR (opcional) | Cloudflare Worker | Redireciona pra `/qr/<uuid>/` |
| `docs.matchco.com` | Documentação técnica (API, integrações) | GitBook / Docusaurus | Devs de rede |
| `status.matchco.com` | Status page + incident history | Statuspage.io / Instatus | Todos |

Multi-tenancy por **subdomínio** (uma rede grande, por ex. Raia Drogasil):

```
raiadrogasil.matchco.com   → schema tenant "raia"
gpashopping.matchco.com    → schema tenant "gpa"
```

django-tenants já suporta isso via `configuration.Domain`. Cada organização
tem seu subdomínio próprio automaticamente.

---

## 3. Estrutura de URLs em `app.matchco.com`

### Público (sem login)
- `/` — anônimo redireciona para `/matchco/`; autenticado vai para feed.
- `/matchco/` — landing pública do produto.
- `/matchco/entrar/` — roteador por papel (candidato/portal).
- `/candidato/signup/` — signup Perfil MatchCo (via QR).
- `/candidato/entrar/` — OTP passwordless (candidato).
- `/candidato/entrar/codigo/` — verificação OTP.
- `/candidato/oportunidades/` — feed territorial (candidato logado por sessão).
- `/qr/<uuid>/` — resolver QR canônico.
- `/privacidade/`, `/privacidade/direitos/`, `/privacidade/processadores/` — LGPD.

### Login clássico
- `/login/` — form login (lojista/sponsor/ops).
- `/logout/`.
- `/reset_password/` — reset via e-mail.

### Console interno (autenticado)
- `/console/` — home do console clássico.
- `/console/recruitment/empregador/necessidades/` — MatchCo lojista.
- `/console/recruitment/matchco/portal/` — painel operacional conforme o escopo do usuário.
- `/console/recruitment/ops/metrics/` — métricas MatchCo.
- `/console/recruitment/ops/ledger/` — auditoria (superuser).
- `/admin/` — Django admin (staff).

---

## 4. Fluxo de acesso por papel

### Candidato (via QR físico)
1. Escaneia QR no shopping → `app.matchco.com/qr/<uuid>/`
2. Redirect canônico → `/candidato/signup/` (com `ep_id` na sessão)
3. Preenche Perfil de 6 campos.
4. Confirma consent granular por escopo.
5. Recebe OTP no e-mail (padrão) ou SMS (se provider configurado).
6. Cai no feed `/candidato/oportunidades/`.

### Lojista (via portal comercial)
1. Recebe link `https://app.matchco.com/matchco/entrar/`
2. Clica "Acessar portal" → `/login/?next=/console/recruitment/matchco/portal/`
3. Login com credenciais fornecidas pela rede.
4. Redirect para painel `/console/recruitment/empregador/necessidades/`

### Shopping/Rede (sponsor)
1. Mesmo caminho do lojista, mas conta com escopo "sponsor".
2. Cai em `/console/recruitment/matchco/portal/`.
3. Vê apenas agregados. **Nunca vê pessoa nominal** — cânone §4.

### Ops MatchCo (equipe interna)
1. `/login/` → usuário superuser.
2. Acesso a `/admin/`, `/console/recruitment/ops/ledger/`, comandos
   `pig_check`, `apply_retention` etc.

---

## 5. Configuração de deploy

### DNS (Cloudflare/Route53)
```
matchco.com          A       → Vercel/Webflow IP
www.matchco.com      CNAME   → matchco.com  (redirect 301)
app.matchco.com      CNAME   → app-cluster.gcp.matchco.internal
*.matchco.com        CNAME   → app.matchco.com   (wildcard para tenants)
docs.matchco.com     CNAME   → docs.gitbook.com
status.matchco.com   CNAME   → matchco.instatus.com
```

### `ALLOWED_HOSTS`
```python
ALLOWED_HOSTS = [
    'app.matchco.com',
    '.matchco.com',    # wildcard para tenants
    'localhost', '127.0.0.1',
]
```

### `CSRF_TRUSTED_ORIGINS`
```python
CSRF_TRUSTED_ORIGINS = [
    'https://app.matchco.com',
    'https://*.matchco.com',
]
```

### Reverse proxy (nginx / Cloud Run / ALB)
- Certificado TLS wildcard `*.matchco.com`.
- HTTP/2 obrigatório.
- Redirect `www` → apex.
- Header `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`.
- CSP restrita (só CDNs conhecidos: cdn.tailwindcss.com, unpkg, jsdelivr).

---

## 6. Marketing site (matchco.com) — o que vai nele

Deploy separado (Vercel/Webflow/Framer), zero dependência do Django.

Conteúdo sugerido:
- Home: pitch das duas portas com CTA "Entrar no app".
- **/produto** — o MatchCo em profundidade.
- **/como-funciona** — vídeo/animação do fluxo bilateral.
- **/pricing** — modelos para shopping / rede / rua isolada.
- **/cases** — depoimentos, resultados.
- **/blog** — SEO.
- **/contato** — form de sales.
- **/politica-de-privacidade** — LGPD institucional (linka para `/privacidade/` no app).
- **/termos-de-uso** — TOS do serviço.
- **CTA principal** → `https://app.matchco.com/matchco/`

O que **NÃO** vai no marketing site:
- Nenhum form que grava dados (usa mailto ou HubSpot/Pipedrive).
- Nenhum login.
- Nenhum QR resolver.
- Nenhum status page (usa subdomínio próprio).

---

## 7. Monitoramento e observabilidade

- **Uptime**: Statuspage/Instatus em `status.matchco.com`, com incidentes
  auto-abertos a partir de alerta no `pig_check` ou `LedgerAppendOnlyError`.
- **Application logs**: stdout → agregador (Grafana Loki / Datadog / CloudWatch).
- **Erros**: Sentry (`https://sentry.io/matchco/app/`).
- **Métricas de produto**: painel `/console/recruitment/ops/metrics/` +
  export via Prometheus/Grafana para dashboards internos.

---

## 8. Migração deste projeto para o modelo SaaS

Estado atual: código Django monolítico rodando em `direct.ddns.net:8001`.

Sequência sugerida:

1. **Comprar `matchco.com`** e `app.matchco.com` (Route53/Cloudflare).
2. **Registrar wildcard TLS** via Let's Encrypt DNS-01.
3. **Deploy staging** em `staging.matchco.com` (mesma infra que prod).
4. **Migrar tenants existentes** — adicionar `matchco.com` como domain de
   cada Organization em `configuration.Domain`.
5. **Marketing site**: fazer em Webflow/Framer separado, apontar para
   `app.matchco.com`.
6. **Cutover**: DNS switch em janela de baixo tráfego. Rollback via TTL curto.

---

## 9. O que fizemos hoje (2026-09-30)

- Fechamos landings legadas: `/sobre-matchco/` e `/recrutamento/` movidas para
  As páginas externas usam somente as rotas canônicas documentadas em
  `docs/help/html/00_MATCHCO_CANONICAL_URLS.html`.
- Trocamos rota `/` para redirect anônimo → `/matchco/`.
- Documentamos aqui a arquitetura de referência.

As views e templates públicos ativos ficam em `recruitment` e seguem as rotas
canônicas do namespace `recruitment_public`; não há rota pública legada ativa.

---

## 10. Referências cruzadas

- `SISTEMA_MATCHCO_CANONICO.md` — regras do produto.
- `POSICIONAMENTO_DUAS_PORTAS.md` — pitch comercial.
- `PROVIDERS.md` — como plugar SMS/e-mail/WhatsApp.
- `runbooks/CUTOVER_PRODUCAO.md` — pré-requisitos de deploy real.
