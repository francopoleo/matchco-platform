# Changelog

Todas as mudanças notáveis do projeto são documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto segue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0-alpha.2] - 2026-07-27

### Added
- Auto-save functionality for content reordering (drag-and-drop)
- Edit buttons (pencil icon) for all content types (Text, Video, File, Quiz)
- Delete buttons (trash icon) for content items
- UpdateViews for Text, Video, and File content editing
- "Adicionar Conteúdo" label for better UX
- Discrete icon buttons with hover effects
- Tooltips on action buttons for clarity
- Mobile-responsive button styling
- VERSIONING.md guide for release management
- CHANGELOG.md for tracking changes

### Changed
- Improved content action buttons from text links to discrete icons
- Better button alignment using flexbox
- Enhanced form context for edit views
- Backend module-reorder endpoint now handles content order updates
- Improved visual hierarchy in content items

### Fixed
- Content reordering now properly persists to database
- Module numbering recalculates on any order change
- Button alignment issues resolved
- Form context properly passed to all edit views
- Content numbers update in real-time during drag-and-drop

### Technical
- Created TextUpdateView, VideoUpdateView, FileUpdateView classes
- Added URL routes for content editing (text-edit, video-edit, file-edit)
- Enhanced course_editor_detail.html with improved Sortable.js integration
- Backend supports batch content order via POST parameters
- Added get_context_data to UpdateViews for proper template rendering

## [2.0.0-alpha.1] - 2026-07-26

### Added
- Complete Course Editor interface
- Module management (create, edit, delete, reorder)
- Content management (text, video, file, quiz)
- Drag-and-drop functionality for modules using Sortable.js
- Drag-and-drop functionality for content items within modules
- Module collapse/expand functionality with localStorage persistence
- Auto-numbering system (1., 1.1, 1.2, etc.)
- Design system integration (Flowbite + custom classes)
- Visual drop indicators (dashed lines) for drag-and-drop feedback
- "Expandir Tudo" and "Colapsar Tudo" buttons for modules
- Responsive design for mobile and desktop

### Features
- Module ordering persists to database
- Content ordering persists to database
- Real-time number updates during reordering
- Edit module links
- Delete module functionality
- Add content buttons for each type
- Module-level content organization

### Technical
- Implemented ModuleReorderView and ContentReorderView
- Created course_editor_detail.html template with complex drag-and-drop logic
- Integrated Sortable.js from CDN
- Used localStorage for collapse state persistence
- Implemented proper form submission for order updates
- Custom CSS for drop indicators with linear-gradient patterns

---

## Versioning Policy

- **MAJOR.MINOR.PATCH-PRERELEASE** format
- Alpha releases: Feature development phase
- Beta releases: Testing phase
- RC releases: Final testing before release
- Final releases: Production ready

## Como Contribuir

Ao fazer commits, use conventional commits:
- `feat:` para novas funcionalidades
- `fix:` para correções de bugs
- `docs:` para documentação
- `refactor:` para refatorações
- `perf:` para melhorias de performance
- `test:` para testes

Example: `git commit -m "feat: add content reordering auto-save"`

---

**Last Updated**: 2026-07-27  
**Maintained by**: Franco  
**Repository**: https://github.com/francopoleo/talk
