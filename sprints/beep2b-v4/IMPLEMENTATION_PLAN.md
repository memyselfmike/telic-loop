# Implementation Plan (rendered from state)

Generated: 2026-03-05T11:19:39.346469


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

- [x] **4.2**: Build About page (about.astro). Hero: Our Story with company narrative. Mission statement. 4 values cards (glass-morphism): Relationships Over Reach, Systems Over Hustle, Transparency Always, Built by Marketers for Marketers. Timeline: 5 milestones from 2014 to today. Stats section with animated counters matching trust bar. All copy from PRD.
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

- [x] **4.5**: Build Contact page (contact.astro). Split layout: left = Why Book a Discovery Call? with 4 benefits list, right = contact form. Form: Name, Email, Company, Message fields with validation. React island ContactForm.tsx for interactivity. Submit with loading state, success message, error handling. Contact details: hello@beep2b.com, LinkedIn link. Create ContactForm.tsx React component.
  - Value: Prospects can submit inquiries and book discovery calls directly from the site
  - Acceptance: Contact page renders split layout. Form validates required fields. Shows loading/success/error states. All copy from PRD Contact section.
  - Deps: 3.4

- [x] **4.6**: Build Blog listing page (blog.astro). Fetch posts from Payload CMS API at /api/posts. 3-col grid (responsive to 2-col/1-col). Each card: featured image or Pixabay fallback, title, date, category badges, excerpt, read more link. Category filter bar at top. Pagination (10 posts per page). Create BlogCard.astro component. Create lib/cms.ts helper for CMS API calls.
  - Value: Visitors can browse blog content, filter by category, driving SEO and thought leadership
  - Acceptance: Blog page fetches and displays posts from CMS. Category filter works. Pagination shows 10 per page. Cards show images, titles, dates, excerpts.
  - Deps: 2.2, 3.4, 3.5

- [x] **4.7**: Build Blog Post dynamic route ([slug].astro). Fetch single post from Payload /api/posts?where[slug][equals]=. Featured image header. Title, author, date, category badges. Render rich text content from Payload lexical editor. Related posts section: 3 posts from same category. Create RichText.astro component for lexical content rendering. Use cms.ts helper.
  - Value: Visitors can read full blog articles with rich formatting, driving engagement and authority
  - Acceptance: Blog post page fetches and renders individual posts. Rich text displays headings, images, lists, blockquotes. Related posts show 3 from same category.
  - Deps: 4.6


## Unphased

- [x] **CE-10-23**: Fix animations.js: (1) Also observe [data-stagger] elements independently, even if they lack data-animate. (2) For data-counter, traverse descendants of observed elements to find and animate counters on child elements. Alternatively, add data-animate to all data-stagger parent containers.
  - Value: Approximately 40% of homepage content is permanently invisible: feature cards, testimonial cards, and trust bar counters. Blog listing page shows zero blog posts despite 3 being fetched from CMS. Services page has invisible benefit lists. This makes the site look broken and empty to any visitor.
  - Acceptance: Fix: Animation system bug: data-stagger elements without data-animate are never observed by IntersectionObserver. Blog post cards on /blog, feature cards on homepage, testimonial cards on homepage, and service benefit lists on /services all have parents with data-stagger but no data-animate, so child elements stay at opacity:0 permanently. The IntersectionObserver only observes [data-animate] elements. When it observes them and finds data-stagger, it calls staggerChildren(). But elements with ONLY data-stagger are never observed at all. Additionally, data-counter elements on trust bar numbers are children of data-animate elements, not data-animate elements themselves, so counter animation never triggers (shows 0 instead of 500+, 22, 2014, 4).

- [x] **CE-10-24**: Change docker-compose.yml line 21 from 3001:3000 to 3000:3000 to match the PRD specification.
  - Value: User following PRD instructions will try localhost:3000/admin and get connection refused. They must discover port 3001 on their own. The CMS is functional but undiscoverable at the documented URL.
  - Acceptance: Fix: CMS admin panel is not accessible at the documented port. docker-compose.yml maps CMS to external port 3001 (line 21: 3001:3000) instead of port 3000 as specified in the PRD. PRD Acceptance Criterion #4 states: Payload CMS admin accessible at http://localhost:3000/admin. The admin panel returns a redirect to /admin/login when accessed at port 3001, confirming CMS works internally but the port mapping contradicts the documented specification.

