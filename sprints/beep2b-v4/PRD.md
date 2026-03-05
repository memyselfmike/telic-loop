# Beep2B v4 — Product Requirements

## Overview

Rebuild of beep2b.com: a B2B LinkedIn lead generation consulting website. Astro static frontend + Payload CMS + MongoDB, all in Docker. Dark theme inspired by the Nexus v3 agency template with scroll-triggered animations and Pixabay-sourced imagery.

## Design Reference

**Study this template carefully before planning or building**: https://uiparadox.co.uk/templates/nexus/v3/

This is the Nexus v3 digital agency template. The beep2b rebuild should closely match its visual style, layout patterns, animation approach, and overall dark premium aesthetic. Open this URL, inspect the design, and replicate the feel — adapted for beep2b's B2B lead generation content.

Key elements to replicate from Nexus v3:
- Dark background with bold white/light typography
- Numbered service sections with descriptions and CTAs
- Scroll-triggered section reveals and parallax effects
- Glass-morphism cards with subtle borders and backdrop blur
- Large hero with animated elements and dual CTAs
- Client testimonial cards with star ratings
- Multi-step process visualization
- Filterable portfolio/work grid (adapt for blog categories)
- Brand/trust bar with partner logos or stats
- Professional contact form section
- Multi-column footer with newsletter signup

## Design Language (Nexus v3 Inspired)

