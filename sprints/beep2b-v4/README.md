# Beep2B — Premium B2B Lead Generation Website

A modern, dark-themed marketing website for B2B LinkedIn lead generation consulting, featuring smooth scroll-triggered animations, interactive content sections, and a fully-integrated headless CMS. Built with Astro for blazing-fast performance and Payload CMS for flexible content management.

## Features

- **Dark Premium Design** — Nexus-inspired dark theme with electric blue accents, bold typography, and glass-morphism UI components
- **Smooth Animations** — Scroll-triggered reveals, parallax backgrounds, staggered entrances, and animated stat counters using Intersection Observer
- **7-Page Marketing Site** — Home, How It Works, Services, About, Contact, Blog, and dynamic blog post pages
- **Headless CMS Integration** — Payload CMS 3.x with MongoDB for managing blog posts, categories, testimonials, and form submissions
- **Docker Compose Stack** — One-command deployment with frontend, CMS, and database services
- **Responsive Design** — Optimized for desktop (1280px+), tablet (768px), and mobile (480px) with touch-friendly navigation
- **Pixabay Integration** — Automated background image fetching and caching for hero and section backgrounds
- **Interactive Forms** — Contact form with validation, loading states, and CMS-backed form submission storage
- **SEO-Ready** — Static site generation with Astro for optimal performance and search engine indexing

## Tech Stack

### Frontend
- **Astro 5.x** — Static site generator with partial hydration
- **React 19** — Interactive islands for forms and mobile navigation
- **TypeScript** — Type-safe component development
- **Custom CSS** — Design token system with CSS custom properties (no frameworks)
- **Intersection Observer API** — Scroll-triggered animations
- **Pixabay API** — Dynamic background image sourcing

### CMS
- **Payload CMS 3.x** — Headless CMS with REST and GraphQL APIs
- **Next.js 15** — React framework powering the CMS admin panel
- **Lexical Editor** — Rich text editing for blog content
- **MongoDB Adapter** — Database integration via Mongoose

### Infrastructure
- **MongoDB 7** — Document database for CMS data
- **Docker Compose** — Multi-container orchestration
- **Node.js 20 Alpine** — Lightweight runtime containers

## Getting Started

### Prerequisites

- **Docker** and **Docker Compose** installed on your system
- **4GB+ RAM** recommended for running all three services
- **Port availability**: 4321 (frontend), 3000 (CMS), 27017 (MongoDB)

### Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd sprints/beep2b-v4
   ```

2. **Start the entire stack**:
   ```bash
   docker compose up
   ```

   This will:
   - Pull MongoDB 7 image
   - Install npm dependencies for both frontend and CMS
   - Start all three services with health checks
   - Seed the database with sample content on first run

3. **Access the services**:
   - **Website**: http://localhost:4321
   - **CMS Admin**: http://localhost:3000/admin
   - **CMS API**: http://localhost:3000/api

4. **CMS Login Credentials** (default seed data):
   - Email: `admin@beep2b.com`
   - Password: `changeme`

### Environment Setup

The default configuration works out-of-the-box for local development. For production or custom setups, you can modify these environment variables in `docker-compose.yml`:

**CMS Service:**
- `MONGODB_URI` — MongoDB connection string (default: `mongodb://db:27017/beep2b`)
- `PAYLOAD_SECRET` — Secret key for JWT tokens (change in production!)
- `NODE_ENV` — Environment mode (default: `development`)

**Frontend Service:**
- `CMS_URL` — CMS API endpoint (default: `http://cms:3000`)
- `NODE_ENV` — Environment mode (default: `development`)

## Usage

### Running the Development Server

```bash
# Start all services in foreground
docker compose up

# Start all services in background (detached mode)
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes database data)
docker compose down -v
```

### Managing Content

1. Navigate to http://localhost:3000/admin
2. Log in with the default credentials
3. Manage content in the following collections:
   - **Posts** — Blog articles with rich text content, categories, and featured images
   - **Categories** — Blog category taxonomy
   - **Testimonials** — Client testimonials with ratings
   - **Form Submissions** — Contact form submissions from the website
   - **Media** — Uploaded images and files

### Fetching Background Images

The project includes a Pixabay API integration for background images:

```bash
# From the frontend directory
cd frontend
npm run fetch-images
```

This downloads high-quality images for:
- Business/office environments
- Technology abstracts
- Professional networking scenes
- Digital marketing visuals

Images are cached in `frontend/public/images/` for offline use.

### Building for Production

```bash
# Build the frontend static site
cd frontend
npm run build

# Build the CMS
cd cms
npm run build
npm run start
```

For production deployment, consider:
- Using a managed MongoDB service (MongoDB Atlas)
- Serving the Astro build via CDN (Netlify, Vercel, Cloudflare Pages)
- Deploying the CMS to a Node.js hosting platform
- Setting strong `PAYLOAD_SECRET` value
- Configuring CORS and CSRF for your production domain

## Project Structure

