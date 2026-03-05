# Architecture Documentation — Beep2B v4

## Overview

Beep2B is a modern B2B marketing website built as a decoupled architecture with three primary services: a static frontend (Astro), a headless CMS (Payload), and a document database (MongoDB). The system is designed for high performance, content flexibility, and zero-hassle deployment via Docker Compose.

The website serves as the digital presence for a B2B LinkedIn lead generation consulting company, featuring smooth animations, interactive content sections, a blog system, and a contact form—all managed through a visual admin interface.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose                            │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│   Frontend   │      │     CMS      │     │   MongoDB    │
│  (Astro 5.x) │◄─────┤ (Payload 3.x)│◄────┤   (Mongo 7)  │
│  Port: 4321  │ HTTP │  Port: 3000  │     │ Port: 27017  │
└──────────────┘      └──────────────┘     └──────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
   Static Site            REST API              Persistent
   React Islands         Admin Panel              Storage
   Animations            GraphQL API            Named Volume
```

### Service Communication

1. **Frontend → CMS**: HTTP requests to fetch blog posts, categories, testimonials via REST API (`http://cms:3000/api`)
2. **CMS → MongoDB**: Mongoose ODM connections via MongoDB URI (`mongodb://db:27017/beep2b`)
3. **User → Frontend**: Browser requests to static pages and React islands
4. **Admin → CMS**: Browser access to admin panel for content management

## Components

### 1. Frontend (Astro Application)

**Technology**: Astro 5.x static site generator with React 19 islands

**Responsibility**: Serve the public-facing marketing website with optimal performance and interactive features.

**Key Features**:
- File-based routing with `.astro` pages
- Partial hydration for interactive components (forms, mobile nav)
- Build-time data fetching from Payload CMS API
- Custom CSS design token system (no frameworks)
- Scroll-triggered animation system using Intersection Observer
- Pixabay integration for dynamic background images

**Directory Structure**:
```
frontend/src/
├── components/    # Reusable UI components
├── layouts/       # Page templates
├── lib/           # Utility functions (CMS client, Pixabay)
├── pages/         # File-based routes
├── scripts/       # Client-side JavaScript
└── styles/        # CSS design system
```

**Port**: 4321
**Container**: `node:20-alpine` with volume-mounted source code

### 2. CMS (Payload Headless CMS)

**Technology**: Payload CMS 3.x built on Next.js 15

**Responsibility**: Provide content management interface and API for blog posts, categories, testimonials, and form submissions.

**Key Features**:
- Visual admin panel at `/admin`
- REST and GraphQL APIs at `/api`
- Lexical rich text editor for blog content
- File upload handling for images
- User authentication and role-based access
- Database seeding on first startup
- CORS middleware for cross-origin requests

**Collections**:
- **Users** — Admin authentication (email/password)
- **Posts** — Blog articles with title, slug, author, date, categories, featured image, excerpt, rich text content
- **Categories** — Blog category taxonomy (title, slug)
- **Testimonials** — Client testimonials (name, company, role, quote, rating 1-5)
- **Media** — Uploaded files with responsive image sizes
- **FormSubmissions** — Contact form submissions from the website

**Port**: 3000
**Container**: `node:20-alpine` with volume-mounted source code

### 3. Database (MongoDB)

**Technology**: MongoDB 7 (official Docker image)

**Responsibility**: Persist all CMS data including users, blog posts, categories, testimonials, media metadata, and form submissions.

**Key Features**:
- Document-based NoSQL storage
- Mongoose ODM integration via Payload
- Named volume for data persistence across container restarts
- Health check via `mongosh` ping command

**Port**: 27017
**Volume**: `beep2b-mongodata` named volume mounted to `/data/db`

## Data Flow

### 1. Page Request Lifecycle (Static Pages)

