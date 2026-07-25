# Plano da demonstração Hospital Generative

**Versão do plano:** 1.0  
**Base:** Talk Learning 1.0.0.0  
**Objetivo:** construir uma demonstração enterprise realista para comunicação, capacitação e conhecimento de um grupo hospitalar sem misturar audiências.

## 1. Modelo recomendado

O modelo atual já comporta a hierarquia principal:

```text
Organização/Tenant: Hospital Generative
└── Empresa: Grupo Hospital Generative
    └── Unidade de negócio: hospital ou operação local
        └── Unidade operacional: departamento/serviço dentro do hospital
```

Para esta demonstração, não devemos criar uma organização Talk Learning como empresa do cliente. A organização representa o tenant do grupo hospitalar; a empresa representa o grupo econômico.

### Exemplo de estrutura

```text
Hospital Generative
└── Grupo Hospital Generative
    ├── Hospital Generative Ipiranga - SP
    │   ├── Pronto Socorro
    │   ├── UTI Adulto
    │   ├── UTI Pediátrica
    │   ├── Centro Cirúrgico
    │   ├── Ortopedia
    │   ├── Laboratório
    │   └── Diagnóstico por Imagem
    ├── Hospital Generative Pompeia - SP
    │   ├── Pronto Socorro
    │   ├── UTI Adulto
    │   ├── Centro Cirúrgico
    │   ├── Ortopedia
    │   └── Laboratório
    ├── Centro de Consultas Pompeia - SP
    │   ├── Consultórios
    │   ├── Cardiologia
    │   ├── Ortopedia
    │   └── Exames
    └── Instituto Generative de Diagnóstico - SP
        ├── Ressonância Magnética
        ├── Tomografia
        ├── Ultrassonografia
        └── Laboratório de Análises
```

`BusinessUnit` representa a unidade/localidade. `OperationalUnit` representa o departamento, serviço ou área assistencial dentro dela. Isso mantém a hierarquia atual sem criar um terceiro modelo concorrente.

## 2. Pessoas e vínculos

As funções atuais devem representar a função no ambiente, e não o tipo jurídico da pessoa. Para a massa inicial, usar:

### Funções assistenciais

- Médico plantonista
- Médico cirurgião
- Médico ortopedista
- Médico cardiologista
- Médico pediatra
- Enfermeiro
- Enfermeiro responsável técnico
- Técnico de enfermagem
- Auxiliar de enfermagem
- Fisioterapeuta
- Farmacêutico
- Biomédico
- Técnico de laboratório
- Técnico de radiologia

### Funções administrativas e operacionais

- Coordenador de unidade
- Coordenador médico
- Coordenador de enfermagem
- Gestor de operações
- Recepcionista
- Faturamento
- Auditor hospitalar
- Recursos humanos
- Tecnologia da informação
- Segurança do paciente
- Compras e suprimentos
- Manutenção predial
- Higienização

### Ecossistema externo

- Prestador médico credenciado
- Empresa terceirizada de enfermagem
- Fornecedor de equipamentos
- Fornecedor de medicamentos
- Laboratório parceiro
- Operadora/conveniado
- Auditor externo

### Pacientes

Pacientes não devem receber a mesma navegação enterprise dos colaboradores. Para o primeiro seed, podem existir como usuários de teste com função `Paciente` e canal `Paciente/Portal`, mas o plano definitivo exige um tipo de pessoa/perfil de acesso separado, com políticas próprias e proteção de dados sensíveis.

## 3. Dimensões de audiência

Usar `BusinessChannel` para separar o contexto de relacionamento, não para substituir departamentos:

- Colaborador interno
- Corpo clínico
- Enfermagem e assistência
- Prestador credenciado
- Fornecedor
- Laboratório parceiro
- Paciente/Portal
- Gestão corporativa

Exemplos de políticas:

```text
Empresa Grupo Hospital Generative
E Canal Corpo clínico
E Função Médico cirurgião
```

```text
Unidade Hospital Generative Ipiranga
E Unidade operacional Centro Cirúrgico
```

```text
Unidade Hospital Generative Pompeia
E Função Técnico de radiologia
```

```text
Empresa Grupo Hospital Generative
E Canal Gestão corporativa
```

