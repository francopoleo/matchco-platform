# Arquitetura de URLs - Web App PWA

## Problema Atual
- Múltiplas rotas para o mesmo tipo de conteúdo
- Fluxo de autenticação confuso
- Landing page, app e admin misturados
- Difícil para PWA (uma única estrutura clara)

## Estrutura Proposta para PWA

```
DOMÍNIO: https://direct.ddns.net/

┌─── PÚBLICO (sem autenticação) ────────────────────────────┐
│                                                             │
│  /                          → Landing Page (ou redirect)   │
│  /login                     → Login                        │
│  /signup                    → Signup Geral                │
│  /candidato/signup          → Signup Candidato (redirect) │
│  /recruiter/signup          → Signup Recrutador           │
│  /recover-password          → Recuperar Senha             │
│                                                             │
│  /matchco/*                 → Marketing/Info Pages        │
│  /help                      → Documentação Pública        │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─── AUTENTICADO: WORKSPACE (Web App Principal) ────────────┐
│                                                             │
│  /app/                      → Dashboard Principal         │
│  /app/profile               → Meu Perfil                 │
│  /app/courses               → Meus Cursos                │
│  /app/feed                  → Feed/Oportunidades         │
│  /app/matches               → Meus Matches               │
│  /app/settings              → Configurações              │
│  /app/help                  → Help Contextual            │
│                                                             │
│  /app/recruitment/*         → Funcionalidades Recrutamento│
│  /app/courses/*             → Gerenciar Cursos           │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─── ADMIN (Requer Admin) ───────────────────────────────────┐
│                                                             │
│  /console/                  → Admin Dashboard             │
│  /console/recruitment/*     → Recrutamento Admin         │
│  /console/courses/*         → Cursos Admin               │
│  /console/users/*           → Usuários Admin             │
│  /console/documentation/*   → Docs Admin                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Fluxo de Usuário

### Usuário Não Autenticado
```
https://direct.ddns.net/
    ↓
[Detectar autenticação]
    ↓
NÃO AUTENTICADO → /login ou landing bonita
```

### Usuário Autenticado
```
https://direct.ddns.net/
    ↓
[Detectar autenticação]
    ↓
AUTENTICADO → /app/ (Dashboard)
```

### Admin
```
https://direct.ddns.net/console/
    ↓
[Verificar permissões]
    ↓
ADMIN → Dashboard Admin
```

## Benefícios para PWA

1. **URL Consistente**: `/app/*` para toda a app
2. **Simples Navigation**: Sem rotas aninhadas confusas
3. **Offline Support**: App shell sempre em `/app/`
4. **Analytics**: Fácil rastrear uso da app vs landing
5. **Mobile-friendly**: Estrutura plana e lógica
6. **Service Worker**: Cache por tipo de rota

## Implementação

### 1. Nova Raiz com Redirecionamento Inteligente
```python
# urls.py
path('', auto_route_view, name='home')  # Redireciona baseado em auth
```

### 2. Prefixo /app/ para Web App
```python
path('app/', include('app_urls.py'))  # Toda a aplicação aqui
```

### 3. Prefixo /console/ para Admin (manter como está)
```python
path('console/', include('console_urls.py'))
```

### 4. Public URLs (sem /app/)
```python
path('login/', ...)
path('signup/', ...)
path('matchco/', ...)  # Manter ou remover
path('help/', ...)
```

## URLs Específicas Propostas

### Landing / Home
| Rota | Descrição | Acesso |
|------|-----------|--------|
| `/` | Auto-detecta (login ou dashboard) | Público/Autenticado |
| `/login` | Página de login | Público |
| `/signup` | Escolher tipo de signup | Público |
| `/signup/candidato` | Signup candidato | Público |
| `/signup/recruiter` | Signup recrutador | Público |

### App (Workspace)
| Rota | Descrição | Acesso |
|------|-----------|--------|
| `/app/` | Dashboard principal | Autenticado |
| `/app/profile` | Perfil do usuário | Autenticado |
| `/app/courses` | Meus cursos | Autenticado |
| `/app/feed` | Feed de oportunidades | Autenticado |
| `/app/matches` | Matches e conversas | Autenticado |
| `/app/recruitment` | Recrutamento (se recruiter) | Autenticado |

### Help/Documentação
| Rota | Descrição | Acesso |
|------|-----------|--------|
| `/help` | Help público | Público |
| `/app/help` | Help contextual (dentro da app) | Autenticado |
| `/console/documentation` | Docs admin | Admin |

### Auth
| Rota | Descrição | Acesso |
|------|-----------|--------|
| `/login` | Login | Público |
| `/logout` | Logout | Autenticado |
| `/recover-password` | Recuperar senha | Público |

## Próximos Passos

1. Criar `/app/` namespace
2. Mover rotas de app para lá
3. Criar view inteligente em `/` que redireciona
4. Atualizar service worker para cache `/app/*`
5. Testar PWA offline

---

**Data**: 2026-10-03
**Status**: Proposta para discussão
