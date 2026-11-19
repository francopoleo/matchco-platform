# Padrão atual das páginas do Console

Checklist curto para desenvolver ou revisar qualquer página administrativa.
Este documento registra o padrão visual consolidado nas páginas ajustadas do
Console. Ele não substitui o contrato de negócio de Recrutamento.

## Estrutura da página

- [ ] Usar o shell padrão do Console, com navegação lateral, barra superior e
  área de conteúdo responsiva.
- [ ] Usar `grupo > página` como breadcrumb discreto, fora dos cartões.
- [ ] Não repetir o grupo do menu como eyebrow azul.
- [ ] Não colocar breadcrumb dentro de um card.
- [ ] Usar um único título principal, em escala moderada.
- [ ] Usar texto de apoio curto, direto e em português do Brasil.
- [ ] Não colocar botão “Voltar” quando o breadcrumb resolve a navegação.

## Cartões, indicadores e tabelas

- [ ] Usar cartões neutros, com borda e superfície do tema, sem excesso de
  arredondamento.
- [ ] Usar indicadores somente em páginas de resumo; formulários não recebem
  cartões de indicador sem necessidade.
- [ ] Indicadores devem ter ícone SVG discreto, cor semântica e texto curto.
- [ ] Usar tabela quando houver comparação de vários registros ou estados.
- [ ] Tabela deve ter cabeçalho claro, linhas com divisor do tema e nenhuma
  linha branca ou fundo preto no modo escuro.
- [ ] Usar estados vazios, carregamento, erro e confirmação no mesmo padrão.
- [ ] Em telas densas, preferir abas ou seções agrupadas a longas colunas de
  texto.

## Abas e navegação interna

- [ ] Usar abas no padrão Flowbite: linha inferior, aba ativa com sublinhado e
  ícone SVG discreto.
- [ ] Cada aba deve representar uma parte real da tarefa, não duplicar itens do
  menu lateral.
- [ ] Não criar abas que apenas redirecionam para páginas já existentes no menu.
- [ ] Em formulários de conteúdo, manter a ordem: identificação, conteúdo,
  versão/anexos e acesso/audiência, somente quando houver essas partes.
- [ ] Se houver uma única opção, remover a aba desnecessária.

## Formulários

- [ ] Agrupar campos por significado e não por modelo técnico.
- [ ] Manter labels acima dos campos, com espaço visível.
- [ ] Usar campos com borda, raio moderado e altura consistente.
- [ ] Evitar inputs e botões excessivamente arredondados.
- [ ] Usar checkbox quadrado com cantos levemente arredondados, nunca circular.
- [ ] Mostrar ajuda, erro e obrigatório próximos ao campo.
- [ ] Usar mensagens de validação em português do Brasil, inclusive as nativas
  quando forem substituídas por validação própria.
- [ ] Manter botões primários, secundários e destrutivos com as mesmas cores e
  estados em todo o Console.

## Tema, idioma e responsividade

- [ ] Testar claro e escuro; textos do menu e superfícies devem manter contraste.
- [ ] Usar tokens do tema e classes compartilhadas, evitando CSS local
  sobreposto.
- [ ] Testar telas estreitas, tabelas com rolagem e formulários em uma coluna.
- [ ] Revisar toda string visível em português do Brasil.
- [ ] Não deixar nomes técnicos, inglês ou mensagens de biblioteca expostos ao
  usuário sem tradução adequada.

## Regras de implementação

- [ ] Reutilizar componentes, classes e macros existentes antes de criar CSS.
- [ ] Não copiar uma variação antiga de outra página sem verificar este padrão.
- [ ] Não alterar regra de negócio em template ou JavaScript.
- [ ] Toda mudança visual que altere o uso deve atualizar o Help contextual.
- [ ] Validar com `manage.py check`, testes da área e `git diff --check`.