- [x] **CE-10-25**: Either (1) POST form data to a Payload CMS endpoint (create a FormSubmissions collection) or (2) send to an email service, or (3) at minimum clearly indicate in the UI that this is a demo form. Option 1 is preferred since the CMS is already available.
  - Value: A prospect who fills out the contact form believes their inquiry was sent, but no data is actually transmitted or stored. This is deceptive UX and means the primary lead-capture mechanism does not function.
  - Acceptance: Fix: Contact form submission is a mock/stub. ContactForm.tsx lines 69-73 simulate the API call with a hardcoded setTimeout and always-succeed behavior. There is no actual form submission endpoint. The form validates inputs correctly but the submit action does nothing real — it just waits 1.5 seconds and shows a success message regardless.

- [x] **CE-10-26**: Ensure all glass-morphism cards have: (1) sufficient background opacity (rgba(18,18,26,0.8) minimum), (2) visible border (rgba(79,125,247,0.2)), (3) text in --color-text-primary (#fff) for headings and --color-text-secondary (#b0b0c0) for body. Check contrast ratios meet WCAG AA (4.5:1 for text).
  - Value: Even when the animation bug is fixed, many sections will have poor readability. Users cannot read service details, feature descriptions, or values cards without squinting. The site does not achieve the premium Nexus-inspired glass-morphism aesthetic promised in the PRD — it looks like a dark void with occasional visible headings.
  - Acceptance: Fix: Extensive content invisible due to low contrast. Even on sections where animations DO trigger, many content elements are nearly invisible because dark text renders on dark backgrounds with insufficient contrast. On the scrolled homepage, the feature cards section heading "Systematic B2B Lead Generation" is visible but the actual card content (titles like Precision Targeting, descriptions) is barely legible — dark gray text on dark cards with no glass-morphism glow or visual distinction. The services page service block detail areas (bullet lists inside dark card regions) are similarly invisible. The About page values cards and timeline sections are empty dark blocks.

- [x] **CE-10-27**: This is likely another manifestation of the animation observer bug — the steps container or individual steps may not be properly observed. Ensure all 4 BEEP steps have data-animate attributes that are observed by the IntersectionObserver, or fix the observer to handle all animated elements.
  - Value: A prospect clicking How It Works to understand the BEEP methodology sees only the Build step. They cannot learn about Engage, Educate, or Promote — the other 75% of the methodology. This page is supposed to convert interest into understanding, but it fails at its primary purpose.
  - Acceptance: Fix: How It Works page only shows 1 of 4 BEEP steps. The scrolled screenshot shows only the Build step (step 01) is visible. Steps 02 (Engage), 03 (Educate), and 04 (Promote) are invisible. The alternating left/right layout means steps 2-4 use slide-left/slide-right animations that apparently do not trigger. Additionally the Why BEEP Works section with 3 differentiator cards is also invisible. This is the core methodology page — showing only 25% of the content defeats its purpose.

- [x] **CE-10-28**: Check Header.astro mobile nav CSS: the mobile menu panel should default to display:none or transform:translateX(100%) and only show on .active class toggle. Verify the initial state of the mobile menu at the 768px breakpoint.
  - Value: On tablet viewports, the navigation menu permanently overlaps the right third of the page content, blocking the hero section and other content. Users cannot dismiss it without JavaScript interaction, and it creates a confusing first impression.
  - Acceptance: Fix: Mobile navigation menu renders open on initial page load at 768px tablet viewport. The scrolled tablet screenshot (home-tablet.png) shows the mobile navigation menu panel open and visible on the right side of the screen, overlapping with page content, without the user clicking the hamburger icon. The menu shows all nav links (Home, How It Works, Services, About, Blog, Contact, Book a Call) in a slide-out panel that should only appear on hamburger click.

- [x] **CE-10-29**: Fix the 2 critical and 4 blocking issues identified. Priority order: (1) Fix animation observer to handle data-stagger and data-counter elements, (2) Fix CMS port mapping to 3000:3000, (3) Fix mobile nav default state at tablet breakpoint, (4) Fix content contrast/visibility for glass-morphism cards, (5) Replace mock contact form with real submission, (6) Fix How It Works page steps 2-4 visibility.
  - Value: The site cannot be shipped as beep2b.com in its current state.
  - Acceptance: Fix: Final evaluation verdict

- [ ] **CE-12-30**: Fix all 140 occurrences across 12 files: index.astro (26), how-it-works.astro (40), services.astro (36), FeatureCard.astro (5), TestimonialCard.astro (7), about.astro (7), contact.astro (7), blog.astro (4), BlogCard.astro (3), blog/[slug].astro (2), RichText.astro (2), contact-form.css (2). Replace --font-size-X with --text-X, --font-weight-X with --font-X, --line-height-X with --leading-X, --letter-spacing-X with --tracking-X, --line-tight with --leading-tight, --line-relaxed with --leading-relaxed, --letter-wide with --tracking-wide.
  - Value: On Home, How It Works, and Services pages, ALL headings render at 18px with normal weight -- identical to body text. There is zero visual hierarchy. Service numbers that should be massive decorative text (96px) are tiny 18px. Section headings, step titles, feature card titles -- everything is the same size. The pages are functionally unreadable for distinguishing content importance. About, Blog, Contact pages use a different wrong convention (--line-tight instead of --leading-tight) which is less severe but still breaks line heights.
  - Acceptance: Fix: CSS variable name mismatch: 140 undefined CSS custom properties across 12 files. Pages use --font-size-* (should be --text-*), --font-weight-* (should be --font-*), --line-height-* (should be --leading-*), --letter-spacing-* (should be --tracking-*), --line-tight/--line-relaxed (should be --leading-*), --letter-wide (should be --tracking-wide). None of these are defined in tokens.css, so ALL font sizes, weights, line heights, and letter spacing fall back to browser defaults (~18px / weight 400).

- [ ] **CE-12-31**: Move cms/src/app/admin/ inside cms/src/app/(payload)/ so the directory becomes cms/src/app/(payload)/admin/[[...segments]]/page.tsx. Delete the standalone cms/src/app/admin/layout.tsx. The admin pages must be children of the (payload) route group to inherit the Payload RootLayout context.
  - Value: PRD Acceptance Criterion #4 states: Payload CMS admin accessible at http://localhost:3000/admin. The admin panel is entirely broken. Users cannot log in, manage blog posts, review form submissions, edit testimonials, or perform any CMS operations. The CMS REST API works (seeded data is accessible), but the visual admin interface -- a core promise of using Payload CMS -- is unusable.
  - Acceptance: Fix: CMS Admin Panel returns HTTP 500 with TypeError: Cannot destructure property 'config' of 'se(...)' as it is undefined. The admin/ directory is a sibling of (payload)/ instead of a child, so the Payload RootLayout context provider is never initialized. The admin UI is completely non-functional -- no login, no dashboard, no collection browsing, no content editing.

- [ ] **CE-12-32**: Add cors: ['http://localhost:4321'] (or cors: '*' for dev) to the buildConfig() call in cms/src/payload.config.ts. This will allow the browser to POST form data across origins.
  - Value: The primary lead-capture mechanism is broken. A prospect who fills out the contact form sees an error message instead of a success confirmation. No inquiry data reaches the CMS database. This defeats the core purpose of a B2B lead generation website -- capturing leads.
  - Acceptance: Fix: Contact form submission fails with CORS error. ContactForm.tsx POSTs to http://localhost:3000/api/form-submissions from the frontend at http://localhost:4321. The Payload CMS config has no cors setting, so the browser blocks the cross-origin request. The form shows 'Something went wrong' error message to the user. No form data is ever stored.

- [ ] **CE-12-33**: Change all size='large' to size='lg' across index.astro, how-it-works.astro, and services.astro. The About page already correctly uses size='lg'. Alternatively, add btn-large styles to Button.astro.
  - Value: CTA buttons on Home, How It Works, and Services pages render with padding: 0px and appear as plain text links instead of prominent call-to-action buttons. On a B2B lead gen site, CTAs are the primary conversion mechanism. 'Book a Discovery Call' looks like a small text link, not a button. Users may not recognize these as clickable actions.
  - Acceptance: Fix: Button size='large' prop mismatch causes zero padding on 15+ CTA buttons. Button.astro accepts size 'sm'|'md'|'lg' and generates CSS class btn-. Pages pass size='large' generating class btn-large which has NO matching CSS rule. Affected: Hero CTAs (2), CTA banner button (1), How It Works CTAs (2), Services CTAs (8), plus any other pages using size='large'.

- [ ] **CE-12-34**: Add 'export const prerender = false;' to blog.astro to enable SSR for this page, OR convert category filtering to client-side JavaScript that hides/shows cards based on their data-category attributes.
  - Value: The category filter bar renders with 10 buttons but none of them actually filter posts. Users clicking 'LinkedIn Marketing' or 'Social Selling' see the same 3 posts every time. The filter UI is deceptive -- it appears functional but does nothing.
  - Acceptance: Fix: Blog category filtering does not work. blog.astro reads Astro.url.searchParams.get('category') but runs in Astro's default SSG mode. Pages are pre-rendered at build time, so query parameters are not evaluated at request time. Clicking a category filter button navigates to /blog?category=slug but shows all 3 posts regardless.

- [ ] **CE-12-35**: In BlogCard.astro, when the image URL is a CSS gradient string (starts with 'linear-gradient'), use it as a background-image CSS property on a div instead of as an img src. Or use a placeholder image element with the gradient as background.
  - Value: All blog post cards display broken images showing raw alt text in the image area. This looks unprofessional and undermines the 'premium agency' visual promise. The blog listing page -- a key content marketing asset -- appears broken.
  - Acceptance: Fix: Blog card images are broken. BlogCard.astro uses getImageUrl() which returns a CSS gradient string (e.g., 'linear-gradient(135deg, #1a1a2e 0%, #0a0a0f 100%)') as a fallback when no cached Pixabay image exists. This gradient string is placed into an <img src='...'> tag, which browsers cannot render. All 3 blog cards show broken image alt text instead of actual images.

- [ ] **CE-12-36**: Either (1) use the Button component in Header.astro and Footer.astro instead of raw HTML with class names, or (2) move the btn/btn-primary/btn-sm/btn-lg styles to global.css so they apply everywhere, or (3) duplicate the relevant styles in Header.astro and Footer.astro scoped styles.
  - Value: The 'Book a Call' navigation CTA -- visible on every page -- looks identical to regular nav links instead of standing out as a call-to-action button. Users cannot distinguish it as a special action. The footer Subscribe button appears as an unstyled browser default, breaking the premium dark theme aesthetic.
  - Acceptance: Fix: Header 'Book a Call' CTA and Footer 'Subscribe' button are unstyled. Both use btn/btn-primary/btn-sm CSS classes directly in HTML, but these classes are defined inside Button.astro with Astro's scoped styles. The scoped class selectors do not apply outside the Button component. The nav CTA renders as plain text (no padding, no gradient, no border-radius). The Subscribe button renders as a default browser button.

- [ ] **CE-12-37**: Add background prop to Section.astro Props interface with 'primary'|'elevated'|'card' options. Apply the corresponding --color-bg-* token to the section wrapper based on the prop value.
  - Value: All sections blend together visually with the same dark background. The Nexus v3 template alternates between dark levels to create visual depth and section separation. Without this, the site feels like one continuous dark wall of content with no visual breathing room between sections.
  - Acceptance: Fix: Section background='elevated' prop is ignored by Section.astro. The component does not accept or use a background prop. Multiple pages pass background='elevated' (index.astro BEEP preview, how-it-works.astro Why BEEP Works, services.astro service blocks) expecting #1a1a2e background, but all sections render with identical #0a0a0f background. This eliminates the visual rhythm that should alternate between primary and elevated backgrounds.

- [ ] **CE-12-38**: Change line 1 of FormSubmissions.ts from  to  to match the v3 convention used by all other collections.
  - Value: If the import fails, the FormSubmissions collection will not register, and the contact form API endpoint will not exist. Combined with the CORS issue, this means form submissions are doubly blocked.
  - Acceptance: Fix: FormSubmissions collection uses wrong import. cms/src/collections/FormSubmissions.ts imports from 'payload/types' (Payload v2 convention) while all other collections correctly import from 'payload' (Payload v3). This may cause build errors or runtime issues depending on module resolution.

- [ ] **CE-12-39**: Priority fixes: (1) Fix 140 CSS variable name mismatches across 12 files. (2) Fix CMS admin panel route structure. (3) Add CORS config to Payload CMS for form submissions. (4) Change Button size=large to size=lg. (5) Fix blog card image fallback. (6) Fix blog SSG category filtering. (7) Style nav CTA and footer Subscribe button. (8) Add background prop to Section.astro. (9) Fix FormSubmissions import.
  - Value: The site has strong architectural foundations (Docker stack works, CMS API serves data, animation system functions, responsive layouts reflow correctly, 7 pages exist) but 4 critical and 5 blocking issues prevent it from meeting the Vision promise of a premium B2B marketing website.
  - Acceptance: Fix: Final evaluation summary.

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
