# PRD: Beep2B Website Rebuild

## 1. System Architecture

### 1.1 Technology Stack
- **Framework**: Astro 5+ with `@astrojs/react` integration for interactive islands
- **UI**: shadcn/ui components (React) with Tailwind CSS
- **CMS**: Sanity v4+ with TypeScript schema definitions
- **Language**: TypeScript throughout (Astro pages, React components, Sanity schemas)
- **Build**: Static site generation (SSG) — all pages pre-rendered at build time
- **Package manager**: npm

### 1.2 Project Structure
```
sprints/beep2b/
├── astro.config.mjs          # Astro config with React + Tailwind
├── tailwind.config.mjs       # Tailwind config with shadcn theme
├── tsconfig.json
├── package.json
├── src/
│   ├── layouts/
│   │   └── BaseLayout.astro  # HTML shell, head, nav, footer
│   ├── components/
│   │   ├── ui/               # shadcn/ui components (Button, Card, etc.)
│   │   ├── Header.astro      # Site header with navigation
│   │   ├── Footer.astro      # Site footer with links, social, newsletter
│   │   ├── Hero.astro        # Hero section (reusable across pages)
│   │   ├── FeatureCard.astro # Feature/benefit card
│   │   ├── TestimonialCard.astro
│   │   ├── BlogCard.astro    # Blog post preview card
│   │   ├── ContactForm.tsx   # React island — interactive form
│   │   ├── MobileNav.tsx     # React island — mobile menu toggle
│   │   └── CategoryFilter.tsx # React island — blog category filter
│   ├── pages/
│   │   ├── index.astro       # Home page
│   │   ├── how-it-works.astro
│   │   ├── services.astro
│   │   ├── about.astro
│   │   ├── contact.astro
│   │   └── blog/
│   │       ├── index.astro       # Blog listing (paginated)
│   │       ├── [...slug].astro   # Individual blog post
│   │       └── category/
│   │           └── [category].astro  # Posts filtered by category
│   ├── lib/
│   │   ├── sanity.ts         # Sanity client + query helpers
│   │   └── utils.ts          # Shared utilities (date formatting, etc.)
│   └── styles/
│       └── globals.css       # Tailwind directives + custom styles
├── sanity/
│   ├── sanity.config.ts      # Sanity Studio configuration
│   ├── sanity.cli.ts         # Sanity CLI config
│   ├── schemas/
│   │   ├── index.ts          # Schema registry
│   │   ├── post.ts           # Blog post schema
│   │   ├── author.ts         # Author schema
│   │   ├── category.ts       # Blog category schema
│   │   ├── page.ts           # Generic page content schema
│   │   ├── siteSettings.ts   # Global site settings
│   │   ├── testimonial.ts    # Testimonial schema
│   │   └── navigation.ts     # Navigation menu schema
│   └── package.json          # Sanity Studio dependencies
└── public/
    ├── favicon.ico
    └── images/               # Static images (logo, icons)
```

### 1.3 Sanity Configuration

**Important**: The Sanity project must be created before the CMS integration tasks can run. The loop should request an Interactive Pause to have the human:
1. Create a Sanity project at sanity.io/manage
2. Provide the project ID
3. Create a dataset named "production"
4. Generate an API token with read permissions

**Timing**: The Interactive Pause for Sanity project creation must be requested at the start of Epic 2 planning, before any Sanity-dependent tasks are executed. Epic 1 must complete fully before the pause is triggered.

The project ID and dataset name are configured in `src/lib/sanity.ts` and `sanity/sanity.config.ts`.

For development/testing before Sanity is set up, all CMS-dependent pages should gracefully handle missing data (show placeholder content or empty states rather than crashing).

### 1.4 Build Constraints

All shadcn/ui components are React components and must be placed in `.tsx` files rendered via React island directives:
- **`client:load`** — for navigation and form components that must be interactive immediately (e.g., `MobileNav.tsx`, `ContactForm.tsx`)
- **`client:visible`** — for below-the-fold interactive components that can hydrate lazily (e.g., `CategoryFilter.tsx`)

Non-interactive styling must use Tailwind utility classes directly in `.astro` files. Do not wrap static/presentational content in React components solely for styling. The goal is to minimize shipped JavaScript by reserving React islands only for genuinely interactive UI.

## 2. Sanity CMS Schemas