Regra sem função ou canal deve liberar todas as funções/canais dentro do escopo hierárquico selecionado. Isso precisa ser mostrado na interface como “todas as funções” e “todos os canais”, nunca como filtro oculto.

## 4. Conteúdo da demonstração

### Cursos

Criar pelo menos 12 cursos, distribuídos em:

- Integração institucional e cultura de segurança
- Segurança do paciente
- Higienização das mãos
- Protocolo de cirurgia segura
- Prevenção e controle de infecções
- Atendimento inicial no pronto socorro
- Rotina da UTI adulto
- Rotina da UTI pediátrica
- Uso seguro de equipamentos de imagem
- Coleta e transporte de exames laboratoriais
- LGPD e sigilo de informações de saúde
- Comunicação com pacientes e familiares

Cada curso deve ter 3 a 5 módulos e conteúdos variados: texto, vídeo, quiz e checklist. Cursos locais devem possuir audiência da unidade ou departamento correspondente.

### Feed

Feed é notícia curta, operacional e temporal:

- Interdição temporária de equipamento de ressonância
- Atualização do protocolo de identificação do paciente
- Treinamento obrigatório de cirurgia segura
- Mudança no fluxo do pronto socorro
- Janela de manutenção do sistema laboratorial
- Reconhecimento de equipe de segurança do paciente

Cada publicação deve ter uma imagem, texto curto, tags e, quando necessário, referência para curso ou Wiki.

### Wiki

Wiki é referência permanente e versionável:

- Checklist de cirurgia segura
- Fluxo de acionamento da UTI
- Manual de coleta e transporte de exames
- Uso e limpeza de equipamentos de imagem
- Telefones e canais de escalonamento
- Protocolo de atendimento a eventos adversos
- Guia de integração de prestadores
- Matriz de responsabilidades por departamento

## 5. Checklists e conteúdos críticos

O seed pode conter exemplos didáticos, mas deve deixar claro que são materiais de demonstração e não protocolos clínicos aprovados.

Exemplo de Wiki “Cirurgia segura — demonstração”:

1. Confirmar identidade do paciente com dois identificadores.
2. Confirmar procedimento, lateralidade e consentimento.
3. Conferir alergias, riscos e exames necessários.
4. Confirmar disponibilidade de sangue, materiais e equipamentos.
5. Realizar pausa de segurança antes da incisão.
6. Registrar contagem de compressas, instrumentais e materiais.
7. Confirmar plano pós-operatório e destino do paciente.
8. Registrar não conformidades e responsáveis pelo acompanhamento.

Não incluir dados reais de pacientes, prontuários, diagnósticos ou imagens clínicas reais na massa demo.

## 6. Gestores por escopo

Criar gestores em camadas:

| Escopo | Exemplo | Responsabilidade |
|---|---|---|
| Grupo | Diretoria corporativa | Conteúdo institucional e políticas do grupo |
| Unidade | Gerente do Hospital Ipiranga | Pessoas e conteúdo da unidade |
| Departamento | Coordenador do Centro Cirúrgico | Conteúdo e audiência do departamento |
| Especialidade | Coordenador de Ortopedia | Cursos e referências da especialidade |

O código atual de console ainda usa principalmente `is_staff`/grupos para liberar telas. Antes da demonstração comercial, a autorização de criação/edição de conteúdo precisa aplicar `ManagementAssignment` por escopo, e não somente proteger a visualização de usuários e relatórios.

## 7. Pontos que faltam antes do seed definitivo

1. **Tipo de pessoa:** adicionar um campo controlado para diferenciar colaborador, corpo clínico, prestador, fornecedor e paciente. Função sozinha não é suficiente.
2. **Autorização de conteúdo:** limitar criação/edição de Feed, Wiki e Curso ao escopo do gestor.
3. **Auditoria:** registrar quem alterou audiência, conteúdo e vínculo de usuário.
4. **Privacidade:** marcar conteúdos como institucionais, operacionais ou sensíveis; pacientes não devem herdar conteúdos internos.
5. **Políticas de segurança:** impedir que uma audiência local seja criada apontando para outra organização.
6. **Reset seguro:** comando separado com confirmação explícita e modo `--dry-run`; preservar apenas o superusuário definido por username/e-mail.
7. **Seed idempotente:** todos os registros devem usar slugs/códigos estáveis e poder ser executados novamente sem duplicar dados.
8. **Imagens demo:** usar somente imagens internas/licenciadas ou SVGs/gradientes gerados localmente.
9. **Dados clínicos:** não usar dados de pacientes reais; nomes, registros e exemplos devem ser fictícios.
10. **Testes de audiência:** validar casos positivos e negativos por grupo, unidade, departamento, função e canal.

