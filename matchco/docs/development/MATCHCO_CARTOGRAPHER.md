# MatchCo Cartographer — mapa único da documentação

Este é o índice de autoridade para a documentação técnica e de produto do
MatchCo. Ele evita que decisões importantes fiquem espalhadas em planos
duplicados, READMEs antigos ou documentos de uma fase já encerrada.

## Fonte de verdade

| Assunto | Fonte canônica | Regra |
|---|---|---|
| Roadmap e contrato de implementação | [`MATCHCO_VALIDATION_PLAN.md`](MATCHCO_VALIDATION_PLAN.md) | Todo novo trabalho deve atualizar este plano e sua fase correspondente. |
| Arquitetura SaaS, tenants e estrutura | [`02_ARCHITECTURE_MULTITENANT.html`](../help/html/02_ARCHITECTURE_MULTITENANT.html) | A versão publicada no Help é a referência operacional. |
| URLs, menus e pontos de entrada | [`00_MATCHCO_CANONICAL_URLS.html`](../help/html/00_MATCHCO_CANONICAL_URLS.html) | Toda rota nova deve aparecer na matriz canônica. |
| Catálogo de serviços e escopo comercial | [`02_ARCHITECTURE_MULTITENANT.html`](../help/html/02_ARCHITECTURE_MULTITENANT.html) e [`MATCHCO_VALIDATION_PLAN.md`](MATCHCO_VALIDATION_PLAN.md) | A organização define o padrão; a empresa pode receber uma exceção explícita. |
| Jornadas de stakeholders | [`00_MATCHCO_CORE_STAKEHOLDER_FLOWS.html`](../help/html/00_MATCHCO_CORE_STAKEHOLDER_FLOWS.html) | Fluxos de candidato, unidade, organização e serviços. |
| Recrutamento Match | [`03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html`](../help/html/03_RECRUITMENT_IMPLEMENTATION_CHECKLIST.html) | Alto giro, Perfil, necessidade, rodadas e Match. |
| LGPD, segurança e incidentes | [`03_RECRUITMENT_PRIVACY_LGPD.html`](../help/html/03_RECRUITMENT_PRIVACY_LGPD.html) e os runbooks | Controles preventivos, resposta e direitos dos titulares. |
| Cursos, treinamento e certificações | [`03_COURSES_IMPLEMENTATION_CHECKLIST.html`](../help/html/03_COURSES_IMPLEMENTATION_CHECKLIST.html) | Conteúdo, progresso, avaliação e certificação. |
| Código e navegação do repositório | [`CODEBASE_MAP.md`](REFERENCES/CODEBASE_MAP.md) | Mapa de módulos, modelos, views e pontos de extensão. |
| Operação segura | [`recruitment/runbooks/README.md`](recruitment/runbooks/README.md) | Runbooks executáveis; cada incidente específico fica em arquivo próprio. |

## Organização dos documentos ativos

```text
matchco/docs/
├── help/html/                 # Help publicado no Console
├── development/               # Fonte técnica e decisões ativas
│   ├── MATCHCO_CARTOGRAPHER.md
│   ├── MATCHCO_MASTER_PLAN.md
│   ├── GUIDES/                # desenvolvimento, deploy e uso
│   ├── REFERENCES/            # API, banco, arquitetura e UI
│   ├── recruitment/           # Match, provedores e runbooks
│   └── archive/               # histórico sem autoridade operacional
└── README.md                  # regras desta estrutura
```

## Classificação do inventário Markdown

### Ativo e centralizado

- arquitetura e desenvolvimento em `matchco/docs/development/`;
- guias em `GUIDES/`;
- referências em `REFERENCES/`;
- recrutamento e runbooks em `recruitment/`;
- o plano comercial/técnico e documentos estratégicos apontados pelo
  `MATCHCO_MASTER_PLAN.md`.

### Preservado fora do índice técnico

- `AGENTS.md` e `CLAUDE.md`: instruções para agentes e ferramentas, não são
  documentação funcional do produto;
- `README.md` da raiz e READMEs de `sdk/`: entrada do repositório/pacote;
- `senhas.md`: material restrito de demonstração, nunca deve ser publicado ou
  indexado pelo Help;
- licenças, changelogs e READMEs de bibliotecas em `static/`, `staticfiles/`
  e `node_modules/`: pertencem às dependências;
- `matchco/docs/archive/`: histórico consultável, sem ser fonte de decisão.

## Regras contra duplicação

1. Uma regra de produto deve existir uma única vez no plano ou no Help
   canônico; os demais documentos devem apontar para ela.
2. Um checklist operacional tem uma única fonte HTML em `help/html/`.
3. Um documento histórico não volta para a área ativa sem revisão explícita.
4. Toda mudança de rota, modelo, serviço, tenant, audiência, QR ou permissão
   atualiza o Help contextual e a matriz de URLs.
5. Antes de criar um `.md`, procure neste índice e no plano mestre; se o tema
   já existir, edite a fonte existente.

## Auditoria atual

O inventário inicial encontrou 135 arquivos Markdown. A maior parte das
duplicações estava entre documentos de raiz, documentação antiga em `docs/`,
arquivos históricos e bibliotecas estáticas. A partir deste Cartographer, o
desenvolvimento considera `matchco/docs/` a raiz documental ativa; os demais
arquivos são compatibilidade, instrução, pacote ou arquivo histórico.

Última revisão: 2026-10-09. Nesta revisão, o Console passou a separar Serviços
de Organização e estrutura, e o catálogo suporta ativação por organização com
override por empresa.

Contrato de conteúdo por empresa: administração no Console, consumo autenticado
no App e operação contextual no Portal. Ownership e audiência são dimensões
complementares; veja `MATCHCO_MASTER_PLAN.md`, fase E do plano e as páginas
HTML de arquitetura e URLs. O seletor de empresa nunca substitui autorização
server-side.