```
User Browser
    │
    ▼
GET http://localhost:4321/
    │
    ▼
Astro Frontend (SSG Build)
    │
    ├─ Load page template (index.astro)
    ├─ Fetch data from CMS API (build-time)
    │   │
    │   ▼
    │   GET http://cms:3000/api/posts
    │   GET http://cms:3000/api/categories
    │   GET http://cms:3000/api/testimonials
    │       │
    │       ▼
    │   Payload CMS
    │       │
    │       ▼
    │   MongoDB query
    │       │
    │       ▼
    │   Return JSON data
    │
    ├─ Render HTML with data
    ├─ Inject animation scripts
    └─ Send static HTML to browser
        │
        ▼
    Browser renders page
        │
        ├─ Execute animations.js
        ├─ Hydrate React islands (if any)
        └─ Display content
```

### 2. Blog Post Request (Dynamic Route)

```
User Browser
    │
    ▼
GET http://localhost:4321/blog/linkedin-marketing-tips
    │
    ▼
Astro Frontend
    │
    ├─ Parse slug from URL
    ├─ Fetch post from CMS API
    │   │
    │   ▼
    │   GET http://cms:3000/api/posts?where[slug][equals]=linkedin-marketing-tips&depth=2
    │       │
    │       ▼
    │   Payload CMS
    │       │
    │       ├─ Query MongoDB for post
    │       ├─ Populate category relationships (depth=2)
    │       └─ Return post data
    │
    ├─ Render blog post template
    ├─ Fetch related posts (same category)
    └─ Send HTML to browser
```

### 3. Contact Form Submission

```
User Browser
    │
    ▼
Fill contact form → Click Submit
    │
    ▼
React ContactForm component (client-side)
    │
    ├─ Validate fields (required, email format)
    ├─ Show loading state
    └─ POST http://cms:3000/api/form-submissions
        │
        Headers: Content-Type: application/json
        Body: { name, email, company, message }
        │
        ▼
    Next.js Middleware (cms/src/middleware.ts)
        │
        ├─ Handle CORS preflight (OPTIONS)
        └─ Set CORS headers
            │
            ▼
        Payload CMS API
            │
            ├─ Validate data against FormSubmissions schema
            ├─ Save to MongoDB
            └─ Return { id, doc } response
                │
                ▼
            ContactForm receives success
                │
                ├─ Clear form
                ├─ Show success message
                └─ Hide loading state
```

### 4. CMS Admin Workflow

```
Admin User
    │
    ▼
Navigate to http://localhost:3000/admin
    │
    ▼
Payload Admin Panel (Next.js SSR)
    │
    ├─ Load admin UI (@payloadcms/ui)
    ├─ Authenticate user (JWT session)
    └─ Display dashboard
        │
        ▼
    Create/Edit Blog Post
        │
        ├─ Fill in title, author, date, excerpt
        ├─ Select categories (relationship field)
        ├─ Upload featured image (Media collection)
        ├─ Write content (Lexical rich text editor)
        └─ Click Save
            │
            ▼
        POST /api/posts
            │
            ├─ Validate schema
            ├─ Auto-generate slug from title
            ├─ Save to MongoDB
            └─ Return saved post
                │
                ▼
            Frontend fetches updated data on next build/request
```

## Key Design Decisions

### 1. Why Astro over Next.js/Gatsby?

**Decision**: Use Astro as the frontend framework instead of Next.js or Gatsby.

**Rationale**:
- **Zero JavaScript by default**: Astro sends no client-side JavaScript unless explicitly needed (React islands), resulting in faster initial page loads
- **Multi-framework support**: Can use React only where interactivity is needed (contact form, mobile nav) while keeping the rest as static HTML
- **Simpler mental model**: File-based routing without complex data fetching patterns (getStaticProps, etc.)
- **Build performance**: Faster builds than Gatsby for static content
- **Perfect for marketing sites**: The use case (mostly static pages with occasional interactivity) aligns perfectly with Astro's architecture

**Trade-offs**: Less ecosystem maturity than Next.js, but this is acceptable for a marketing site with straightforward requirements.

### 2. Why Payload CMS over Strapi/Contentful?

**Decision**: Use Payload CMS 3.x as the headless CMS instead of Strapi, Contentful, or other alternatives.

