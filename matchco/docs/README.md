# Documentação do MatchCo

Esta é a única raiz de documentação do projeto.

## Estrutura

- `help/html/`: fonte publicada da Central de Documentação do Console. Os
  checklists exibidos no Help vivem aqui e cada checklist deve ter uma única
  fonte HTML.
- `development/`: arquitetura, decisões técnicas, setup, operação e
  documentação específica dos módulos. Inclui `GUIDES/`, `REFERENCES/` e os
  documentos técnicos dos módulos.
- `archive/`: materiais históricos preservados para consulta, sem uso como
  fonte ativa do Help.

## Regras

1. Documentação exibida no produto deve ser HTML em `help/html/`.
2. Documentação de desenvolvimento deve ficar em `development/`.
3. Materiais antigos devem ir para `archive/`, nunca para o índice ativo.
4. Ao criar ou alterar uma rota, atualizar a matriz
   `help/html/00_MATCHCO_CANONICAL_URLS.html` e o índice do Help.
5. Não criar uma segunda versão de checklist para a mesma funcionalidade.

## Comece por aqui

- [`development/MATCHCO_CARTOGRAPHER.md`](development/MATCHCO_CARTOGRAPHER.md):
  mapa único, fontes de verdade, inventário e regras contra duplicação.
- [`development/MATCHCO_MASTER_PLAN.md`](development/MATCHCO_MASTER_PLAN.md):
  visão consolidada do produto e fases de desenvolvimento.
- [`development/MATCHCO_VALIDATION_PLAN.md`](development/MATCHCO_VALIDATION_PLAN.md):
  contrato detalhado e checkboxes de execução.

O Console lê a Central de Documentação diretamente de `docs/help/html/`.
