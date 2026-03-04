# ADR-0003: Vanilla JavaScript Frontend Without Framework

## Status
Accepted

## Context

The PRD specifies "a vanilla HTML/CSS/JS frontend" with "no build step, no framework" and requirements for a "visually polished web app that feels like a real product."

Options considered:

1. **Vanilla JavaScript** - Plain HTML/CSS/JS with browser APIs
2. **React** - Popular, component-based, requires build step
3. **Vue** - Lighter than React, easier learning curve
4. **Svelte** - Compiles to vanilla JS, no runtime
5. **Alpine.js** - Minimal framework, no build required

## Decision

We will build the frontend using vanilla JavaScript with the IIFE (Immediately Invoked Function Expression) pattern for modular code organization.

Architecture:
- Single `index.html` file (SPA)
- Modular CSS with custom properties (`variables.css`, `base.css`, `components.css`)
- JavaScript modules using IIFE pattern with global namespace (`window.BookAPI`, `window.Library`, etc.)
- Native Fetch API for HTTP requests
- No transpilation, no bundling, no build step

## Consequences

### What Becomes Easier

- **Zero build complexity**: No webpack, vite, or rollup configuration
- **Instant feedback**: Edit file, refresh browser, see changes
- **Small bundle size**: No framework overhead (~50KB total JS vs 150KB+ for frameworks)
- **Fast page loads**: Direct browser parsing, no virtual DOM reconciliation
- **Simple deployment**: Copy static files to nginx, done
- **Standard APIs**: Uses Fetch, DOM manipulation, EventTarget directly
- **Easy debugging**: No source maps needed, code runs as-written

### What Becomes More Difficult

- **Manual DOM management**: No reactive bindings, must update DOM explicitly
- **Code organization**: Requires discipline to avoid global namespace pollution
- **Repetitive code**: No component reuse system (mitigated with functions)
- **State management**: No built-in reactivity, must manage manually
- **Browser compatibility**: Must check API support (though modern browsers are consistent)

### Mitigations

- Use IIFE pattern to create pseudo-modules with private state
- Expose public APIs on `window` object for inter-module communication
- Create reusable render functions (e.g., `renderStars()`, `renderBookCard()`)
- Use CSS custom properties for theme consistency
- Document module boundaries and responsibilities clearly
- Leverage modern browser APIs (Fetch, async/await) without polyfills

### Design Patterns Used

**IIFE Modules**:
```javascript
(function() {
  let privateState = [];

  window.ModuleName = {
    publicMethod: function() { /* ... */ }
  };
})();
```

**Event Delegation**: Attach listeners to parent elements for dynamic content

**Debouncing**: Limit expensive operations (search input → API call)

**Toast Notifications**: Global `window.Toast` for user feedback

### Alternative Considered

**Alpine.js** was considered as it provides reactivity without a build step, but:
- Still adds 15KB framework code
- Introduces new syntax/learning curve
- Vanilla JS is sufficient for this app's complexity
- PRD explicitly requests "no framework"
