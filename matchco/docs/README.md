# Documentação do MatchCo

## Consulte primeiro

Para desenvolvimento, use somente [`atual/`](atual/):

- [`atual/CONTRATO_RECRUTAMENTO.md`](atual/CONTRATO_RECRUTAMENTO.md): fonte de
  verdade do fluxo de Cargo, Perfil, Necessidade, Oportunidade e Match.
- [`atual/PLANO_IMPLEMENTACAO.md`](atual/PLANO_IMPLEMENTACAO.md): lista curta
  do que ainda falta implementar.
- [`atual/PADRAO_CONSOLE.md`](atual/PADRAO_CONSOLE.md): padrão das páginas,
  formulários, tabelas, abas, tema escuro e responsividade.
- [`help/html/03_RECRUITMENT_APRESENTACAO_VENDAS.html`](help/html/03_RECRUITMENT_APRESENTACAO_VENDAS.html):
  apresentação comercial vinculada ao contrato.

## Estrutura

- `atual/`: documentos vigentes para decisão e desenvolvimento.
- `help/html/`: documentação operacional publicada pelo Console.
- `legacy/`: documentos antigos preservados apenas para consulta. Não usar
  como fonte de implementação nova.

## Regra de atualização

Uma mudança de regra deve atualizar o contrato atual. Depois, revise a
apresentação comercial, o plano de pendências e o Help contextual relacionado.
Execute `manage.py check`, a verificação da apresentação e `git diff --check`.

Não criar uma nova checklist para substituir a documentação atual. Se um
documento antigo voltar a ser necessário, a decisão precisa ser incorporada
primeiro em `atual/`.
