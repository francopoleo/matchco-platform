# Changelog do Projeto Talk/MatchCo

Todas as mudanças notáveis do projeto são documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
e este projeto segue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0-alpha.2] - 2026-07-27

### Adicionado
- Funcionalidade de auto-save para reordenação de conteúdo (drag-and-drop)
- Botões de edição (ícone de lápis) para todos os tipos de conteúdo (Text, Video, File, Quiz)
- Botões de exclusão (ícone de lixo) para itens de conteúdo
- UpdateViews para edição de conteúdo Text, Video e File
- Label "Adicionar Conteúdo" para melhor UX
- Botões de ação discretos com efeitos hover
- Tooltips em botões de ação para clareza
- Estilo de botões responsivo para mobile
- Guia VERSIONING.md para gerenciamento de releases
- CHANGELOG.md para rastreamento de mudanças

### Alterado
- Botões de ação de conteúdo melhorados de links de texto para ícones discretos
- Melhor alinhamento de botão usando flexbox
- Contexto de formulário melhorado para edit views
- Endpoint de reordenação de módulo agora trata atualizações de ordem de conteúdo
- Hierarquia visual melhorada em itens de conteúdo

### Corrigido
- Reordenação de conteúdo agora persiste corretamente para banco de dados
- Numeração de módulo recalcula em qualquer mudança de ordem
- Problemas de alinhamento de botão resolvidos
- Contexto de formulário passado corretamente para todas as edit views
- Números de conteúdo atualizam em tempo real durante drag-and-drop

### Técnico
- Criado TextUpdateView, VideoUpdateView, FileUpdateView classes
- Adicionadas rotas de URL para edição de conteúdo (text-edit, video-edit, file-edit)
- Aprimorado course_editor_detail.html com integração melhorada de Sortable.js
- Backend suporta ordem de conteúdo em lote via parâmetros POST
- Adicionado get_context_data para UpdateViews com renderização correta de template

---

## [2.0.0-alpha.1] - 2026-07-26

### Adicionado
- Interface completa do Course Editor
- Gerenciamento de módulos (criar, editar, deletar, reordenar)
- Gerenciamento de conteúdo (texto, vídeo, arquivo, quiz)
- Funcionalidade drag-and-drop para módulos usando Sortable.js
- Funcionalidade drag-and-drop para itens de conteúdo dentro de módulos
- Funcionalidade colapso/expansão de módulos com persistência em localStorage
- Sistema de auto-numeração (1., 1.1, 1.2, etc.)
- Integração do design system (Flowbite + classes customizadas)
- Indicadores visuais de drop (linhas tracejadas) para feedback de drag-and-drop
- Botões "Expandir Tudo" e "Colapsar Tudo" para módulos
- Design responsivo para mobile e desktop

### Features
- Ordenação de módulos persiste para banco de dados
- Ordenação de conteúdo persiste para banco de dados
- Atualizações de número em tempo real durante reordenação
- Links de edição de módulo
- Funcionalidade de deletar módulo
- Botões de adicionar conteúdo para cada tipo
- Organização de conteúdo em nível de módulo

### Técnico
- Implementado ModuleReorderView e ContentReorderView
- Criado template course_editor_detail.html com lógica complexa de drag-and-drop
- Integrado Sortable.js de CDN
- Utilizado localStorage para persistência de estado de colapso
- Implementada submissão de formulário adequada para atualizações de ordem
- CSS customizado para indicadores de drop com padrões de linear-gradient

---

## Política de Versionamento

- **MAJOR.MINOR.PATCH-PRERELEASE** format
- Releases alpha: Fase de desenvolvimento de features
- Releases beta: Fase de testes
- Releases RC: Testes finais antes do release
- Releases finais: Pronto para produção

---

## Como Contribuir

Ao fazer commits, use conventional commits:

- `feat:` para novas funcionalidades
- `fix:` para correções de bugs
- `docs:` para documentação
- `refactor:` para refatorações
- `perf:` para melhorias de performance
- `test:` para testes
- `chore:` para manutenção

### Exemplo
```bash
git commit -m "feat: add content reordering auto-save"
```

---

## Histórico de Releases

Veja [releases no GitHub](https://github.com/francopoleo/talk/releases) para a lista completa.

---

**Última Atualização**: 2026-10-02  
**Mantido por**: Franco  
**Repositório**: https://github.com/francopoleo/talk
