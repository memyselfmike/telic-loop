# ADR-0007: Use Pixabay API for Background Images

## Status
Accepted

## Context
We needed high-quality background images for the hero section and various page sections. Requirements included:
- Professional, business-oriented imagery (office scenes, technology, networking)
- Dark-themed or easily overlaid with dark gradients
- Horizontal orientation (landscape) for hero backgrounds
- High resolution (1920px+ width) for modern displays
- Free to use commercially (no licensing costs)

Candidates considered:
- **Stock photo APIs** — Unsplash, Pexels, Pixabay
- **Manual curation** — Download and commit images to repository
- **Paid stock photos** — Shutterstock, Getty Images
- **AI-generated images** — Midjourney, DALL-E, Stable Diffusion

## Decision
We chose **Pixabay API** for background image sourcing with local caching.

Key factors:
1. **Free API access** — No costs for commercial use (CC0 license)
2. **High-quality images** — Professional photography suitable for business context
3. **Generous API limits** — 100 requests/minute, sufficient for development and build-time fetching
4. **No attribution required** — CC0 license allows use without crediting photographer
5. **Flexible search** — Can query by keywords ("business office dark", "technology abstract")
6. **Server-side fetching** — Images downloaded at build time and cached locally (not fetched by client browsers)

## Consequences

### Positive
- No manual image curation required (API provides filtered, high-quality results)
- Images cached in `frontend/public/images/` for offline development and faster builds
- Easy to refresh images by re-running `npm run fetch-images` script
- No licensing fees or attribution requirements
- Fallback to solid gradients if API is unavailable (resilient to network issues)

### Negative
- Dependency on external API (though mitigated by local caching)
- Images not unique to Beep2B (other sites may use the same Pixabay images)
- API key must be managed (currently hardcoded in `pixabay.ts`, should be moved to environment variable)
- Image quality and relevance depend on search query accuracy

### Mitigations
- Local caching in `public/images/` ensures images are available even if Pixabay API is down
- `fetch-images.ts` script can be run manually to refresh images when needed
- Fallback gradient backgrounds ensure pages render correctly even without images
- For production, images can be manually curated and committed to repository (removing Pixabay dependency)
- API key should be moved to `.env` file to avoid exposing it in source code

### Future Improvements
1. Move API key to environment variable (`PIXABAY_API_KEY`)
2. Add image optimization (resize, compress) before caching
3. Consider switching to manually curated images for better brand uniqueness
4. Implement lazy loading for background images to improve initial page load
