# Documentação atual do MatchCo

Esta é a pasta de consulta diária para desenvolvimento. O material antigo fica
em `../legacy/` e não deve orientar novas telas, regras ou modelos.

## Ordem de leitura

1. [Contrato de Recrutamento](CONTRATO_RECRUTAMENTO.md) — fonte de verdade do
   fluxo Cargo, Perfil, Necessidade, Oportunidade e Match.
2. [Plano de implementação](PLANO_IMPLEMENTACAO.md) — somente pendências
   atuais, ordem de execução e critérios de aceite.
3. [Padrão do Console](PADRAO_CONSOLE.md) — checklist visual e de experiência
   para novas telas e ajustes.
4. [Apresentação comercial](../help/html/03_RECRUITMENT_APRESENTACAO_VENDAS.html)
   — visão simples para cliente e candidato, vinculada ao contrato.

## Regra de atualização

Quando uma regra mudar:

1. atualize o contrato;
2. atualize a apresentação comercial;
3. atualize o plano somente se surgir ou terminar uma pendência;
4. atualize o Help contextual e a documentação operacional da tela;
5. execute `manage.py check`, a verificação da apresentação e `git diff --check`.

Não usar arquivos de `legacy` como fonte para uma implementação nova. Se uma
decisão antiga voltar a ser considerada, ela deve ser reescrita no contrato
atual antes de entrar no código.
