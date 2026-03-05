# ADR-0008: Use Lexical for Rich Text Editing

## Status
Accepted

## Context
We needed a rich text editor for blog post content in the Payload CMS admin panel. Requirements included:
- Intuitive editing experience for non-technical content authors
- Support for headings, paragraphs, lists, blockquotes, links, and images
- Clean HTML output (no inline styles or legacy markup)
- Extensibility for custom formatting or embed types
- Good accessibility and keyboard navigation
- Mobile-friendly editing on tablets

Candidates considered:
- **Lexical** — Facebook's modern extensible text editor framework
- **Slate** — Fully customizable framework for building rich text editors
- **TinyMCE** — Popular WYSIWYG editor (freemium)
- **CKEditor** — Another popular WYSIWYG editor (freemium)
- **Markdown** — Plain text markup (not WYSIWYG)
- **ProseMirror** — Extensible rich text editing toolkit

## Decision
We chose **Lexical** via Payload's `@payloadcms/richtext-lexical` integration.

Key factors:
1. **Payload CMS integration** — First-class support via official `@payloadcms/richtext-lexical` package
2. **Modern architecture** — Built by Facebook (Meta) with lessons learned from Draft.js
3. **Extensibility** — Plugin architecture makes it easy to add custom nodes or formatting
4. **Accessibility** — Strong focus on keyboard navigation and screen reader support
5. **Clean output** — Generates semantic HTML without inline styles or legacy markup
6. **Framework agnostic** — Can be used outside of React if needed
7. **Active development** — Maintained by Meta with regular updates

## Consequences

### Positive
- Content editors get a clean, intuitive WYSIWYG interface for blog posts
- Structured content output (Lexical's JSON format) can be rendered consistently across different frontends
- Extensible plugin system allows adding custom features (e.g., callout boxes, embedded tweets)
- Auto-generated TypeScript types for rich text content via Payload
- Accessibility features ensure content is editable by keyboard-only users
- Mobile-responsive editor works on tablets for on-the-go content editing

### Negative
- Lexical is newer and less mature than TinyMCE/CKEditor (smaller ecosystem of plugins)
- Custom plugins require understanding Lexical's node system (steeper learning curve than simpler editors)
- Rendering Lexical JSON on the frontend requires a rendering component (`RichText.astro`)
- Migration from other rich text formats (Markdown, HTML) requires transformation logic

### Mitigations
- Payload's Lexical integration provides default plugins for common formatting (headings, lists, links, images)
- `RichText.astro` component handles rendering Lexical JSON to HTML on the frontend
- Documentation from Payload and Lexical covers most common use cases
- For advanced features, can extend with custom Lexical plugins or fall back to raw HTML blocks

### Implementation Details
1. **CMS configuration** — `@payloadcms/richtext-lexical` configured in `payload.config.ts`
2. **Blog post schema** — `content` field uses `richText` type with Lexical editor
3. **Frontend rendering** — `RichText.astro` component converts Lexical JSON to HTML
4. **Supported formatting** — Headings (H1-H6), paragraphs, bold, italic, underline, strikethrough, lists (ordered/unordered), blockquotes, links, images

### Future Enhancements
1. Add custom Lexical plugins for callout boxes, code blocks with syntax highlighting
2. Implement embedded content (YouTube videos, tweets) via custom nodes
3. Add word count or reading time estimation in the editor
4. Enable collaborative editing (Lexical supports Yjs for real-time collaboration)
