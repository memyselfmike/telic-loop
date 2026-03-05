# ADR-0009: Use React Islands for Interactive Components

## Status
Accepted

## Context
While the marketing website is primarily static content, certain components require client-side interactivity:
- Contact form with validation, loading states, and API submission
- Mobile navigation menu with toggle state and animations
- Potentially future interactive features (newsletter signup, live chat, etc.)

We needed to decide how to implement these interactive features while maintaining the performance benefits of a static site. Candidates considered:
- **React islands via Astro** — Selective hydration of React components
- **Vanilla JavaScript** — Plain JavaScript for all interactivity
- **Vue/Svelte islands** — Alternative framework islands in Astro
- **Full React SPA** — Convert entire site to React
- **Web Components** — Custom elements with shadow DOM

## Decision
We chose **React 19 islands** via Astro's `@astrojs/react` integration with selective hydration.

Key factors:
1. **Minimal JavaScript** — Only components that need interactivity ship JavaScript to the browser
2. **Familiar technology** — React is widely known, making the codebase accessible to most developers
3. **Component ecosystem** — Can leverage React hooks and npm packages if needed
4. **Selective hydration** — Astro's `client:load`, `client:visible`, `client:idle` directives provide fine-grained control
5. **Type safety** — TypeScript works seamlessly with React components
6. **Future flexibility** — Easy to add more interactive features as needed

## Consequences

### Positive
- Interactive components (ContactForm, MobileNav) have full React capabilities (hooks, state management, lifecycle methods)
- Non-interactive components remain as static `.astro` files with zero JavaScript overhead
- Can use React DevTools for debugging interactive components
- Easy to integrate third-party React libraries if needed (form validation, UI components)
- Developers familiar with React can contribute immediately
- TypeScript types ensure type-safe props between Astro and React components

### Negative
- Requires learning Astro's hydration directives (`client:load`, `client:visible`, etc.)
- Adds React to the dependency tree (~45KB gzipped runtime per island)
- Potential for developers to overuse React when static components would suffice
- Multiple framework contexts (switching between `.astro` and `.tsx` files)

### Mitigations
- Clear documentation on when to use React islands vs static Astro components
- Code review process ensures React is only used where interactivity is genuinely needed
- Astro's `client:visible` directive lazy-loads islands only when they enter the viewport
- Contact form uses `client:load` (needed immediately), mobile nav uses `client:idle` (can wait)

### Implementation Details

**React islands in this project**:
1. **ContactForm.tsx** (`client:load`)
   - Form state management (name, email, company, message)
   - Client-side validation (required fields, email format)
   - Loading state during API submission
   - Success/error message display
   - POST to Payload CMS `/api/form-submissions`

2. **MobileNav** (inline script, not React)
   - Toggle state for menu open/closed
   - Body scroll lock when menu is open
   - Close on link click or escape key
   - Note: Implemented as vanilla JS to avoid loading React for simple toggle behavior

**Hydration strategy**:
- `client:load` — Hydrate immediately on page load (ContactForm)
- `client:idle` — Hydrate when browser is idle (future features)
- `client:visible` — Hydrate when scrolled into viewport (future features)

### Alternative Considered: Vanilla JavaScript
We considered implementing the contact form in vanilla JavaScript to avoid React entirely. This would reduce bundle size by ~45KB but would:
- Lose type safety for component state
- Require manual DOM manipulation and event handling
- Be harder to test (no React Testing Library)
- Make future feature additions more difficult

For a marketing site with minimal interactivity, the 45KB trade-off is acceptable for the developer experience benefits.

### Future Considerations
If the site requires more complex client-side features (user dashboards, real-time updates, complex forms), consider:
1. Migrating to Next.js for full React SSR/SSG
2. Adding state management (Zustand, Redux) if shared state is needed
3. Using React Query for API data fetching and caching
4. Implementing progressive enhancement (core functionality works without JS)
