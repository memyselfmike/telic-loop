# Implementation Plan (rendered from state)

Generated: 2026-03-05T09:50:42.198787


## Infrastructure

- [x] **1.1**: Create docker-compose.yml with 3 services: frontend (node:20-alpine, port 4321, volume-mount frontend/), cms (node:22-alpine, port 3000, volume-mount cms/, command: sh -c "npm install && npx next dev"), db (mongo:7, port 27017). MongoDB named volume mongodata. CMS depends on db (mongosh healthcheck). Frontend depends on CMS. CMS env: DATABASE_URL=mongodb://db:27017/beep2b, PAYLOAD_SECRET, PAYLOAD_CONFIG_PATH=src/payload.config.ts. Frontend env: CMS_URL=http://cms:3000. Add .dockerignore for node_modules.
  - Value: User can docker compose up and have the entire stack running with zero manual config
  - Acceptance: docker compose config validates. docker compose up builds and starts all 3 services. MongoDB data persists via named volume across restarts.

- [x] **1.2**: Scaffold Payload CMS 3.x in cms/. package.json: payload, @payloadcms/db-mongodb, @payloadcms/richtext-lexical, @payloadcms/next, @payloadcms/ui, next@15, react, react-dom, sharp, cross-env, graphql. dev script: next dev. next.config.mjs with withPayload. tsconfig.json with @payload-config alias. src/payload.config.ts with buildConfig, mongooseAdapter, lexicalEditor. App dir: (payload)/layout.tsx, admin/[[...segments]]/page.tsx, api/[...slug]/route.ts. Users collection for auth.
  - Value: CMS service boots with Next.js, serves admin panel at /admin and REST API at /api
  - Acceptance: cms container starts via docker compose. http://localhost:3000/admin loads Payload admin panel. /api endpoint responds to requests. No startup errors in logs.
  - Deps: 1.1

- [x] **1.4**: Scaffold Astro 5.x frontend in frontend/. package.json with astro@5, @astrojs/react, react, react-dom. Create astro.config.mjs enabling React integration, dev server on 0.0.0.0:4321. Create Dockerfile (node:20-alpine, workdir, copy, npm install). Create src/pages/index.astro with placeholder. Create src/layouts/BaseLayout.astro with HTML shell, dark theme meta, viewport meta, charset.
  - Value: Frontend service boots and serves pages so all subsequent UI tasks have a working foundation
  - Acceptance: frontend container starts via docker compose. http://localhost:4321 returns HTML page. Astro dev server hot-reloads on file changes. Dark background visible.
  - Deps: 1.1


## Cms

- [x] **2.1**: Create Payload CMS collections. Posts: title, slug (auto from title), author, date, categories (relationship), featuredImage (upload), excerpt (textarea), content (richText/lexical). Categories: title, slug. Testimonials: name, company, role, quote (textarea), rating (1-5 number). Media collection for uploads. Register all collections in payload.config.ts.
  - Value: CMS has the complete data model to manage all site content: posts, categories, testimonials, media
  - Acceptance: Payload admin shows Posts, Categories, Testimonials, Media collections. Can create entries in each. REST API returns data at /api/posts, /api/categories, /api/testimonials.
  - Deps: 1.2

- [x] **2.2**: Create seed script at cms/src/seed.ts that runs via Payload onInit hook (skip if data exists). Seeds: 9 blog categories from PRD, 3 testimonials (Sarah M./James K./Anja W. with full copy from PRD including star ratings), 3 sample blog posts with realistic B2B/LinkedIn content, excerpts, and category assignments. Also create a default admin user (admin@beep2b.com / changeme) so CMS is immediately accessible.
  - Value: Site launches with realistic content so every page has data to display from day one, and CMS is immediately accessible
  - Acceptance: After fresh docker compose up, /api/categories returns 9 items, /api/posts returns 3 posts with categories, /api/testimonials returns 3 entries. Admin login works. Data persists across restarts.
  - Deps: 2.1


## Design_System

