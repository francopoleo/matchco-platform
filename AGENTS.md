# Regra de manutenção do MatchCo

## Atualizar o Help junto com cada mudança

Toda alteração no sistema deve atualizar a documentação central HTML e o Help contextual relacionado.

Isso vale para:

- novas rotas, URLs ou pontos de entrada;
- mudanças de login, permissões, tenant ou audiência;
- novos modelos, estados, programas, QRs ou convites;
- alterações de fluxo para candidato, colaborador, lojista, shopping ou parceiro;
- mudanças visuais que alterem a forma de usar uma página;
- novas integrações, cursos, Feed, Wiki, documentos ou certificações.

Antes de concluir uma mudança:

1. Atualize `/console/documentacao/`.
2. Atualize ou crie o documento HTML da categoria correspondente em `/console/documentacao/<categoria>/`.
3. Atualize `matchco/console/contextual_docs.py` quando a mudança tiver uma tela operacional específica.
4. Adicione ou ajuste o link no widget de Help contextual.
5. Verifique claro/escuro, mobile e os links da documentação.
6. Execute `manage.py check` e valide o template HTML.

A documentação não deve expor nomes técnicos de campos como explicação principal. Primeiro vem o significado para a pessoa; o código interno fica como referência secundária.
