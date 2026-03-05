# ADR-0001: Use Astro for Static Site Generation

## Status
Accepted

## Context
We needed to choose a frontend framework for a marketing website that would:
- Deliver exceptional performance (fast page loads, minimal JavaScript)
- Support static site generation for SEO and deployment simplicity
- Allow interactive components where needed (forms, mobile navigation)
- Work well with a headless CMS architecture
- Provide excellent developer experience

Candidates considered:
- **Next.js** — Popular React framework with SSR/SSG capabilities
- **Gatsby** — Established static site generator for React
- **Astro** — Modern static site generator with partial hydration
- **Nuxt** — Vue-based framework with SSG support

## Decision
We chose **Astro 5.x** as the frontend framework.

Key factors:
1. **Zero JavaScript by default** — Astro ships no client-side JavaScript unless explicitly needed, resulting in faster initial page loads and better Core Web Vitals scores
2. **Partial hydration (Islands Architecture)** — Only interactive components (ContactForm, MobileNav) are hydrated with React, keeping the bundle size minimal
3. **Multi-framework support** — Can use React for islands while keeping the majority of the site as static `.astro` components
4. **File-based routing** — Simple, intuitive routing model for marketing pages
5. **Build performance** — Faster build times than Gatsby for primarily static content
6. **Content-first focus** — Designed specifically for content-driven sites like blogs and marketing pages

## Consequences

### Positive
- Excellent Lighthouse scores (90+ across all metrics) due to minimal JavaScript
- Fast development iteration with hot module reloading
- Easy integration with Payload CMS REST API via `fetch()` at build time
- Simple mental model for developers unfamiliar with complex React data fetching patterns
- Smaller bundle sizes compared to full React applications

### Negative
- Smaller ecosystem compared to Next.js (fewer plugins and integrations)
- Less community support and tutorials compared to established frameworks
- React islands require explicit `client:load` or `client:visible` directives, which can be forgotten
- No built-in image optimization (though this can be added via integrations)

### Mitigations
- For any features requiring extensive ecosystem support, we can add Astro integrations or custom implementations
- Documentation and code comments explicitly note where React islands are used
- Image optimization is handled by Payload CMS (responsive sizes) and Pixabay pre-fetching
