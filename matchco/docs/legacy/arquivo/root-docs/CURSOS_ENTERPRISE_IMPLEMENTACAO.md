# Cursos Enterprise — Checklist de Implementação

Documento vivo de execução. Cada item deve ser marcado somente depois de código, teste e validação funcional.

## Convenções

- `[ ]` pendente
- `[-]` em andamento ou parcialmente entregue
- `[x]` concluído e validado
- `[!]` bloqueado ou exige decisão

## Objetivo

Transformar o módulo de cursos em uma experiência enterprise, com navegação livre ou controlada, progresso confiável, pré-requisitos, consumo mensurável, avaliações, certificados, evidências de compliance e relatórios por empresa.

## Estado atual identificado

- [x] Cursos, módulos e conteúdos existentes.
- [x] Matrícula e progresso básico existentes.
- [x] Eventos de aprendizagem existentes.
- [x] Quizzes com nota mínima existentes.
- [x] Trilhas com passos e pré-requisitos básicos existentes.
- [x] Certificados existentes.
- [x] Isolamento tenant e `TenantUser` aplicados na matrícula e no conteúdo.
- [x] Reset/seed de desenvolvimento existente.
- [ ] Motor único de acesso e conclusão.
- [ ] Política configurável por curso.
- [ ] Progresso detalhado por conteúdo.
- [ ] Evidências técnicas de vídeo, PDF e apresentação.
- [ ] Relatórios enterprise completos.

## Fase 0 — Contrato técnico e banco

- [ ] Definir enums oficiais de progressão: `free`, `linear`, `prerequisite`, `drip`, `mastery`, `compliance`.
- [ ] Definir estados oficiais: `pending`, `available`, `in_progress`, `blocked`, `completed`, `failed`, `expired`.
- [ ] Definir fontes de conclusão: `manual`, `open`, `time`, `percentage`, `quiz`, `evidence`, `combined`.
- [ ] Criar política de progressão do curso.
- [ ] Criar política de conclusão do conteúdo.
- [ ] Criar entidade de progresso individual detalhado.
- [ ] Criar entidade de evidência de conclusão.
- [ ] Criar entidade de pré-requisito entre cursos, módulos e conteúdos.
- [ ] Criar entidade de janela de acesso/matrícula.
- [ ] Criar constraints e índices para usuário, curso, conteúdo e tenant.
- [ ] Garantir que relações tenant usem `TenantUser` e `TenantOrganization`.
- [ ] Criar migrações limpas para desenvolvimento.
- [ ] Atualizar o reset demo para recriar todos os modelos.

## Fase 1 — Motor central de aprendizagem

- [ ] Criar `can_access_course(user, course)`.
- [ ] Criar `can_access_content(user, content)`.
- [ ] Criar `get_progress(user, course)`.
- [ ] Criar `get_content_status(user, content)`.
- [ ] Criar `record_consumption(user, content, event_data)`.
- [ ] Criar `evaluate_completion(user, content)`.
- [ ] Criar `complete_content(user, content, source)`.
- [ ] Criar `get_next_available_content(user, course)`.
- [ ] Criar `issue_certificate_if_eligible(user, course)`.
- [ ] Migrar views para usar exclusivamente o motor.
- [ ] Migrar APIs para usar exclusivamente o motor.
- [ ] Impedir conclusão baseada somente em payload enviado pelo navegador.
- [ ] Tornar operações idempotentes.
- [ ] Adicionar transações para conclusão, aprovação e certificado.

## Fase 2 — Navegação

### Modo livre

- [ ] Permitir acesso fora de ordem.
- [ ] Exibir botão “Marcar como concluído”.
- [ ] Permitir revisão de conteúdos concluídos.

### Modo linear

- [ ] Bloquear o próximo conteúdo até o anterior estar concluído.
- [ ] Bloquear acesso por URL direta.
- [ ] Mostrar o motivo do bloqueio.
- [ ] Liberar automaticamente após conclusão válida.