### Color Palette
- **Background**: Deep dark (#0a0a0f primary, #12121a cards, #1a1a2e elevated surfaces)
- **Text**: White (#ffffff headings), light gray (#b0b0c0 body), muted (#6b6b80 secondary)
- **Accent**: Electric blue (#4f7df7 primary actions), with a secondary warm accent (#f7a04f) for highlights
- **Gradients**: Subtle dark-to-darker gradients on sections, accent gradient on CTAs

### Typography
- **Headings**: Large, bold, condensed (700-900 weight). Hero headline 4-5rem desktop, 2.5rem mobile
- **Body**: Clean sans-serif, 1rem base, generous line-height (1.7)
- **Section labels**: Uppercase, letter-spaced, small (0.75rem), accent colored

### Animations & Effects
- **Scroll-triggered reveals**: Every section fades/slides in using Intersection Observer
- **Parallax backgrounds**: Hero and section dividers with subtle parallax scroll
- **Hover effects**: Cards lift (translateY + shadow), buttons glow, links underline-slide
- **Number counters**: Stats animate counting up when scrolled into view
- **Staggered entrance**: Grid items appear one-by-one with 100ms delay between each
- **Smooth transitions**: All interactive state changes use 200-300ms ease transitions

### Component Patterns
- **Section layout**: Full-width dark sections with max-width content container (1200px)
- **Cards**: Dark glass-morphism (semi-transparent bg, subtle border, backdrop blur)
- **Buttons**: Primary (gradient bg, glow shadow), Secondary (transparent, border, hover fill)
- **Badges/pills**: Small rounded labels with accent bg for categories, step numbers
- **Dividers**: Subtle gradient lines or accent-colored thin borders between sections

## Site Content (Port from beep2b v1)

### Company Info
- **Name**: Beep2B
- **Tagline**: "Consistent B2B Leads From LinkedIn"
- **Founded**: 2014
- **Clients**: 500+ across 22 countries
- **Core method**: BEEP (Build, Engage, Educate, Promote)
- **Email**: hello@beep2b.com

### Page Content

#### Home Page (`/`)
1. **Hero**: "Consistent B2B Leads From LinkedIn" — large animated headline, subtitle about the repeatable BEEP system, dual CTAs ("Book a Discovery Call" + "See How It Works"), Pixabay background with dark overlay
2. **Trust bar**: Animated counters — "500+ Clients", "22 Countries", "Est. 2014", "4 Steps"
3. **Features grid** (6 cards, Nexus numbered-service style):
   - Precision Targeting — connect with decision-makers in your exact niche
   - Relationship-First — genuine conversations, not cold spam
   - Predictable Pipeline — know exactly how many leads to expect each month
   - Thought Leadership — position yourself as the go-to expert
   - Transparent Reporting — see every metric, every conversation, every result
   - Training & Playbooks — learn the system so your team can run it independently
4. **BEEP preview**: 4-step visual with icons/numbers, brief description each, CTA to /how-it-works
5. **Testimonials**: 3 cards with client quotes, names, roles, star ratings
6. **CTA banner**: "Ready to Grow Your B2B Pipeline?" with gradient background

#### How It Works (`/how-it-works`)
Interactive 4-step BEEP methodology:
- **Build**: Grow your LinkedIn network with precision-targeted connections to your ideal customer profile
- **Engage**: Foster meaningful one-to-one conversations based on prospects' goals, interests, and pain points
- **Educate**: Deliver high-value content that establishes you as a trusted authority in your niche
- **Promote**: Share offerings to a warmed, trusting audience that already sees your value

Each step: large step number, letter badge (B/E/E/P), heading, description, highlight badge. Alternating left/right layout with scroll-triggered entrance. "Why BEEP Works" section below with 3 differentiators.

#### Services (`/services`)
Three service blocks (Nexus numbered-service style):
1. **LinkedIn Marketing** — Managed outreach: profile optimization, targeted connection building, personalized conversation sequences, monthly reporting, dedicated account manager
2. **Thought Leadership Marketing** — Content strategy, ghostwritten articles, engagement campaigns, LinkedIn newsletter setup and growth
3. **LinkedIn Training** — Half/full-day workshops, BEEP methodology playbook, profile audits, post-training coaching

Each: numbered heading, description paragraph, benefits list (5-6 items), CTA button.

#### About (`/about`)
- Hero: "Our Story" with company narrative (founded 2014, 22 countries)
- Mission: "Make systematic B2B lead generation on LinkedIn accessible to every entrepreneur and marketer"
- Values (4 cards): Relationships Over Reach, Systems Over Hustle, Transparency Always, Built by Marketers for Marketers
- Timeline: 5 milestones from founding to today
- Stats section with animated counters

#### Contact (`/contact`)
- Split layout: left = "Why Book a Discovery Call?" with 4 benefits, right = contact form
- Form fields: Name (required), Email (required), Company (optional), Message (required)
- Submit with loading state, success message, error handling
- Contact details: hello@beep2b.com, LinkedIn @beep2b
- React island for form interactivity

#### Blog (`/blog`)
- Grid of post cards from Payload CMS (3 columns desktop, 2 tablet, 1 mobile)
- Each card: featured image (or Pixabay fallback), title, date, category badges, excerpt
- Pagination (10 posts per page)
- Category filter bar at top

#### Blog Post (`/blog/[slug]`)
- Featured image header
- Title, author, date, categories
- Rich text body from Payload (headings, images, lists, blockquotes)
- Related posts section (3 posts from same category)

### Testimonials (hardcoded fallbacks + CMS)
1. "Within 3 months of implementing BEEP, I was having 4 to 5 qualified discovery calls a week." — Sarah M., Founder B2B SaaS (UK), 5 stars
2. "The methodology is so systematic. I knew exactly what to do every day, and the results were predictable." — James K., Sales Director (Australia), 5 stars
3. "We trained our whole team. Within 6 weeks, 3 reps had LinkedIn as their top lead source." — Anja W., VP Marketing (Germany), 5 stars

### Blog Categories (seed these)
Authority Marketing, B2B, LinkedIn Marketing, LinkedIn Profile, LinkedIn Tips, LinkedIn Training, Relationship Selling, Social Selling, Thought Leadership

## Acceptance Criteria

1. `docker compose up` starts all 3 services (Astro, Payload, MongoDB) with no manual steps
2. Home page loads at http://localhost:4321 with animated hero, features grid, BEEP preview, testimonials
3. All 7 pages navigable from the top navigation bar
4. Payload CMS admin accessible at http://localhost:3000/admin
5. Blog posts render from Payload CMS data (3 seed posts visible)
6. Contact form validates inputs and shows success/error states
7. Scroll-triggered animations fire on every major section
8. Pixabay images used for hero and section backgrounds
9. Responsive at 1280px, 768px, and 480px — dark theme consistent across all viewports
10. Data persists across `docker compose down && docker compose up` (MongoDB volume)
11. Visual quality matches the Nexus v3 aesthetic — dark, bold, animated, premium feel
