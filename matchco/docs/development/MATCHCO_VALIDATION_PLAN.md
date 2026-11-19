# Plano atual de implementação do Recrutamento Match

**Versão:** 2.1.0
**Data:** 2026-11-19
**Estado:** contrato definido; implementação incremental pendente

Este arquivo não é histórico. Ele contém somente o que ainda precisa ser
implementado ou validado. Decisões de produto, perguntas, respostas, exemplos,
papéis e regras completas ficam no documento canônico:

`docs/development/recruitment/SISTEMA_MATCHCO_CANONICO.md`

A apresentação comercial vinculada é:

`docs/help/html/03_RECRUITMENT_APRESENTACAO_VENDAS.html`

Se houver conflito, o documento canônico vence. Se o contrato mudar, a
apresentação deve ser revisada e o vínculo deve ser validado com:

```bash
./.venv/bin/python scripts/check_recruitment_presentation_contract.py
```

## O que já está decidido

- Recrutamento Match é sem currículo e sem lista pública de vagas.
- O Perfil pertence à pessoa e pode ser reutilizado.
- O RH mantém o Cargo; a MatchCo mantém as funções e respostas canônicas.
- O gerente escolhe um Cargo aprovado e declara uma Necessidade local.
- O Match é bilateral: interesse da pessoa + interesse da unidade.
- Não existe pontuação, classificação ou ranking de candidatos.
- O contato só é liberado depois do Match e da autorização correspondente.
- Portal e Console são interfaces diferentes do mesmo fluxo do servidor.
- Rede, shopping, empresa e unidade permanecem em seus próprios escopos.

Não reabrir essas decisões em novas telas ou modelos sem uma revisão formal do
contrato canônico.

## O que falta implementar

### 1. Catálogo único de funções e respostas

- [ ] Consolidar os termos publicados de funções, segmentos, ambientes,
  experiências, intenções, disponibilidade e circulação.
- [ ] Garantir que `caixa`, `Caixa de loja`, `Operador de caixa` e `Frente de
  caixa` sejam resolvidos por busca para termos canônicos, sem duplicação.
- [ ] Permitir múltipla escolha no Perfil e guardar cada resposta com origem,
  finalidade, escopo e data de confirmação.
- [ ] Publicar os catálogos iniciais para varejo, farmácia, franquia,
  alimentação, shopping, estoque e logística.
- [ ] Impedir que RH ou gerente criem perguntas e respostas livres para o
  cálculo de elegibilidade.

**Aceite:** o mesmo candidato pode responder `Caixa de loja` uma vez e essa
resposta pode ser usada em oportunidades autorizadas de Drogasil, lojas de
shopping ou outras empresas, sem copiar nem expor dados fora do escopo.

### 2. Cargo mantido pelo RH

- [ ] Finalizar o formulário de Cargo com identificação, descrição, funções
  canônicas, requisitos, remuneração, benefícios, contratação e publicação.
- [ ] Classificar cada requisito como `Obrigatório`, `Desejável`, `Negociável`
  ou `Pode aprender`.
- [ ] Permitir que o Cargo `Caixa de loja sênior` seja ligado a `Caixa de loja`,
  `Operador de caixa` e `Frente de caixa`.
- [ ] Separar características do Cargo, como senioridade e remuneração, das
  funções que o candidato escolhe no Perfil.
- [ ] Exigir aprovação/publicação do RH antes de o gerente usar o Cargo.

**Aceite:** o gerente nunca cadastra outro cargo para resolver uma necessidade
local. Ele escolhe o Cargo aprovado e apenas complementa os dados da unidade.

### 3. Necessidade e Oportunidade da unidade

- [ ] Fazer o gerente escolher empresa, unidade e Cargo aprovado.
- [ ] Permitir informar quantidade, dias, período, início, formato, duração,
  prazo da rodada e campos negociáveis.
- [ ] Copiar descrição, requisitos, remuneração e funções do Cargo para uma
  versão congelada da Oportunidade.
- [ ] Criar nova versão quando houver alteração material, exigindo revisão da
  pessoa interessada.
- [ ] Bloquear publicação sem unidade, Cargo, função, condições principais e
  requisitos completos.

**Aceite:** alterar o Cargo depois da publicação não muda silenciosamente uma
Oportunidade já apresentada.

### 4. Questionário e atualização do Perfil

- [ ] Implementar o questionário único descrito na seção 19.4.1 do contrato.
- [ ] Manter identidade mínima, celular confirmado, idade, região/CEP,
  funções, experiências, segmentos, ambientes, intenção, disponibilidade,
  formato, início e autorizações.
- [ ] Tratar dias, períodos, formato e início como informações atuais que
  podem precisar de confirmação.
- [ ] Não coletar currículo, CPF, endereço completo, foto ou histórico
  desnecessário no primeiro cadastro.
- [ ] Mostrar ao candidato o motivo compreensível de cada confirmação e cada
  autorização de circulação.