### Pré-requisitos

- [ ] Pré-requisito de conteúdo.
- [ ] Pré-requisito de módulo.
- [ ] Pré-requisito de curso.
- [ ] Pré-requisito com nota mínima.
- [ ] Pré-requisito com múltiplas condições.
- [ ] Validação contra ciclos de dependência.
- [ ] Editor visual de dependências.

## Fase 3 — Progresso do aluno

- [ ] Exibir progresso geral do curso.
- [ ] Exibir progresso por módulo.
- [ ] Exibir estado de cada conteúdo.
- [ ] Criar botão “Continuar curso”.
- [ ] Retomar último conteúdo e posição.
- [ ] Exibir tempo estudado.
- [ ] Exibir conteúdos pendentes.
- [ ] Exibir requisitos pendentes.
- [ ] Exibir progresso no console do administrador.
- [ ] Diferenciar conteúdo concluído, disponível, bloqueado e reprovado.

## Fase 4 — Texto, PDF e apresentação

### Texto

- [ ] Regra de abertura simples.
- [ ] Regra de conclusão manual.
- [ ] Regra de tempo mínimo.
- [ ] Regra de rolagem até o final.
- [ ] Confirmação de leitura.

### PDF

- [ ] Registrar abertura.
- [ ] Registrar última página.
- [ ] Registrar páginas alcançadas.
- [ ] Registrar tempo ativo.
- [ ] Configurar percentual mínimo de páginas.
- [ ] Configurar confirmação de leitura.
- [ ] Diferenciar download de leitura.

### Apresentação

- [ ] Registrar slides vistos.
- [ ] Registrar último slide.
- [ ] Registrar tempo ativo.
- [ ] Configurar cobertura mínima.
- [ ] Permitir retomada.

## Fase 5 — Vídeo

- [ ] Registrar `currentTime` e duração.
- [ ] Registrar percentual reproduzido.
- [ ] Registrar sessões e retomada.
- [ ] Registrar pausas e abandono.
- [ ] Registrar heartbeat do player.
- [ ] Limitar avanço artificial.
- [ ] Configurar conclusão em 50%, 80%, 90%, 95% ou 100%.
- [ ] Configurar exigência de assistir sem salto.
- [ ] Configurar vídeo + quiz como regra combinada.
- [ ] Mostrar percentual ao aluno.
- [ ] Criar relatório de abandono de vídeo.

Nota: o sistema registra evidência técnica de reprodução, mas não pode garantir atenção humana. Para compliance, combinar percentual, tempo mínimo e avaliação.

## Fase 6 — Quiz e domínio

- [x] Nota mínima existente.
- [ ] Vincular quiz obrigatório ao conteúdo.
- [ ] Vincular quiz obrigatório ao módulo.
- [ ] Vincular quiz obrigatório ao curso.
- [ ] Liberar próximo item somente após aprovação.
- [ ] Configurar número máximo de tentativas.
- [ ] Configurar intervalo entre tentativas.
- [ ] Configurar tempo limite.
- [ ] Configurar embaralhamento.
- [ ] Persistir respostas e nota no servidor.
- [ ] Exibir feedback de aprovação/reprovação.
- [ ] Permitir política de refazer conteúdo após reprovação.
- [ ] Testar aprovação, reprovação, limite e expiração de tentativas.

## Fase 7 — Liberação programada

- [ ] Liberar imediatamente.
- [ ] Liberar em data fixa.
- [ ] Liberar após dias da matrícula.
- [ ] Liberar após conclusão de requisito.
- [ ] Configurar início e fim de turma.
- [ ] Configurar expiração da matrícula.
- [ ] Exibir contagem regressiva ou data de liberação.
- [ ] Bloquear acesso antes da data no backend.
- [ ] Testar fuso horário e mudança de data.

## Fase 8 — Compliance e evidências