### 2.1 Blog Post (`post`)
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | Yes | Post title |
| slug | slug | Yes | URL slug, sourced from title |
| author | reference → author | Yes | |
| publishedAt | datetime | Yes | Publication date |
| categories | array of reference → category | Yes | One or more categories |
| featuredImage | image | No | With alt text field |
| excerpt | text | No | Short summary for cards (max 200 chars) |
| body | block content (Portable Text) | Yes | Rich text with images, links, headings |

### 2.2 Author (`author`)
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| name | string | Yes | |
| slug | slug | Yes | |
| image | image | No | Author headshot |
| bio | text | No | Short bio |

### 2.3 Category (`category`)
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | Yes | Display name |
| slug | slug | Yes | URL-safe identifier |
| description | text | No | Category description |

**Seed categories** (matching existing blog): Authority Marketing, B2B, LinkedIn Marketing, LinkedIn Profile, LinkedIn Tips, LinkedIn Training, Relationship Selling, Social Selling, Thought Leadership.

### 2.4 Page Content (`page`)
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | Yes | Page identifier |
| slug | slug | Yes | Must match route (e.g., "home", "about") |
| sections | array of content blocks | Yes | See section types below |

**Section types** (as Sanity objects within the sections array):
- `hero`: heading (string), subheading (text), ctaText (string), ctaLink (string), backgroundImage (image)
- `features`: heading (string), items[] — each with icon (string), title (string), description (text)
- `testimonials`: heading (string), items[] — each a reference → testimonial
- `textBlock`: heading (string), body (block content)
- `cta`: heading (string), description (text), buttonText (string), buttonLink (string)

### 2.5 Testimonial (`testimonial`)
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| name | string | Yes | Person's name |
| company | string | No | Company name |
| role | string | No | Job title |
| quote | text | Yes | Testimonial text |
| image | image | No | Headshot |

### 2.6 Site Settings (`siteSettings`)
| Field | Type | Notes |
|-------|------|-------|
| title | string | Site title for meta tags |
| description | text | Default meta description |
| logo | image | Site logo |
| socialLinks | object | linkedin, twitter, facebook URLs |
| footerText | text | Footer copyright/tagline |
| ctaDefaultLink | string | Default CTA destination (booking page URL) |

### 2.7 Navigation (`navigation`)
| Field | Type | Notes |
|-------|------|-------|
| items | array of objects | Each: label (string), href (string), children[] (optional nested items) |

## 3. Page Specifications

### 3.1 Home Page (`/`)

**Sections:**
1. **Hero**: Large headline ("Consistent B2B Leads From LinkedIn" or similar from CMS), subheadline, primary CTA button ("Book a Discovery Call"), optional background image
2. **What We Do**: 3-4 feature cards (icon + title + short description) highlighting core services
3. **How It Works Preview**: Brief 4-step visual of the BEEP method with link to full page
4. **Social Proof**: 2-3 testimonial cards from CMS
5. **CTA Banner**: Bottom CTA section ("Ready to grow?" + button)

### 3.2 How It Works (`/how-it-works`)

The BEEP Method presented as a visual 4-step process:
1. **Build** — Grow your LinkedIn network with targeted connections
2. **Engage** — Foster meaningful conversations based on goals and interests
3. **Educate** — Deliver valuable content addressing prospect pain points
4. **Promote** — Share offerings to a warmed, trusting audience

Each step: number/icon, heading, 2-3 sentence description. Alternating layout (text left/right) for visual interest. CTA at bottom.

### 3.3 Services (`/services`)

Three service sections on one page:
1. **LinkedIn Marketing**: Core lead generation service description
2. **Thought Leadership Marketing**: Content-driven authority building
3. **LinkedIn Training**: Training programs for teams

Each section: heading, description paragraph, key benefits list, CTA link. Content from CMS `page` schema.

### 3.4 About (`/about`)

- Company story: founded 2014, grown to serve members in 22 countries
- Mission statement: "Built by marketers for marketers"
- Philosophy: systematic social selling over hard-sell approaches
- Optional team section (from CMS)
- CTA to contact/discovery call

### 3.5 Contact (`/contact`)

Contact form (React island) with fields:
- Name (required)
- Email (required, validated)
- Company (optional)
- Message (required, textarea)
- Submit button

