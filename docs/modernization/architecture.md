# Arquitetura nova do Talk

## Objetivo

Construir uma plataforma modular de comunicação e aprendizagem usando Django como núcleo, templates server-side, Tailwind/Flowbite no frontend, HTMX para interações incrementais e JavaScript nativo apenas quando necessário.

Puput e Wagtail não fazem parte da arquitetura final. O valor principal do sistema fica nos domínios próprios: distribuição de conteúdo, aprendizagem, gamificação e comunicação.

## Módulos

```text
accounts       autenticação, perfis e atributos organizacionais
audience       políticas de público e elegibilidade
content        conteúdos distribuíveis e anexos
learning       cursos, módulos, matrículas, progresso e avaliações
gamification   pontos, eventos, badges, níveis e ranking
publishing     wiki, feed, tags e distribuição editorial
notifications  notificações e preferências
chat           comunicação em tempo real
ui             templates, componentes e assets do frontend
```

Cada módulo deve expor serviços e consultas próprios. Templates não devem decidir regras de acesso; views devem chamar serviços de domínio.

## Motor de público

O acesso a um conteúdo será resultado de uma política explícita:

```text
Content -> AudiencePolicy -> AudienceRule(s)
User    -> atributos organizacionais
EligibilityService -> permitido / negado + motivo
```

Conceitos principais:

- `AudiencePolicy`: conjunto versionado de regras.
- `AudienceRule`: dimensão, operador e valores permitidos.
- `EligibilityService`: única porta para responder se um usuário pode visualizar ou iniciar um conteúdo.
- `EligibilityDecision`: resultado com código e explicação para auditoria.

Dimensões iniciais:

- empresa
- unidade da empresa
- unidade Epson
- tipo de canal
- função
- usuário específico

O motor deve suportar regras `ALL` e `ANY`, datas de publicação, expiração, status do conteúdo e bloqueios explícitos.

Exemplo de API interna:

```python
decision = eligibility.can_view(user, content)

if decision.allowed:
    ...
```

Não haverá consultas de audiência espalhadas por templates ou por cada view.

## Aprendizagem

```text
LearningProgram
  Module
    LearningItem
      TextItem
      VideoItem
      FileItem
      ImageItem
      QuizItem

Enrollment
  ModuleProgress
    ItemProgress
  QuizAttempt
```

O progresso deve pertencer sempre a uma matrícula específica. Conclusão de conteúdo, conclusão de módulo e conclusão de curso serão eventos de domínio idempotentes.

## Gamificação

Gamificação não deve ser acionada diretamente por templates. O módulo `learning` publica eventos, por exemplo:

```text
enrollment.created
learning_item.completed
quiz.passed
program.completed
```

O módulo `gamification` consome esses eventos e aplica regras configuráveis:

```text
GamificationRule -> evento + condição -> recompensa
Reward           -> pontos, badge, nível ou conquista
Ledger           -> histórico imutável de pontos
```

O ledger será a fonte de auditoria. Saldo e ranking serão projeções calculáveis a partir dele.

## Conteúdo editorial

Wiki e Feed serão modelos Django comuns, sem herança de `Page`, `BlogPage` ou `EntryPage`.

Arquivos usarão `FileField`/`ImageField` com storage configurável. Textos editoriais começarão com HTML sanitizado ou Markdown controlado; o editor visual poderá ser adicionado depois sem acoplar o domínio a um CMS.

## Frontend

```text
ui/static/ui/src/input.css
ui/static/ui/src/app.js
ui/static/ui/dist/app.css
ui/static/ui/dist/app.js
ui/templates/ui/base.html
ui/templates/components/
```

Durante a fase de modernização, Flowbite será carregado pelo CDN oficial,
incluindo seu CSS e JavaScript. Isso permite validar rapidamente os componentes
sem uma etapa de build frontend. Uma compilação local poderá ser adicionada
posteriormente apenas para otimização de produção. Bootstrap, jQuery, Blocs,
Tilt, Lazysizes, Font Awesome legado e fontes externas não fazem parte do
frontend final.

O HTML deverá continuar sendo renderizado pelo Django. Flowbite será usado apenas para componentes como menu, modal, tabs e accordion.

O shell visual é compartilhado por todo o produto: `ui/base.html` é a base das
telas novas e `ui/navigation.html` funciona como compatibilidade para telas
legadas em migração. O mesmo navbar, sidebar, avatar, seletor de idioma,
toggle de tema e comportamento mobile são usados por usuários comuns e
gestores. A diferença de perfil fica apenas nos links exibidos: gestores
autorizados recebem o acesso ao `/console/`, enquanto usuários comuns recebem
a navegação de aprendizagem, feed, wiki, busca, perfil e gamificação.

A identidade visual usa acentos neon controlados (fúcsia, ciano, esmeralda e
âmbar) sobre superfícies neutras, mantendo contraste e legibilidade nos modos
claro e escuro. Novos componentes devem reutilizar esse shell antes de criar
uma navegação própria.

### Localização e tradução