## 7.1. Configuração agnóstica implementada

O Talk agora possui configuração por organização em `/console/organization-settings/`:

- `OrganizationTerminology` permite editar os rótulos e descrições dos três níveis hierárquicos.
- `PersonType` permite cadastrar tipos como colaborador, médico, prestador, fornecedor ou paciente.
- `Membership.person_type` relaciona o tipo de pessoa ao vínculo organizacional, permitindo que o mesmo usuário tenha contextos diferentes em organizações ou vínculos distintos.
- O frontend recebe `organization_terminology` por contexto, com fallback para os termos genéricos `Empresa`, `Unidade de negócio` e `Unidade operacional`.

Para o demo hospitalar, a configuração recomendada é:

```text
Nível 1: Grupo
Nível 2: Hospital ou Centro de consultas
Nível 3: Unidade, departamento ou serviço
```

Os nomes técnicos dos modelos permanecem estáveis para o sistema ser agnóstico; somente a apresentação e as descrições mudam por organização.

## 8. Estratégia de reset e seed

O comando planejado deve ser explícito:

```text
python manage.py seed_hospital_demo --reset --admin-email admin@talk.local --dry-run
python manage.py seed_hospital_demo --reset --admin-email admin@talk.local
```

O reset deve:

- exigir `--reset`;
- imprimir a quantidade de registros por modelo antes de apagar;
- apagar dados de negócio, vínculos, conteúdo, cursos, publicações e usuários não protegidos;
- preservar ou recriar somente o administrador indicado;
- executar em transação;
- criar a estrutura hospitalar e validar referências no final.

O seed deve ser separado dos comandos genéricos existentes para que a demonstração hospitalar possa ser removida/recriada sem depender de dados de Learning Operations.

## 9. Critérios de aceite

- O administrador vê todos os ambientes.
- Um gestor corporativo não vê conteúdo exclusivo de outra unidade quando sua audiência não contempla a unidade.
- Um gestor do Ipiranga pode gerenciar o Centro Cirúrgico do Ipiranga, mas não a UTI da Pompeia.
- Um médico cirurgião recebe cursos e wikis clínicos pertinentes, sem receber conteúdo de fornecedor não relacionado.
- Um fornecedor recebe apenas conteúdos do canal de fornecedores e sua unidade/escopo.
- Um paciente de demonstração não recebe conteúdo interno de colaboradores.
- Feed, Wiki e Cursos aparecem com contagens de impacto coerentes.
- O seed pode ser repetido sem duplicidade.
- O reset não remove o administrador protegido.

## 10. Segundo tenant: Seguradora Generative

O mesmo comando `seed_hospital_demo` também cria ou atualiza a organização
`seguradora-generative`. O seed permanece único para que atualizações comuns
de infraestrutura, usuários, audiência e conteúdos de demonstração possam ser
reproduzidas nos dois ambientes sem duplicar comandos.

A seguradora demonstra uma operação multicanal com regionais, central de
relacionamento, operação digital, corretores, assessorias, bancos, parceiros,
prestadores credenciados e clientes. Seus dados são isolados por organização:
6 operações, 21 equipes, 7 tipos de pessoa, 17 funções, 8 cursos, 8
publicações e políticas próprias.

Usuários podem possuir memberships em mais de uma organização, mas somente
uma fica ativa por vez na sessão. Quando houver mais de uma organização
disponível, a navbar exibe o seletor de organização. A seleção é validada
contra as memberships ativas (superusuários podem inspecionar todos os
tenants) e é aplicada aos cursos, feed, wiki, busca, indicadores e avaliação
de audiência.