- [ ] Confirmação de leitura.
- [ ] Aprovação de gestor.
- [ ] Presença presencial.
- [ ] Upload de comprovante.
- [ ] Comentário do responsável.
- [ ] Data e hora da evidência.
- [ ] Responsável pela aprovação.
- [ ] Histórico imutável.
- [ ] Exportação de evidências.
- [ ] Revogação com motivo.
- [ ] Revalidação após nova versão do curso.

## Fase 9 — Certificados

- [x] Certificado existente.
- [ ] Condicionar certificado ao motor de regras.
- [ ] Número único e código de validação.
- [ ] Registrar versão do curso.
- [ ] Registrar empresa e organização.
- [ ] Configurar validade.
- [ ] Configurar expiração.
- [ ] Permitir revogação.
- [ ] Criar página de validação.
- [ ] Impedir emissão duplicada.

## Fase 10 — Experiência do player

- [ ] Barra de progresso do curso.
- [ ] Barra de progresso do módulo.
- [ ] Lista lateral com estados.
- [ ] Botão “Continuar curso”.
- [ ] Botão “Próximo conteúdo”.
- [ ] Botão “Conteúdo anterior”.
- [ ] Mensagem clara de bloqueio.
- [ ] Exibição da regra de conclusão.
- [ ] Exibição de tempo e percentual.
- [ ] Retomada automática.
- [ ] Layout responsivo.
- [ ] Acessibilidade de teclado e leitor de tela.
- [ ] Estado consistente após navegação HTMX/API.

## Fase 11 — Editor de cursos

- [ ] Escolher modo de progressão.
- [ ] Escolher regra de conclusão.
- [ ] Configurar tempo mínimo.
- [ ] Configurar percentual mínimo.
- [ ] Configurar quiz e nota mínima.
- [ ] Configurar tentativas.
- [ ] Configurar liberação programada.
- [ ] Configurar certificado.
- [ ] Configurar evidência.
- [ ] Criar ordem visual de módulos e conteúdos.
- [ ] Criar dependências visualmente.
- [ ] Validar ciclos antes de publicar.
- [ ] Pré-visualizar como aluno.
- [ ] Exibir alertas de configuração incompleta.
- [ ] Publicar versão imutável do curso.

## Fase 12 — Relatórios enterprise

- [ ] Progresso por curso.
- [ ] Progresso por módulo.
- [ ] Progresso por conteúdo.
- [ ] Progresso por usuário.
- [ ] Tempo estudado.
- [ ] Última atividade.
- [ ] Conteúdos abandonados.
- [ ] Vídeos não concluídos.
- [ ] PDFs não lidos.
- [ ] Quizzes reprovados.
- [ ] Tentativas por usuário.
- [ ] Certificados emitidos.
- [ ] Certificados vencidos.
- [ ] Pendências de compliance.
- [ ] Linha do tempo de auditoria.
- [ ] Exportação CSV/PDF.
- [ ] Filtros por empresa, organização, unidade e período.
- [ ] Superadmin com visão consolidada.
- [ ] Usuário comum restrito à empresa correta.

## Fase 13 — Multiempresa e segurança

- [x] Conversão de usuário público para `TenantUser` na matrícula.
- [x] Conversão de usuário público para `TenantUser` no conteúdo.
- [x] Webhook com conversão de `TenantOrganization` para `Organization` pública.
- [ ] Auditoria de todas as ForeignKeys de usuário tenant.
- [ ] Auditoria de todas as ForeignKeys de organização tenant.
- [ ] Testar troca de empresa no topo sem mudar de página.
- [ ] Testar usuário em duas empresas.
- [ ] Testar empresa XYZ sem dados Bourbon.
- [ ] Testar superadmin em empresa individual.
- [ ] Testar superadmin em visão consolidada.
- [ ] Testar acesso direto por URL.
- [ ] Testar alteração maliciosa de IDs no payload.
- [ ] Testar APIs com tenant incorreto.

## Fase 14 — Reset e seed de desenvolvimento