**Rationale**:
- **Code-first configuration**: Collections defined in TypeScript files, not UI configuration (version-controllable, easier to replicate)
- **Built on Next.js**: Familiar technology stack, easier to extend or customize
- **Rich text via Lexical**: Modern, extensible rich text editor (Facebook's open-source project)
- **Self-hosted**: No vendor lock-in, complete data ownership
- **MongoDB support**: Native MongoDB adapter with Mongoose (document DB fits unstructured blog content)
- **GraphQL + REST**: Both API paradigms available out of the box

**Trade-offs**: Smaller community than Strapi, but documentation is good and the codebase is clean.

### 3. Why MongoDB over PostgreSQL?

**Decision**: Use MongoDB as the database instead of PostgreSQL or MySQL.

**Rationale**:
- **Schema flexibility**: Blog posts, testimonials, and form submissions have varying structures (rich text, nested categories, etc.)
- **Payload CMS support**: Payload has first-class MongoDB support via `@payloadcms/db-mongodb`
- **Simpler deployment**: Official MongoDB Docker image requires zero configuration
- **Document model fit**: CMS content naturally fits the document paradigm (posts are self-contained documents with embedded metadata)

**Trade-offs**: No ACID guarantees for complex transactions, but this is not needed for a content-driven marketing site.

### 4. Why Custom CSS over Tailwind?

**Decision**: Use custom CSS with design tokens instead of Tailwind CSS.

**Rationale**:
- **Full control over design**: The Nexus-inspired dark theme requires specific gradients, glass-morphism effects, and animations that don't map well to utility classes
- **Smaller bundle size**: Only the CSS actually used is shipped (no 3MB+ of utility classes)
- **Better animation control**: Complex `@keyframes` and Intersection Observer integrations are easier with custom CSS
- **Learning opportunity**: Demonstrates CSS custom properties (design tokens) and modern CSS techniques

**Trade-offs**: Slower initial development compared to Tailwind's rapid prototyping, but results in cleaner, more maintainable code for this design system.

### 5. Why Docker Compose over Kubernetes?

**Decision**: Deploy all services via Docker Compose instead of Kubernetes or serverless.

**Rationale**:
- **Simplicity**: Single `docker compose up` command starts the entire stack
- **Local development parity**: Production and development environments use the same orchestration
- **Lower resource overhead**: Suitable for small-to-medium traffic (500+ clients mentioned in content)
- **Easier debugging**: Logs, health checks, and service dependencies clearly defined in one file

**Trade-offs**: Not horizontally scalable like Kubernetes, but this can be addressed later if traffic demands it.

### 6. Why Intersection Observer over CSS-only Animations?

**Decision**: Use JavaScript Intersection Observer for scroll-triggered animations instead of CSS-only solutions.

**Rationale**:
- **Precise control**: Trigger animations exactly when elements enter viewport, not on page load
- **Performance**: Observe elements efficiently without scroll event listeners
- **Complex interactions**: Supports staggered child animations, number counters, and parallax effects
- **Progressive enhancement**: Pages still render correctly if JavaScript is disabled (just no animations)

**Trade-offs**: Requires client-side JavaScript, but the animation bundle is small (<3KB) and non-blocking.

## Infrastructure

### Docker Compose Configuration

The entire application stack is defined in `docker-compose.yml`:

```yaml
services:
  db:          # MongoDB 7
  cms:         # Payload CMS (Node.js 20)
  frontend:    # Astro frontend (Node.js 20)

volumes:
  mongodata:   # Named volume for MongoDB persistence
```

**Dependency Chain**:
1. MongoDB starts first with health check (`mongosh --eval "db.adminCommand('ping')"`)
2. CMS waits for MongoDB to be healthy before starting
3. Frontend waits for CMS to be running before starting

**Volume Mounts**:
- `./cms:/app` — CMS source code (hot reload)
- `./frontend:/app` — Frontend source code (hot reload)
- `/app/node_modules` — Anonymous volume to prevent overwriting installed packages
- `mongodata:/data/db` — Named volume for MongoDB persistence

**Restart Policy**: `unless-stopped` — Services restart automatically unless explicitly stopped

### Environment Configuration

**Development** (default):
- CMS runs on `http://localhost:3000` with `NODE_ENV=development`
- Frontend runs on `http://localhost:4321` with hot module reloading
- MongoDB data persists across restarts via named volume

**Production** (recommended setup):
- Use managed MongoDB (MongoDB Atlas)
- Build Astro frontend to static files (`npm run build`)
- Deploy static files to CDN (Netlify, Vercel, Cloudflare Pages)
- Deploy CMS to Node.js hosting (Heroku, Railway, DigitalOcean)
- Set `PAYLOAD_SECRET` to a strong random value
- Configure CORS/CSRF for production domain

### Health Checks

**MongoDB**:
```yaml
test: mongosh --eval "db.adminCommand('ping')"
interval: 10s
timeout: 5s
retries: 5
start_period: 40s
```

**CMS and Frontend**: No explicit health checks (rely on MongoDB health check via depends_on)

### Data Persistence

MongoDB data is stored in a named Docker volume (`beep2b-mongodata`). This ensures:
- Data survives `docker compose down` and `docker compose up` cycles
- Data is not lost when containers are recreated
- Data can be backed up via `docker volume` commands

**Backup example**:
```bash
docker run --rm -v beep2b-mongodata:/data -v $(pwd):/backup alpine tar czf /backup/mongo-backup.tar.gz /data
```

**Restore example**:
```bash
docker run --rm -v beep2b-mongodata:/data -v $(pwd):/backup alpine tar xzf /backup/mongo-backup.tar.gz
```

## Security Considerations

1. **Change default credentials**: The seed script creates `admin@beep2b.com / changeme` — this MUST be changed in production
2. **Set strong PAYLOAD_SECRET**: Used for JWT signing — use a cryptographically random string
3. **Configure CORS properly**: Restrict allowed origins in production (`cors` and `csrf` in `payload.config.ts`)
4. **Use HTTPS**: Always serve production sites over HTTPS (handled by CDN/hosting provider)
5. **Sanitize form inputs**: Payload CMS automatically sanitizes inputs, but be cautious with rich text rendering
6. **Rate limit API endpoints**: Consider adding rate limiting middleware for form submissions to prevent spam

## Performance Optimizations

1. **Static Site Generation**: Astro pre-renders pages at build time for instant loading
2. **Partial Hydration**: Only contact form and mobile nav send JavaScript to the client
3. **Image Optimization**: Payload CMS generates responsive image sizes (thumbnail, card, feature)
4. **Lazy Loading**: Intersection Observer-based animations also defer non-critical rendering
5. **CDN Caching**: Static assets can be served from edge locations worldwide
6. **Database Indexing**: Payload automatically indexes common query fields (slug, date, categories)

## Scalability Considerations

For future growth, consider:

1. **Horizontal scaling**: Add multiple CMS instances behind a load balancer
2. **Database replication**: Use MongoDB replica sets for high availability
3. **CDN integration**: Serve static frontend from Cloudflare, Fastly, or AWS CloudFront
4. **Caching layer**: Add Redis for API response caching
5. **Search optimization**: Integrate Algolia or Meilisearch for full-text blog search
6. **Media CDN**: Use Cloudinary or Imgix for image transformation and delivery

## Monitoring and Observability

Recommended production monitoring:

1. **Application logs**: Aggregate Docker logs to service (DataDog, Loggly, Papertrail)
2. **Uptime monitoring**: Ping services at regular intervals (UptimeRobot, Pingdom)
3. **Error tracking**: Instrument frontend/CMS with Sentry or Rollbar
4. **Performance monitoring**: Use Lighthouse CI for frontend performance regression testing
5. **Database metrics**: Monitor MongoDB query performance, connection pool, and disk usage

## Future Architecture Enhancements

Potential improvements for future iterations:

1. **Multi-language support** (i18n) — Payload CMS has localization plugins
2. **Search functionality** — Add full-text search to blog with search index
3. **Analytics integration** — Add privacy-friendly analytics (Plausible, Fathom)
4. **Email service integration** — Send form submissions to email (SendGrid, Postmark)
5. **Newsletter system** — Collect email subscribers and send newsletters
6. **A/B testing framework** — Experiment with different CTAs and layouts
7. **Progressive Web App** — Add service worker for offline functionality
8. **GraphQL frontend** — Migrate from REST to GraphQL for more efficient data fetching