- [x] **3.1**: Create CSS design token system at frontend/src/styles/tokens.css. Define custom properties: backgrounds (#0a0a0f, #12121a, #1a1a2e), text (#fff, #b0b0c0, #6b6b80), accents (#4f7df7, #f7a04f), gradients, spacing scale (4/8/16/24/32/48/64/96px), shadows with blue tint (sm/md/lg/xl), border-radius (4/8/12/24/999px), transitions (200/300ms ease), font sizes (0.75-5rem). Create global.css importing tokens with base resets, dark body, typography, link styles, container max-width 1200px.
  - Value: Establishes visual consistency so every component shares the same premium dark palette, spacing, and typography
  - Acceptance: All CSS custom properties load. Body has #0a0a0f background. Typography renders with correct sizes and colors. No hardcoded color values needed outside tokens.
  - Deps: 1.4

- [x] **3.2**: Create scroll animation system: frontend/src/scripts/animations.js using Intersection Observer. Support data-animate attrs (fade-in, slide-up, slide-left, slide-right, scale-in). Staggered entrance via data-stagger with 100ms delay between children. Parallax scroll via data-parallax. Number counter animation via data-counter (0 to target). Create corresponding CSS @keyframes in frontend/src/styles/animations.css with initial hidden states and animated visible states.
  - Value: Every section gets smooth scroll-triggered entrance animations matching the Nexus premium feel
  - Acceptance: Elements with data-animate appear with animation when scrolled into view. Staggered grids animate children sequentially. Parallax backgrounds shift on scroll. Number counters animate to target.
  - Deps: 3.1

- [x] **3.3**: Create shared UI components: Section.astro (full-width dark wrapper, max-width 1200px content, optional parallax bg, section label, generous padding), Card.astro (glass-morphism: rgba bg, subtle border, backdrop-filter blur, hover translateY -4px + shadow transition), Button.astro (primary: gradient bg + glow shadow; secondary: transparent + border + hover fill), Badge.astro (small rounded pill with accent bg for categories/step numbers), SectionDivider.astro (gradient line divider between sections).
  - Value: Reusable component library ensures visual consistency and accelerates page development across all 7 pages
  - Acceptance: Each component renders with Nexus-style dark glass-morphism aesthetic. Cards lift on hover with shadow. Buttons show glow/fill effects. Badges display with accent colors. All use design tokens.
  - Deps: 3.1

- [x] **3.4**: Create Header.astro: sticky nav with glass-morphism (backdrop blur, semi-transparent bg), logo text "Beep2B", 7 nav links (Home, How It Works, Services, About, Blog, Contact, Book a Call CTA button), active link accent indicator, mobile hamburger icon trigger. Create Footer.astro: 4-column layout (company info + tagline, quick links, services, newsletter email input + social links), copyright, dark bg. Update BaseLayout.astro to include Header, Footer, global.css, animations.css, animations.js.
  - Value: Every page gets consistent premium navigation and footer without duplicating code
  - Acceptance: Header renders on all pages with working nav links to all 7 routes. Glass-morphism effect visible. Footer shows 4-column desktop layout, stacks on mobile. Active page highlighted.
  - Deps: 3.1, 3.2

- [x] **3.5**: Create Pixabay image helper at frontend/src/lib/pixabay.ts. Server-side fetch from Pixabay API (key: 54899839-52cb07e8d7437ca93ecb74181). Accepts query, returns image URL. Caches downloaded images to frontend/public/images/ with descriptive filenames. Create fetch-images script that pre-downloads backgrounds for: business office dark, technology abstract, networking professional, digital marketing. Run at build/dev time. Fallback to solid gradient if API fails.
  - Value: Hero and section backgrounds use high-quality Pixabay photos, cached locally for fast loads and offline resilience
  - Acceptance: Pixabay API returns images. Images download to public/images/. Cached images serve without re-fetching. At least 4 background images available. Graceful fallback on API failure.
  - Deps: 1.4


## Pages

- [x] **4.1**: Build complete Home page (index.astro). Hero: bold headline, subtitle, dual CTAs, Pixabay bg with dark overlay, animated entrance. Trust bar: 4 animated counters. Features grid: 6 numbered glass-morphism cards with staggered entrance. BEEP preview: 4-step visual with letter badges and CTA to /how-it-works. Testimonials: 3 cards with quotes, names, roles, star ratings. CTA banner: gradient bg. Create FeatureCard.astro and TestimonialCard.astro.
  - Value: Landing page makes powerful first impression with premium hero, social proof counters, and clear value proposition
  - Acceptance: Hero renders with Pixabay bg, dark overlay, headline, 2 CTAs. Trust bar counters animate on scroll. 6 feature cards in 3-col grid with numbered badges. BEEP shows 4 steps with colored letter badges. 3 testimonials with star ratings. CTA banner with gradient. All copy from PRD.
  - Deps: 3.2, 3.4, 3.5

- [ ] **4.2**: Build About page (about.astro). Hero: Our Story with company narrative. Mission statement. 4 values cards (glass-morphism): Relationships Over Reach, Systems Over Hustle, Transparency Always, Built by Marketers for Marketers. Timeline: 5 milestones from 2014 to today. Stats section with animated counters matching trust bar. All copy from PRD.
  - Value: Prospects learn the company story, mission, and values that differentiate Beep2B
  - Acceptance: About page renders with hero, mission, 4 values cards, timeline, animated stats. All copy matches PRD About section.
  - Deps: 3.2, 3.4

- [x] **4.3**: Build How It Works page (how-it-works.astro). Hero banner with page title. Interactive 4-step BEEP methodology with alternating left/right layout. Each step: large step number (01-04), letter badge (B/E/E/P) with unique accent color, heading, detailed description paragraph, highlight badge. Scroll-triggered entrance animation per step. Below: "Why BEEP Works" section with 3 differentiator glass-morphism cards. All copy from PRD.
  - Value: Prospects understand exactly how the BEEP methodology works through an engaging interactive walkthrough
  - Acceptance: 4 BEEP steps render in alternating layout with colored letter badges. Each step animates on scroll. Why BEEP Works shows 3 differentiator cards. All copy matches PRD content.
  - Deps: 3.2, 3.4

- [x] **4.4**: Build Services page (services.astro). 3 numbered service blocks in Nexus style: 01 LinkedIn Marketing (managed outreach, profile optimization, connection building, conversation sequences, monthly reporting, account manager), 02 Thought Leadership Marketing (content strategy, ghostwritten articles, engagement campaigns, newsletter setup), 03 LinkedIn Training (workshops, BEEP playbook, profile audits, coaching). Each: numbered heading, description paragraph, 5-6 bullet benefits, CTA button. Scroll-triggered animations.
  - Value: Prospects see detailed service offerings with clear benefits, driving them toward a discovery call
  - Acceptance: 3 numbered service blocks render with headings, descriptions, bullet benefit lists, and CTA buttons. Each block animates on scroll. All copy matches PRD services section.
  - Deps: 3.2, 3.4

- [ ] **4.5**: Build Contact page (contact.astro). Split layout: left = Why Book a Discovery Call? with 4 benefits list, right = contact form. Form: Name, Email, Company, Message fields with validation. React island ContactForm.tsx for interactivity. Submit with loading state, success message, error handling. Contact details: hello@beep2b.com, LinkedIn link. Create ContactForm.tsx React component.
  - Value: Prospects can submit inquiries and book discovery calls directly from the site
  - Acceptance: Contact page renders split layout. Form validates required fields. Shows loading/success/error states. All copy from PRD Contact section.
  - Deps: 3.4

- [ ] **4.6**: Build Blog listing page (blog.astro). Fetch posts from Payload CMS API at /api/posts. 3-col grid (responsive to 2-col/1-col). Each card: featured image or Pixabay fallback, title, date, category badges, excerpt, read more link. Category filter bar at top. Pagination (10 posts per page). Create BlogCard.astro component. Create lib/cms.ts helper for CMS API calls.
  - Value: Visitors can browse blog content, filter by category, driving SEO and thought leadership
  - Acceptance: Blog page fetches and displays posts from CMS. Category filter works. Pagination shows 10 per page. Cards show images, titles, dates, excerpts.
  - Deps: 2.2, 3.4, 3.5

- [ ] **4.7**: Build Blog Post dynamic route ([slug].astro). Fetch single post from Payload /api/posts?where[slug][equals]=. Featured image header. Title, author, date, category badges. Render rich text content from Payload lexical editor. Related posts section: 3 posts from same category. Create RichText.astro component for lexical content rendering. Use cms.ts helper.
  - Value: Visitors can read full blog articles with rich formatting, driving engagement and authority
  - Acceptance: Blog post page fetches and renders individual posts. Rich text displays headings, images, lists, blockquotes. Related posts show 3 from same category.
  - Deps: 4.6


## Unphased

- [x] **CE-4-13**: Add 4 new tasks: (4.2) About page with hero, mission, values cards, timeline, stats counters. (4.5) Contact page with split layout, React ContactForm island component, form validation, success/error states. (4.6) Blog listing page fetching posts from Payload CMS API, 3-col grid, pagination, category filter bar. (4.7) Blog post dynamic route [slug].astro fetching single post from Payload, rendering rich text, related posts section.
  - Value: The site will be missing 4 out of 7 pages. Navigation links to About, Contact, Blog, and Blog Post will 404. The blog-from-CMS and contact-form acceptance criteria cannot be met. This is roughly 50% of the promised deliverable missing.
  - Acceptance: Fix: 4 of 7 required pages are completely missing from the plan: About (/about), Contact (/contact), Blog listing (/blog), and Blog Post (/blog/[slug]). The PRD explicitly requires all 7 pages navigable from the nav bar (Acceptance Criterion #3). The blog pages are especially critical since they require CMS integration (Acceptance Criterion #5: Blog posts render from Payload CMS data). The Contact page requires a React island for form interactivity (Acceptance Criterion #6: Contact form validates inputs).

- [x] **CE-4-14**: Update Task 1.1 to use MONGODB_URI instead of DATABASE_URL, matching the ARCHITECTURE.md specification and Payload CMS 3.x conventions.
  - Value: CMS will not connect to MongoDB on docker compose up if the wrong env var is used, breaking the entire stack on first launch.
  - Acceptance: Fix: Environment variable mismatch between Architecture doc and Task 1.1. ARCHITECTURE.md specifies MONGODB_URI=mongodb://db:27017/beep2b but Task 1.1 uses DATABASE_URL=mongodb://db:27017/beep2b. Payload CMS 3.x with @payloadcms/db-mongodb uses MONGODB_URI (or the uri option in mongooseAdapter). Using the wrong env var name will cause the CMS to fail to connect to MongoDB.

- [x] **CE-4-15**: Change CMS service in Task 1.1 from node:22-alpine to node:20-alpine to match ARCHITECTURE.md.
  - Value: Potential build failures or runtime incompatibilities from Node version mismatch between ARCHITECTURE spec and plan.
  - Acceptance: Fix: Task 1.1 specifies node:22-alpine for the CMS service, but ARCHITECTURE.md specifies node:20-alpine for both frontend and CMS. Payload CMS 3.x with Next.js 15 works fine on Node 20, and using mismatched Node versions between services is unnecessary complexity. More importantly, node:22-alpine may have compatibility issues with native modules like sharp.

- [x] **CE-4-16**: Add responsive breakpoint custom properties to Task 3.1 (e.g., --breakpoint-sm: 480px, --breakpoint-md: 768px, --breakpoint-lg: 1280px). Add responsive media queries to global.css and each component. Alternatively, add a dedicated responsive pass task after all pages are built, but it is better to bake responsiveness into each component task.
  - Value: Site will look broken on tablets and phones. The 480px breakpoint (mobile) will have overflowing content, unreadable text, and broken layouts for grids, hero sections, and footer columns.
  - Acceptance: Fix: No responsive design task exists. PRD Acceptance Criterion #9 requires responsive layout at 1280px, 768px, and 480px breakpoints. The design token system (3.1) defines sizes but no media query breakpoints or responsive utilities. Individual page tasks mention no responsive considerations. Without explicit responsive work, the 3-column grids, hero sections, and multi-column footer will break at mobile viewports.

- [x] **CE-4-17**: Task 3.4 should specify: (a) creating a MobileNav.tsx React island or inline <script> for toggle state, (b) the slide-in/dropdown menu panel design, (c) body scroll lock when menu is open, (d) menu closes on link click and on escape key. Add MobileNav component to files_expected.
  - Value: On mobile viewports (480px, 768px), users will see a hamburger icon that does not work. They will have no way to navigate between pages on mobile devices.
  - Acceptance: Fix: Mobile navigation has no implementation plan. Task 3.4 mentions a mobile hamburger icon trigger but does not describe the mobile menu panel, toggle behavior, or the React island needed for interactive state. Astro components are static HTML -- a hamburger menu toggle requires JavaScript interactivity, either as a React island or inline script. Without this, the hamburger icon will render but clicking it will do nothing.

- [x] **CE-4-18**: Priority fixes: (1) Add tasks for About, Contact, Blog, Blog Post pages. (2) Fix MONGODB_URI env var name. (3) Fix node version to 20-alpine. (4) Add responsive breakpoints to design system and components. (5) Specify mobile nav toggle implementation. (6) Add CMS API client helper task. (7) Wire testimonial/blog data fetching from CMS.
  - Value: If built as planned, the site will be missing About, Contact, Blog, and Blog Post pages. Navigation will have dead links. CMS blog content will be unreachable. Contact form acceptance criterion cannot be met. Mobile experience will be broken. This is not shippable as the beep2b.com website.
  - Acceptance: Fix: PLAN VERDICT: REVISE. The plan has 1 critical gap (4 missing pages = ~50% of deliverable), 4 blocking issues (env var mismatch, node version mismatch, no responsive design, broken mobile nav), 4 degraded issues (missing SectionDivider file, no Pages collection, no CMS data fetching for testimonials, no shared CMS API client), and 2 polish items (task ID gaps, hardcoded API key). The critical gap alone is disqualifying — the PRD promises 7 pages and the plan only delivers 3.