Form submits to a configurable action URL (environment variable `PUBLIC_FORM_ACTION`). On submit: show success message. On error: show error message. Client-side validation before submit.

### 3.6 Blog Listing (`/blog`)

- Card grid: 10 posts per page, each card shows featured image, title, date, categories, excerpt
- Category filter bar at top (links to `/blog/category/[slug]`)
- Pagination: prev/next + page numbers
- Posts fetched from Sanity at build time via GROQ queries

### 3.7 Blog Post (`/blog/[slug]`)

- Full-width featured image (if present)
- Title, author, date, categories
- Body rendered from Sanity Portable Text (headings, paragraphs, images, links, lists, quotes)
- Author bio card at bottom
- "Related Posts" section: 3 posts from same category
- Back to blog link

### 3.8 Blog Category (`/blog/category/[slug]`)

Same layout as blog listing, filtered to one category. Category title displayed as page heading.

## 4. Design Specifications

### 4.1 Color Scheme
- **Primary**: Blue (#1e40af / blue-800) — professional B2B feel
- **Primary light**: (#3b82f6 / blue-500) — hover states, accents
- **Background**: White (#ffffff) with light gray sections (#f8fafc / slate-50)
- **Text**: Dark gray (#1e293b / slate-800) for body, near-black (#0f172a / slate-900) for headings
- **Accent**: Subtle gradient or tint for CTAs and highlights

### 4.2 Typography
- **Headings**: Inter (or system font stack) — bold, clean
- **Body**: Inter (or system font stack) — regular weight, good readability
- **Blog body**: Slightly larger line-height for long-form reading

### 4.3 Component Styling
All interactive components use shadcn/ui defaults with the blue primary color configured in Tailwind. Components needed:
- `Button` (primary, secondary, outline variants)
- `Card` (blog cards, feature cards, testimonial cards)
- `Input`, `Textarea`, `Label` (contact form)
- `NavigationMenu` (desktop nav)
- `Sheet` (mobile nav drawer)
- `Badge` (category tags)
- `Separator`
- `Pagination` (blog pagination)

### 4.4 Responsive Breakpoints
- Mobile: < 768px (single column, hamburger nav, stacked cards)
- Tablet: 768px – 1024px (2-column grids)
- Desktop: > 1024px (full layout, horizontal nav, 3-column card grids)

## 5. SEO and Meta

Every page must include:
- `<title>` tag (page-specific)
- `<meta name="description">` (page-specific or from CMS)
- Open Graph tags: og:title, og:description, og:image, og:url
- Canonical URL
- Structured data (Organization schema on home page)
- `robots.txt` and `sitemap.xml` (Astro generates sitemap with `@astrojs/sitemap`)

## 6. Acceptance Criteria

### Epic 1: Astro + shadcn Foundation
- [ ] Astro project initializes and builds successfully
- [ ] shadcn/ui components installed and rendering (Button, Card, Input)
- [ ] Tailwind configured with custom blue color scheme
- [ ] BaseLayout with Header (desktop nav + mobile nav) and Footer
- [ ] All page routes created and rendering with placeholder content
- [ ] Responsive layout working at mobile, tablet, and desktop breakpoints
- [ ] `npm run build` produces static output with no errors

### Epic 2: Sanity CMS Integration
- [ ] Sanity Studio project created with all schemas (post, author, category, page, testimonial, siteSettings, navigation)
- [ ] Sanity client configured in Astro (`src/lib/sanity.ts`)
- [ ] GROQ queries fetch blog posts, page content, and site settings at build time
- [ ] Blog listing page renders posts from Sanity with pagination
- [ ] Individual blog post pages generated from Sanity data
- [ ] Category filter pages generated for each category
- [ ] Portable Text body content renders correctly (headings, images, links, lists)
- [ ] Pages gracefully handle missing/empty CMS data (no build crashes)

### Epic 3: Complete Pages and Polish
- [ ] Home page: hero, features, BEEP preview, testimonials, CTA — all from CMS
- [ ] How It Works page: 4-step BEEP method visual layout
- [ ] Services page: 3 service sections with descriptions and CTAs
- [ ] About page: company story, mission, CTA
- [ ] Contact page: working form with validation and success/error states
- [ ] Blog post page: author card, related posts section
- [ ] SEO: meta tags, OG tags, sitemap, robots.txt on all pages
- [ ] Final visual polish: consistent spacing, typography, color across all pages
