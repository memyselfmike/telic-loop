# Vision: Beep2B Website Rebuild

## The Outcome

A business owner visits beep2b.com and finds a modern, fast, professional marketing website that clearly communicates what Beep2B does (B2B LinkedIn lead generation consulting), how their BEEP method works, and gives them a path to book a discovery call. The site owner can update all page content and publish blog posts through a Sanity CMS dashboard without touching code.

## Who Is This For

Two audiences:

1. **Site visitors**: B2B entrepreneurs, solopreneurs, and marketers looking for LinkedIn lead generation help. They need to quickly understand the value proposition, see how the method works, read educational blog content, and book a strategy call.

2. **Site owner**: The Beep2B team who needs to publish blog posts, update page content (hero text, testimonials, service descriptions), and manage the site without developer involvement.

## What "Value Delivered" Looks Like

### 1. Modern Marketing Website

A complete rebuild of beep2b.com with a fresh, modern design using Astro for static site generation and shadcn/ui components for a polished, consistent UI. The site loads fast (static HTML), looks professional, and works on desktop and mobile.

Pages:
- **Home**: Hero with value proposition, features/benefits section, social proof (testimonials), CTA to book a discovery call
- **How It Works**: The BEEP Method explained (Build, Engage, Educate, Promote) with visual step-by-step layout
- **Services**: What Beep2B offers — LinkedIn Marketing, Thought Leadership Marketing, LinkedIn Training (can be one page with sections or separate pages, whichever reads better)
- **About**: Company story (est. 2014, 22 countries), mission, approach
- **Blog**: List view with category filtering, individual post pages with rich content
- **Contact**: Contact form with name, email, company, message fields

### 2. Content Management with Sanity CMS

All content is managed through Sanity Studio:
- **Blog posts**: Title, slug, author, publish date, categories (from the existing 9 categories: Authority Marketing, B2B, LinkedIn Marketing, LinkedIn Profile, LinkedIn Tips, LinkedIn Training, Relationship Selling, Social Selling, Thought Leadership), featured image, rich text body with embedded images
- **Page content**: Editable sections for each page — hero text, feature blocks, testimonials, CTAs. The site owner can change headlines, descriptions, and images without code changes
- **Navigation**: Menu items manageable from CMS
- **Site settings**: Company info, social links, footer content

### 3. Blog with Discovery

The blog is a core content marketing tool. Visitors can:
- Browse all posts in a card grid layout
- Filter by category
- Read individual posts with proper typography, images, and formatting
- See related posts or recent posts sidebar/section
- Navigate with pagination (the current site has ~120 posts across 12 pages)

### 4. Responsive and Fast

- Astro generates static HTML — near-instant page loads
- Mobile-first responsive design using shadcn/ui components
- Proper SEO: meta tags, Open Graph, structured data, sitemap
- Accessible: semantic HTML, proper heading hierarchy, alt text

## What This Is NOT

- Not a web application (no user accounts, no dashboards, no login)
- Not an e-commerce site (no payments, no products)
- Not a migration tool (existing blog content will be manually entered into Sanity later — the CMS structure must support it, but we don't migrate data)
- Not the LinMetrics tool (that's a separate product, just link to it)
- Not a booking system (discovery calls link to an external booking page like Calendly)

## Architecture

- **Frontend**: Astro static site with React islands for interactive components
- **UI Components**: shadcn/ui (React) for buttons, cards, forms, navigation
- **Styling**: Tailwind CSS (comes with shadcn)
- **CMS**: Sanity.io headless CMS with Sanity Studio
- **Deployment target**: Static build output (can deploy anywhere — Vercel, Netlify, etc.)
- **Content delivery**: Sanity CDN for images and content API for build-time data fetching

## Constraints

- Node.js 18+ for build tooling
- Astro 4+ with React integration
- shadcn/ui components (not raw Radix, not Material UI, not Chakra)
- Sanity v3 (latest) with TypeScript schemas
- All pages must work without JavaScript (progressive enhancement — Astro's default)
- Blog pagination: 10 posts per page
- Mobile breakpoint: 768px
- Professional, clean design with a blue/dark color scheme consistent with B2B SaaS aesthetics
- Contact form submits to a configurable endpoint (can be Formspree, Netlify Forms, or similar — just needs the form markup and handler)
- No server-side runtime required — pure static site with build-time CMS data fetching