- [x] Reset-only existente.
- [x] Reset + seed existente.
- [x] Superadmin demo criado.
- [x] Empresas demo existentes.
- [ ] Curso Livre demo.
- [ ] Curso Linear demo.
- [ ] Curso com pré-requisito demo.
- [ ] Curso Drip demo.
- [ ] Curso Domínio demo.
- [ ] Curso Compliance demo.
- [ ] Exemplos de vídeo, PDF, apresentação e quiz.
- [ ] Usuário com progresso zero.
- [ ] Usuário em andamento.
- [ ] Usuário concluído.
- [ ] Usuário reprovado.
- [ ] Usuário com certificado.
- [ ] Usuário com conteúdo bloqueado.
- [ ] Reset idempotente.
- [ ] Reset preserva domínios de desenvolvimento.

## Fase 15 — Testes obrigatórios

- [ ] Teste unitário do modo livre.
- [ ] Teste unitário do modo linear.
- [ ] Teste unitário de pré-requisito.
- [ ] Teste unitário de drip.
- [ ] Teste unitário de quiz e nota mínima.
- [ ] Teste unitário de tempo mínimo.
- [ ] Teste unitário de percentual de vídeo.
- [ ] Teste de integração de matrícula.
- [ ] Teste de integração de conclusão.
- [ ] Teste de integração de certificado.
- [ ] Teste de repetição de eventos.
- [ ] Teste de concorrência em dois dispositivos.
- [ ] Teste de isolamento tenant.
- [ ] Teste de permissão por empresa.
- [ ] Teste da API e da interface com a mesma regra.
- [ ] Teste de reset e seed.
- [ ] Teste de regressão nas páginas existentes do console.

## Critérios finais de aceite

- [ ] O aluno sempre sabe o que pode fazer agora e o que falta para avançar.
- [ ] O botão “Continuar curso” leva ao próximo item válido.
- [ ] Nenhum conteúdo bloqueado é liberado por URL direta.
- [ ] O mesmo progresso aparece corretamente no player, console e API.
- [ ] Vídeo, PDF e apresentação registram evidência conforme sua política.
- [ ] Quiz aprovado libera a etapa configurada.
- [ ] Curso incompleto não emite certificado.
- [ ] Relatório de uma empresa não exibe outra empresa.
- [ ] Superadmin consegue consultar empresa individual e visão consolidada.
- [ ] O reset recria um ambiente completo e reproduzível.
- [ ] `manage.py check` passa sem erros.
- [ ] Todos os testes automatizados passam.
- [ ] Fluxo manual completo é validado em ambiente de desenvolvimento.

## Registro de decisões

- **D1 — Motor único:** regras de acesso e conclusão ficam em serviços centrais.
- **D2 — Segurança:** backend é a autoridade; o navegador não decide conclusão.
- **D3 — Evidência:** telemetria prova consumo técnico, não atenção humana.
- **D4 — Desenvolvimento:** dados de teste podem ser recriados; não há legado produtivo a preservar.
- **D5 — Padrão enterprise:** cursos obrigatórios usam progressão linear e avaliação quando aplicável.

## Histórico de execução

| Data | Fase | Alteração | Validação | Responsável |
|---|---|---|---|---|
| 18/09/2026 | Base | Conversão `User` → `TenantUser` em matrícula e conteúdo | Fluxos principais retornando HTTP 200 | Codex |
| 18/09/2026 | Gamificação | Configuração opcional e seed demo | Matrícula sem `GamificationSettings` não falha | Codex |
| 18/09/2026 | Documento | Checklist inicial criada | Documento versionado no repositório | Codex |

## Fontes comparativas

- LearnDash — Course Progression: <https://learndash.com/support/kb/add-ons/courses/course-progression/>
- LearnDash — Course Enrollment Mode: <https://learndash.com/support/kb/core/courses/course-enrollment-mode/>
- LearnDash — Lesson Display and Content Settings: <https://learndash.com/support/kb/add-ons/lessons/lesson-display-content/>
