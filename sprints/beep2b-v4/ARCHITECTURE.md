# Architecture — Beep2B v4

## Docker Compose Services

| Service | Image/Build | Port | Purpose |
|---------|------------|------|---------|
| **frontend** | Custom (node:20-alpine) | 4321 | Astro dev server |
| **cms** | Custom (node:20-alpine) | 3000 | Payload CMS admin + API |
| **db** | mongo:7 | 27017 | MongoDB for Payload |

### docker-compose.yml Requirements

- `docker compose up` starts everything — no manual setup steps
- MongoDB uses a named volume (`mongodata`) for persistence
- CMS depends on db (healthcheck: mongosh --eval "db.adminCommand('ping')")
- Frontend depends on CMS being healthy
- CMS environment: `MONGODB_URI=mongodb://db:27017/beep2b`, `PAYLOAD_SECRET=beep2b-dev-secret-key`, `PAYLOAD_CONFIG_PATH=src/payload.config.ts`
- Frontend environment: `CMS_URL=http://cms:3000` for API calls during build/dev
- Both custom services use `npm install && npm run dev` for development mode

## Astro Frontend (port 4321)

- **Astro 5.x** with `@astrojs/react` for interactive islands
- **CSS**: Custom CSS with CSS custom properties (design tokens) — NO Tailwind
- **Animations**: CSS `@keyframes` + Intersection Observer for scroll-triggered reveals
- **Pixabay**: Server-side fetch at build/dev time for hero/section backgrounds
- Pages are `.astro` files, interactive components (contact form, mobile nav) are React islands

### Page Routes

| Route | Page |
|-------|------|
| `/` | Home — hero, features, BEEP preview, testimonials, CTA |
| `/how-it-works` | BEEP methodology deep-dive (4 interactive steps) |
| `/services` | 3 service offerings with benefit lists |
| `/about` | Company story, mission, values, timeline, stats |
| `/contact` | Contact form + discovery call benefits |
| `/blog` | Blog listing with pagination (from Payload) |
| `/blog/[slug]` | Individual blog post |

## Payload CMS (port 3000)

- **Payload 3.x** with MongoDB adapter
- Admin panel at `http://localhost:3000/admin`
- REST API at `http://localhost:3000/api`

### Collections

| Collection | Fields | Purpose |
|-----------|--------|---------|
| **posts** | title, slug, author, date, categories (relationship), featuredImage (upload), excerpt, content (richText) | Blog posts |
| **categories** | title, slug | Blog categories |
| **testimonials** | name, company, role, quote, rating (1-5) | Client testimonials |
| **pages** | title, slug, sections (array of blocks) | CMS-managed page content |

### Seed Data

On first startup, seed the database with:
- 9 blog categories (Authority Marketing, B2B, LinkedIn Marketing, LinkedIn Profile, LinkedIn Tips, LinkedIn Training, Relationship Selling, Social Selling, Thought Leadership)
- 3 sample blog posts
- 3 testimonials (Sarah M., James K., Anja W. — use existing copy)
- Home page content

## Pixabay Integration

- API Key: `54899839-52cb07e8d7437ca93ecb74181`
- Endpoint: `https://pixabay.com/api/?key=API_KEY&q=QUERY&image_type=photo&orientation=horizontal&min_width=1920`
- Use at Astro build/dev time to fetch hero backgrounds, section backgrounds
- Cache downloaded images in `public/images/` so they persist
- Queries: "business office dark", "technology abstract", "networking professional", "digital marketing"