Todas as telas novas e todas as telas que forem revisadas devem participar do
sistema nativo de internacionalização do Django. Não devemos manter textos de
interface fixos em views, templates ou JavaScript quando forem apresentados ao
usuário.

Padrão de implementação:

- templates usam `{% trans %}` para textos curtos e `{% blocktrans %}` para
  frases com variáveis;
- Python usa `gettext_lazy` em labels, mensagens, títulos e nomes de opções;
- JavaScript recebe textos traduzíveis pelo HTML ou por atributos `data-*`,
  evitando um segundo sistema de tradução no frontend;
- traduções ficam em arquivos `.po` por idioma e os arquivos compilados `.mo`
  são gerados no processo de build/deploy;
- `LocaleMiddleware` permanece habilitado e a preferência do usuário continua
  sendo definida pelo perfil e pela sessão;
- comandos padrão do projeto: `makemessages` para extrair mensagens e
  `compilemessages` para gerar os catálogos publicados;
- cada nova view deve ser revisada com os idiomas suportados (`pt-br`, `en` e
  `es`) antes de ser considerada concluída.

A localização será feita incrementalmente: primeiro console, navegação,
formulários, filtros e mensagens de sucesso/erro; depois cursos, feed, wiki,
perfil, gamificação e telas de aprendizagem. Variáveis de negócio, slugs,
permissões, nomes de eventos e identificadores técnicos não devem ser
traduzidos.

## Console de gestores

O sistema terá duas superfícies administrativas:

- `/console/`: interface operacional Flowbite para gestores de conteúdo e audiência.
- `/admin/`: Django Admin restrito a suporte técnico e superusuários.

O console inicial cobre dashboard operacional, cadastro e edição de Feed/Wiki,
seleção de políticas de audiência e listagem de políticas de público.

Gestores serão autorizados por `is_staff`, superusuário ou grupos de domínio
(`content_manager` e `audience_manager`). A autorização será reforçada no
backend, independentemente da visibilidade dos menus.

O menu Flowbite atual está em prévia via CDN para acelerar a validação visual.
Depois da aprovação, Tailwind/Flowbite serão compilados e servidos localmente.

### Padrão responsivo para tabelas e formulários

Responsividade é um requisito funcional, especialmente para gestores que usam o
console em celular. Todos os novos templates devem seguir o princípio
mobile-first e usar a largura disponível da página.

Formulários:

- ocupar `w-full` por padrão, sem limitar o container a uma largura estreita;
- organizar os campos em uma coluna no mobile e em duas ou mais colunas a
  partir dos breakpoints necessários (`md:grid-cols-2`, por exemplo);
- usar componentes Flowbite/Tailwind com estados de foco, erro, disabled,
  light mode e dark mode;
- manter ações primárias e secundárias acessíveis no rodapé do formulário,
  permitindo quebra de linha em telas pequenas;
- evitar larguras fixas, `min-width` desnecessário e componentes que provoquem
  overflow horizontal.

Tabelas:

- em desktop, usar tabelas Flowbite com cabeçalho, linhas listradas, filtros,
  paginação e coluna de ações;
- em mobile, preferir transformar cada registro em um card vertical, mantendo
  visíveis apenas os dados principais e as ações;
- esconder ou reorganizar colunas secundárias com classes responsivas quando
  isso preservar a compreensão do registro;
- usar `overflow-x-auto` somente como fallback para tabelas genuinamente
  tabulares e muito largas, como relatórios detalhados;
- nunca exigir scroll horizontal para ações essenciais, status, título ou
  identificação do registro;
- manter busca e filtros empilháveis: uma coluna no mobile e layout horizontal
  em telas maiores.

Estrutura recomendada para tabelas administrativas:

```html
<div class="hidden md:block overflow-x-auto">
    <!-- tabela Flowbite para desktop -->
</div>

<div class="space-y-3 md:hidden">
    <!-- cards equivalentes para mobile -->
</div>
```

Esse padrão deve ser aplicado ao console de publicações, políticas e regras de
audiência, cursos, usuários, matrículas e relatórios. Componentes reutilizáveis
devem ficar em `templates/components/`, evitando que cada tela implemente uma
variação incompatível.

### HTMX

HTMX será a camada padrão para interações que não exigem uma aplicação SPA:

- filtros de cursos, feed e wiki;
- atualização de progresso e conclusão de itens;
- modais e formulários inline;
- paginação e carregamento incremental;
- notificações e estados parciais de gamificação.

Cada interação HTMX deverá ter uma resposta HTML completa como fallback. Os fragmentos ficarão em `templates/components/` ou junto do domínio responsável, e as regras de negócio continuarão nas views/services Django.

## Princípios

1. Regra de negócio em serviços Python.
2. Acesso sempre verificado no backend.
3. Templates apenas apresentam dados.
4. Eventos de domínio desacoplam aprendizagem e gamificação.
5. Consultas de leitura ficam em selectors/querysets.
6. Dependências externas são substituíveis e isoladas.
7. Toda decisão de acesso relevante precisa ser testável.