### 5. Serviço único de elegibilidade

- [ ] Criar um serviço de domínio único, como `evaluate_deterministic_match`,
  usado por Portal, Console, prévia e rodada de convites.
- [ ] Retornar critérios obrigatórios, atendidos, ausentes e negociáveis.
- [ ] Representar `100%` somente como atendimento dos critérios obrigatórios;
  nunca como nota, qualidade ou probabilidade de contratação.
- [ ] Retornar mensagens compreensíveis: `Compatível`, `Compatível com
  negociação`, `Precisa confirmar disponibilidade` e `Não elegível`.
- [ ] Bloquear qualquer cálculo paralelo em modelo, consulta, JavaScript,
  modelo de página ou tela alternativa.

### 6. Rodadas de convite

- [ ] Fazer a rodada usar a mesma elegibilidade da prévia.
- [ ] Ordenar somente por proximidade aproximada e desempate estável, conforme
  consentimento e escopo territorial.
- [ ] Remover qualquer peso legado de relevância, recência ou qualidade.
- [ ] Não revelar lista nominal antes de a pessoa demonstrar interesse.
- [ ] Evitar convite duplicado e processar expiração e nova rodada.

### 7. Portal e Console com paridade

- [ ] Fazer as duas interfaces chamarem os mesmos serviços de Cargo,
  Necessidade, elegibilidade, convite, interesse, negociação, Match e resposta.
- [ ] Comparar, em testes de contrato, estado, eventos, critérios e dados
  exibidos pelas duas interfaces.
- [ ] Permitir textos diferentes para cada papel, mas não regras diferentes.
- [ ] Garantir o mesmo controle de organização, empresa, unidade,
  consentimento, versão e contato.
- [ ] Bloquear contato no Portal e no Console antes de `CONTACT_ENABLED`.

### 8. Interesse, Match e negociação

- [ ] Confirmar que a pessoa vê a oportunidade completa antes de demonstrar
  interesse.
- [ ] Mostrar à unidade somente a projeção autorizada depois do interesse da
  pessoa.
- [ ] Liberar o contato somente depois do interesse bilateral e da autorização.
- [ ] Exibir negociação somente para campos marcados como negociáveis.
- [ ] Registrar as respostas de encerramento `RC-01` a `RC-05` com explicação
  adequada e auditoria.

### 9. Estrutura de demonstração

- [ ] Validar os dados oficiais da Rede Drogasil: empresa, lojas de Lapa,
  Perdizes, Bourbon e centro de distribuição.
- [ ] Validar os dados oficiais do Bourbon Shopping: administração, empresas
  lojistas, unidades das lojas e prestadores autorizados.
- [ ] Representar o mesmo local físico em contextos diferentes sem compartilhar
  automaticamente usuários, conteúdo, audiência ou permissões.
- [ ] Criar exemplos de Cargo, Necessidade, Perfil, convite, Match e resposta
  para pelo menos Caixa de loja, Vendedor de loja e Auxiliar de estoque.

### 10. Segurança, LGPD e operação

- [ ] Testar isolamento entre organizações, empresas, shopping, rede, unidade
  e Perfil.
- [ ] Testar revogação de consentimento e pausa de circulação pela pessoa.
- [ ] Testar ausência de telefone, e-mail, endereço e CEP antes da liberação
  autorizada.
- [ ] Validar auditoria de criação, alteração de versão, interesse, Match,
  contato e encerramento.
- [ ] Confirmar os gates de idade, direitos do titular, retenção e pontos QR
  antes de uso produtivo em escala.

## Ordem recomendada

1. Catálogo e respostas canônicas.
2. Formulário de Cargo do RH.
3. Necessidade e versão da Oportunidade.
4. Questionário reutilizável do candidato.
5. Serviço único de elegibilidade.
6. Rodadas por proximidade.
7. Paridade Portal/Console.
8. Interesse, negociação, Match e respostas.
9. Dados de demonstração e testes de tenant.
10. Gates de segurança, LGPD e operação.

## Critério para considerar o fluxo pronto

O fluxo só será considerado implementado quando uma pessoa puder entrar pelo QR,
criar ou reutilizar o Perfil, responder funções canônicas, receber uma
Oportunidade baseada em um Cargo aprovado, demonstrar interesse, ser avaliada
pelos mesmos critérios no Portal e no Console, concluir um Match bilateral,
negociar apenas o permitido e receber uma resposta final auditável.

## Validação mínima a cada alteração

```bash
./.venv/bin/python matchco/manage.py check
./.venv/bin/python matchco/manage.py makemigrations --check --dry-run
./.venv/bin/python scripts/check_recruitment_presentation_contract.py
git diff --check
```

Qualquer mudança de regra, pergunta, chip, estado, permissão, rota ou mensagem
deve atualizar primeiro o contrato canônico, depois a apresentação e, por fim,
este plano de pendências.
