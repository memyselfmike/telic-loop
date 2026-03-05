# ADR-0004: Use Custom CSS Design System Over Tailwind

## Status
Accepted

## Context
We needed to implement a dark-themed, animation-rich design inspired by the Nexus v3 digital agency template. The design required:
- Dark color palette with glass-morphism effects
- Custom gradients and shadows
- Complex scroll-triggered animations
- Consistent spacing, typography, and color tokens
- Responsive breakpoints for mobile, tablet, and desktop

Candidates considered:
- **Tailwind CSS** — Utility-first CSS framework
- **Custom CSS with design tokens** — CSS custom properties with traditional stylesheets
- **Styled Components / CSS-in-JS** — Component-scoped styles
- **CSS Modules** — Scoped CSS files per component

## Decision
We chose a **custom CSS design system** using CSS custom properties (design tokens) with traditional stylesheets.

Key factors:
1. **Full design control** — The Nexus-inspired design requires specific gradients, glass-morphism backdrop filters, and animations that don't map cleanly to utility classes
2. **Smaller bundle size** — Only the CSS actually used is shipped (no multi-megabyte utility class library)
3. **Animation complexity** — Custom `@keyframes` and Intersection Observer integrations are more maintainable with traditional CSS
4. **Design tokens** — CSS custom properties provide the same consistency benefits as Tailwind's design system
5. **Learning opportunity** — Demonstrates modern CSS techniques (custom properties, `backdrop-filter`, `@keyframes`, grid, flexbox)

## Consequences

### Positive
- Complete control over the design system (no framework constraints)
- Smaller CSS bundle (~15KB vs Tailwind's 3MB+ development build or ~50KB+ production build)
- Easier to implement complex animations (staggered entrances, parallax, counters) without fighting utility class abstractions
- Clean component markup without dozens of utility classes
- Better suited for bespoke designs that don't follow standard UI patterns
- CSS custom properties in `tokens.css` provide a single source of truth for colors, spacing, shadows, etc.

### Negative
- Slower initial development compared to Tailwind's rapid prototyping
- No built-in purging mechanism (though unused CSS is minimal with custom approach)
- Developers must understand CSS specificity and cascade rules
- Less "copy-paste" examples from the community (Tailwind has extensive examples)

### Mitigations
- Design token system (`tokens.css`) reduces repetition and ensures consistency
- Component styles are scoped to prevent cascade issues
- Global styles (`global.css`) handle base resets and typography
- Animation system (`animations.css` + `animations.js`) is reusable across all components
- Well-documented design tokens make it easy for future developers to maintain consistency
