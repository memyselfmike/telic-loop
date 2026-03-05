# ADR-0002: Use Payload CMS for Content Management

## Status
Accepted

## Context
We needed a headless CMS solution to manage blog posts, categories, testimonials, and form submissions. The CMS had to:
- Provide a visual admin interface for non-technical content editors
- Expose REST and/or GraphQL APIs for the frontend to consume
- Support rich text editing for blog content
- Be self-hosted to avoid vendor lock-in and reduce costs
- Integrate well with modern JavaScript frameworks
- Support file uploads and media management

Candidates considered:
- **Strapi** — Popular open-source headless CMS
- **Payload CMS** — Code-first headless CMS built on Next.js
- **Contentful** — Commercial headless CMS (SaaS)
- **Ghost** — Open-source blogging platform with headless API
- **Sanity** — Commercial headless CMS with generous free tier

## Decision
We chose **Payload CMS 3.x** as the headless CMS.

Key factors:
1. **Code-first configuration** — Collections defined in TypeScript files (version-controllable, easy to replicate across environments)
2. **Built on Next.js** — Familiar technology stack, easier to extend or customize
3. **Modern rich text editor** — Uses Lexical (Facebook's open-source editor), which is more extensible than traditional WYSIWYG editors
4. **Self-hosted** — Complete data ownership, no vendor lock-in, no per-seat pricing
5. **MongoDB support** — Native MongoDB adapter via `@payloadcms/db-mongodb`, fits document-based content model
6. **Dual API support** — Both REST and GraphQL APIs available out of the box
7. **TypeScript-native** — Full type safety with auto-generated TypeScript types for collections

## Consequences

### Positive
- Collections defined in code (`cms/src/collections/*.ts`) can be version-controlled and reviewed
- TypeScript types are automatically generated from collection schemas, ensuring type safety between CMS and frontend
- Customizing the admin panel or adding custom endpoints is straightforward (it's just Next.js)
- Self-hosting means predictable costs (only infrastructure, no per-user fees)
- Lexical editor provides a better content editing experience than basic markdown or legacy WYSIWYG editors
- MongoDB's flexible schema makes it easy to iterate on content models without migrations

### Negative
- Smaller community compared to Strapi (fewer plugins, less community support)
- Payload 3.x + Next.js 15 version compatibility issues encountered (admin panel routing required specific setup)
- Less mature ecosystem of third-party integrations
- Self-hosting requires managing infrastructure and updates
- Learning curve for developers unfamiliar with Payload's architecture

### Mitigations
- Payload documentation is comprehensive and well-maintained
- Next.js version compatibility issues resolved by using `next@15.3.3` with `payload@3.32.0`
- For missing integrations, we can build custom hooks or endpoints (Payload provides clear extension points)
- Infrastructure management simplified by Docker Compose for local development and standardized deployment