```
sprints/beep2b-v4/
├── frontend/                 # Astro frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components (.astro, .tsx)
│   │   │   ├── Badge.astro
│   │   │   ├── BlogCard.astro
│   │   │   ├── Button.astro
│   │   │   ├── Card.astro
│   │   │   ├── ContactForm.tsx
│   │   │   ├── FeatureCard.astro
│   │   │   ├── Footer.astro
│   │   │   ├── Header.astro
│   │   │   ├── RichText.astro
│   │   │   ├── Section.astro
│   │   │   ├── SectionDivider.astro
│   │   │   └── TestimonialCard.astro
│   │   ├── layouts/         # Page layouts
│   │   │   └── BaseLayout.astro
│   │   ├── lib/             # Utility functions
│   │   │   ├── cms.ts       # CMS API client
│   │   │   └── pixabay.ts   # Pixabay image fetcher
│   │   ├── pages/           # File-based routing
│   │   │   ├── index.astro          # Home page
│   │   │   ├── how-it-works.astro   # BEEP methodology
│   │   │   ├── services.astro       # Service offerings
│   │   │   ├── about.astro          # Company info
│   │   │   ├── contact.astro        # Contact form
│   │   │   ├── blog.astro           # Blog listing
│   │   │   └── blog/[slug].astro    # Dynamic blog posts
│   │   ├── scripts/         # Client-side JavaScript
│   │   │   └── animations.js        # Scroll animation system
│   │   └── styles/          # Global styles and tokens
│   │       ├── tokens.css           # Design system variables
│   │       ├── global.css           # Base styles
│   │       ├── animations.css       # Animation keyframes
│   │       └── contact-form.css     # Form-specific styles
│   ├── public/              # Static assets
│   │   └── images/          # Cached background images
│   ├── astro.config.mjs     # Astro configuration
│   ├── tsconfig.json        # TypeScript config
│   └── package.json
│
├── cms/                     # Payload CMS application
│   ├── src/
│   │   ├── app/            # Next.js app directory
│   │   │   ├── (payload)/  # Payload route group
│   │   │   │   └── layout.tsx
│   │   │   ├── admin/      # Admin panel routes
│   │   │   │   ├── layout.tsx
│   │   │   │   └── [[...segments]]/page.tsx
│   │   │   └── api/        # API routes
│   │   │       └── [...slug]/route.ts
│   │   ├── collections/    # Payload collections (data models)
│   │   │   ├── Users.ts
│   │   │   ├── Posts.ts
│   │   │   ├── Categories.ts
│   │   │   ├── Testimonials.ts
│   │   │   ├── Media.ts
│   │   │   └── FormSubmissions.ts
│   │   ├── payload.config.ts    # CMS configuration
│   │   ├── seed.ts             # Database seed script
│   │   ├── middleware.ts       # CORS handling
│   │   └── payload-types.ts    # Generated TypeScript types
│   ├── next.config.mjs     # Next.js configuration
│   ├── tsconfig.json       # TypeScript config
│   └── package.json
│
├── docker-compose.yml      # Multi-container orchestration
├── .dockerignore          # Docker build exclusions
├── ARCHITECTURE.md        # Architecture documentation
├── VISION.md             # Project vision statement
├── PRD.md               # Product requirements
└── README.md            # This file
```

## API Reference

### Payload CMS REST API

All API endpoints are available at `http://localhost:3000/api/{collection}` and return JSON responses.

#### Get All Posts
```
GET /api/posts?page=1&limit=10&depth=2
```

Query parameters:
- `page` — Page number (default: 1)
- `limit` — Results per page (default: 10)
- `depth` — Relationship depth for populated fields (default: 0)
- `where[field][operator]=value` — Filter by field (e.g., `where[categories.slug][equals]=b2b`)

#### Get Post by Slug
```
GET /api/posts?where[slug][equals]=post-slug&depth=2&limit=1
```

#### Get All Categories
```
GET /api/categories?limit=100
```

#### Submit Contact Form
```
POST /api/form-submissions
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "company": "Acme Corp",
  "message": "I'd like to learn more about your services."
}
```

#### Get Related Posts
```
GET /api/posts?where[categories][in]=category-id&where[id][not_equals]=exclude-id&limit=3&depth=2
```

### Response Format

All collection endpoints return paginated responses:

```json
{
  "docs": [...],
  "totalDocs": 25,
  "limit": 10,
  "totalPages": 3,
  "page": 1,
  "pagingCounter": 1,
  "hasPrevPage": false,
  "hasNextPage": true,
  "prevPage": null,
  "nextPage": 2
}
```

## Design System

The project uses a custom CSS design token system defined in `frontend/src/styles/tokens.css`.

### Color Palette
- **Backgrounds**: `--color-bg-primary` (#0a0a0f), `--color-bg-card` (#12121a), `--color-bg-elevated` (#1a1a2e)
- **Text**: `--color-text-primary` (#ffffff), `--color-text-secondary` (#b0b0c0), `--color-text-muted` (#6b6b80)
- **Accents**: `--color-accent-primary` (#4f7df7), `--color-accent-secondary` (#f7a04f)

### Spacing Scale
Uses a consistent spacing scale from `--space-1` (4px) to `--space-24` (96px).

### Animation System
- Scroll-triggered reveals via Intersection Observer
- Supported animations: `fade-in`, `slide-up`, `slide-left`, `slide-right`, `scale-in`
- Staggered child animations with 100ms delay
- Number counters that animate from 0 to target value
- Parallax background scroll effects

## License

MIT License

Copyright (c) 2026 Beep2B

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
