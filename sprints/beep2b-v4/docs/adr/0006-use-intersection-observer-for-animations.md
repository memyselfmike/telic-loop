# ADR-0006: Use Intersection Observer for Scroll-Triggered Animations

## Status
Accepted

## Context
We needed to implement scroll-triggered animations for a premium user experience, including:
- Fade-in and slide-up effects when sections enter the viewport
- Staggered entrance animations for grid items
- Animated number counters for statistics
- Parallax background scroll effects

Performance and accessibility were critical concerns. Candidates considered:
- **Intersection Observer API** — Browser API for observing element visibility
- **Scroll event listeners** — Traditional `window.addEventListener('scroll', ...)`
- **CSS-only animations** — Using `animation-delay` and `animation-play-state`
- **Third-party libraries** — AOS (Animate On Scroll), ScrollReveal, GSAP ScrollTrigger

## Decision
We chose the **Intersection Observer API** with custom JavaScript implementation.

Key factors:
1. **Performance** — Intersection Observer is optimized by the browser and doesn't block the main thread (unlike scroll event listeners)
2. **Precise control** — Trigger animations exactly when elements enter the viewport with configurable threshold
3. **Battery friendly** — No continuous scroll event polling, only fires when intersection state changes
4. **Progressive enhancement** — Pages render correctly without JavaScript (animations just don't trigger)
5. **Small bundle size** — Custom implementation is ~3KB (vs 10KB+ for third-party libraries)
6. **Complex interactions** — Supports staggered child animations, number counters, and parallax effects

## Consequences

### Positive
- Smooth 60fps animations without scroll event jank
- Declarative API via HTML data attributes (`data-animate="fade-in"`, `data-stagger`, `data-counter`)
- Reusable across all components without duplicating animation logic
- Automatically handles elements added dynamically (observes all matching elements on page load)
- No external dependencies (uses native browser API)
- Accessible (respects `prefers-reduced-motion` media query)

### Negative
- Requires JavaScript (pages without JS don't show animations)
- IE11 not supported (though IE11 is no longer relevant in 2026)
- Initial implementation more complex than CSS-only animations
- Must manually observe elements (not automatic like CSS)

### Mitigations
- Progressive enhancement: Content is fully visible and functional without JavaScript
- Animation script is small and loads quickly (non-blocking)
- Fallback for `prefers-reduced-motion`: Animations are disabled for users who prefer reduced motion
- Well-documented data attributes make it easy for developers to add animations to new components

### Implementation Details
Animation system consists of:
1. **animations.css** — CSS `@keyframes` for fade-in, slide-up, slide-left, slide-right, scale-in
2. **animations.js** — Intersection Observer setup, stagger logic, counter animation, parallax
3. **HTML data attributes** — `data-animate`, `data-stagger`, `data-counter`, `data-parallax`

Example usage:
```html
<div data-animate="fade-in">Fades in when scrolled into view</div>
<div data-stagger>
  <div>Appears first</div>
  <div>Appears 100ms later</div>
  <div>Appears 200ms later</div>
</div>
<span data-counter="500">Animates from 0 to 500</span>
```
