# Implementation Plan (rendered from state)

Generated: 2026-02-18T18:56:58.397019


## Foundation

- [ ] **1.1**: Initialize Astro 5 project with React integration, TypeScript, and Tailwind CSS v4. Run npm create astro, install @astrojs/react, then install tailwindcss and @tailwindcss/vite. Configure astro.config.mjs with React integration and Tailwind via vite.plugins (not @astrojs/tailwind which is deprecated for Tailwind v4). Create src/styles/globals.css with @import tailwindcss directive. Set up tsconfig.json. Verify npm run dev starts and npm run build produces dist/ output.
  - Value: Establishes the project foundation so every subsequent page, component, and integration has a working build pipeline — without this, nothing else can begin.
  - Acceptance: 1. npm run dev starts Astro dev server on port 4321. 2. npm run build produces dist/ folder with an index.html. 3. astro.config.mjs includes react() integration and tailwindcss() in vite.plugins array. 4. TypeScript compiles without errors. 5. globals.css has @import tailwindcss directive.

- [ ] **1.2**: Set up shadcn/ui with blue B2B theme. Run npx shadcn@latest init (Astro framework). Configure CSS variables in globals.css using @theme directive for blue primary (#1e40af), slate text, white/gray backgrounds per PRD 4.1. Tailwind v4 uses CSS-based config (@theme), not tailwind.config.mjs. Install cn utility in src/lib/utils.ts. Add core shadcn components: Button, Card, Input, Textarea, Label, Badge, Separator.
  - Value: Provides the consistent, professional UI component library that gives every page a polished B2B look — visitors see quality, not a DIY site.
  - Acceptance: 1. globals.css has @import tailwindcss and @theme block with CSS custom properties for blue theme. 2. src/components/ui/ contains Button, Card, Input, Textarea, Label, Badge, Separator .tsx files. 3. src/lib/utils.ts exports cn() function. 4. A test page renders a Button and Card with blue theme colors. 5. npm run build succeeds. 6. No tailwind.config.mjs file needed (Tailwind v4 uses CSS-based @theme config).
  - Deps: 1.1

- [ ] **1.3**: Create BaseLayout.astro with HTML shell: doctype, lang, charset, viewport meta, globals.css import, Inter font stack (system font fallback), and a <slot /> for page content. Include shared head elements (favicon link, default title/description). This is the wrapper every page will use.
  - Value: Ensures every page on the site has consistent HTML structure, styling, and head metadata — visitors experience a unified, professional site rather than disjointed pages.
  - Acceptance: 1. src/layouts/BaseLayout.astro exists with valid HTML5 shell. 2. Imports globals.css. 3. Has <slot /> for content. 4. Default <title> and <meta description> are set. 5. index.astro uses BaseLayout and renders.
  - Deps: 1.2

- [ ] **1.4**: Build Header.astro with site logo/name text, desktop navigation bar linking all 6 pages (Home, How It Works, Services, About, Blog, Contact), and MobileNav.tsx React island using shadcn Sheet component for hamburger menu at <768px. Desktop nav uses horizontal links visible at >1024px. Add shadcn Sheet and NavigationMenu components if not yet installed.
  - Value: Visitors can navigate between all pages on any device — desktop users see a clean nav bar, mobile users tap a hamburger menu. Navigation is the core site usability feature.
  - Acceptance: 1. Header.astro renders site name and 6 navigation links on desktop. 2. MobileNav.tsx renders hamburger button that opens Sheet with all 6 links. 3. Desktop nav hidden below 768px, hamburger hidden above 1024px. 4. client:load directive on MobileNav. 5. npm run build succeeds.
  - Deps: 1.3

- [ ] **1.5**: Build Footer.astro with navigation links to all pages, social media link placeholders (LinkedIn, Twitter), copyright text with current year, and a brief company tagline. Use Tailwind for dark background section with light text. Wire Footer into BaseLayout so it appears on every page.
  - Value: Every page has a consistent footer giving visitors secondary navigation and reinforcing the professional brand — no page feels like a dead end.
  - Acceptance: 1. Footer.astro renders nav links, social placeholders, copyright. 2. BaseLayout includes Footer below the slot. 3. Footer visible on all pages. 4. Responsive: stacks on mobile, horizontal layout on desktop. 5. npm run build succeeds.
  - Deps: 1.3

- [ ] **2.1**: Create Sanity Studio project in sanity/ directory. Set up sanity.config.ts with project ID and dataset. Note: Sanity Studio only exposes env vars prefixed SANITY_STUDIO_ to browser code -- either hardcode project ID in config or use SANITY_STUDIO_PROJECT_ID. Create sanity.cli.ts. Add package.json with sanity and @sanity/vision dependencies. Configure npm scripts for sanity dev (port 3333). Use defineConfig from sanity, defineType/defineField for schema API. Verify npx sanity dev launches Studio UI.
  - Value: The site owner gets a content management dashboard — Sanity Studio is the tool they will use to manage all blog posts and page content without touching code.
  - Acceptance: 1. sanity/ directory exists with sanity.config.ts, sanity.cli.ts, package.json. 2. Config reads SANITY_PROJECT_ID and SANITY_DATASET from env. 3. npm install in sanity/ succeeds. 4. Studio starts without schema errors (empty schemas OK at this point).
  - Deps: 1.8


## Core

- [ ] **1.6**: Create 5 page routes (excluding blog, handled in task 1.7) with placeholder content using BaseLayout. Home (index.astro): hero section with headline, subheadline, CTA button, 3 feature cards, testimonial placeholders, bottom CTA. How It Works: 4-step BEEP method placeholders. Services: 3 service sections. About: company story placeholder. Contact: form placeholder. All pages use BaseLayout with Header and Footer.
  - Value: Visitors can navigate to every page and see meaningful placeholder content — the complete site structure is browsable, proving the navigation and layout system works end-to-end.
  - Acceptance: 1. All 5 non-blog routes resolve: /, /how-it-works, /services, /about, /contact. 2. Each page uses BaseLayout with Header and Footer. 3. Each has section-appropriate placeholder content (not empty). 4. Blue theme colors applied. 5. npm run build succeeds with all routes.
  - Deps: 1.4, 1.5

- [ ] **1.7**: Create blog/[...page].astro as the blog listing page with placeholder blog card grid (BlogCard.astro component showing image placeholder, title, date, category badges, excerpt). Use getStaticPaths with paginate() returning hardcoded placeholder posts. Build responsive grid: 1 col mobile, 2 col tablet, 3 col desktop. Render prev/next pagination links from page.url.prev and page.url.next. Do NOT create a separate blog/index.astro -- the [...page].astro rest route serves /blog as page 1.
  - Value: Visitors see a professional blog listing layout that previews content marketing posts — the card grid and pagination structure is ready for real CMS data in Epic 2.
  - Acceptance: 1. /blog route renders a grid of placeholder BlogCards (served by [...page].astro page 1). 2. BlogCard shows image area, title, date, category Badge, excerpt. 3. Grid responsive: 1/2/3 columns. 4. Pagination links rendered (pointing to /blog/2 etc with placeholder data). 5. No blog/index.astro file exists (would conflict with [...page].astro). 6. npm run build succeeds.
  - Deps: 1.4, 1.5

- [ ] **2.2**: Create 4 Sanity TypeScript schemas in sanity/schemas/: post.ts (title, slug, author ref, publishedAt, categories refs, featuredImage with alt text, excerpt max 200 chars, body as Portable Text), author.ts (name, slug, image, bio), category.ts (title, slug, description), page.ts (title, slug, sections array with hero/features/testimonials/textBlock/cta object types per PRD 2.4). Create schemas/index.ts registering these 4 schemas. Task 2.2b handles the remaining 3 schemas (testimonial, siteSettings, navigation).
  - Value: Defines the content model that lets the site owner create and organize all website content — blog posts, page sections, testimonials — through a structured, intuitive CMS interface.
  - Acceptance: 1. sanity/schemas/ contains post.ts, author.ts, category.ts, page.ts, index.ts. 2. post.ts has all 8 fields per PRD 2.1 (title, slug, author ref, publishedAt, categories array ref, featuredImage, excerpt, body). 3. page.ts sections array includes 5 object types: hero, features, testimonials, textBlock, cta with fields per PRD 2.4. 4. schemas/index.ts exports exactly these 4 schemas. 5. Studio loads with these 4 types visible (no validation errors).
  - Deps: 2.1

- [ ] **2.2b**: Create 3 remaining Sanity schemas: testimonial.ts (name required, company optional, role optional, quote required, image optional), siteSettings.ts (title, description, logo, socialLinks object with linkedin/twitter/facebook string fields, footerText, ctaDefaultLink), navigation.ts (items array where each item has label string, href string, optional children array of same shape). Update schemas/index.ts to register all 7 schemas (4 from task 2.2 + these 3). Verify Studio sidebar shows all 7 document types.
  - Value: Completes the content model so site owner can manage testimonials, global site settings, and navigation menus — every editable piece of the site is CMS-controlled.
  - Acceptance: 1. sanity/schemas/ contains testimonial.ts, siteSettings.ts, navigation.ts. 2. schemas/index.ts exports all 7 schemas. 3. Studio shows all 7 document types in sidebar. 4. siteSettings has socialLinks object with linkedin/twitter/facebook string fields.
  - Deps: 2.2

- [ ] **2.3**: Create Sanity client library at src/lib/sanity.ts. Configure @sanity/client with project ID, dataset, API version, and useCdn:true from env vars. Create GROQ query helpers: getAllPosts (paginated), getPostBySlug, getPostsByCategory, getAllCategories, getPageBySlug, getSiteSettings, getNavigation. Add @sanity/image-url builder for image URLs.
  - Value: Connects the Astro frontend to Sanity CMS data — without this bridge, no CMS content can appear on the site. Query helpers ensure consistent, efficient data fetching.
  - Acceptance: 1. src/lib/sanity.ts exports configured client and all query functions. 2. Client reads SANITY_PROJECT_ID, SANITY_DATASET, SANITY_API_TOKEN from env. 3. When env vars are empty or missing, client returns empty results (not throws). 4. GROQ queries include proper projections (not fetching entire documents). 5. Image URL builder exported. 6. TypeScript types defined for query results.
  - Deps: 2.2b

- [ ] **2.4**: Wire blog listing page (blog/[...page].astro) to Sanity. Replace placeholder data with real Sanity posts via getAllPosts GROQ query in getStaticPaths. Use paginate() with pageSize:10 to generate /blog, /blog/2, /blog/3 etc. Render BlogCard.astro for each post with real data (featured image via image-url, title, publishedAt formatted date, category Badges, excerpt). Prev/next links from page.url.prev/next.
  - Value: Visitors can browse blog posts as a paginated card grid — the content marketing engine is live, showing real CMS content organized for discovery.
  - Acceptance: 1. /blog renders posts from Sanity as BlogCard grid. 2. Max 10 posts per page. 3. Pagination generates /blog/[page] routes. 4. Prev/next links navigate between pages. 5. When no Sanity data, shows placeholder message instead of crashing.
  - Deps: 2.3

- [ ] **2.5**: Create individual blog post page at blog/[slug].astro (named param, NOT rest param -- rest param [...slug] would conflict with [...page] pagination route). Use getStaticPaths to generate a page per Sanity post slug. Fetch full post data including body (Portable Text), author, categories. Render Portable Text body using astro-portabletext. Display featured image, title, author name, date, category badges. Style for long-form reading with proper typography.
  - Value: Visitors can read full blog posts with rich formatting — headings, images, links, lists, blockquotes all render correctly, making the blog a credible content marketing channel.
  - Acceptance: 1. /blog/[slug] routes generated from Sanity post slugs via [slug].astro (named param). 2. Portable Text renders headings, paragraphs, images, links, lists via astro-portabletext. 3. Post metadata displayed (title, author, date, categories). 4. Featured image shown if present. 5. Graceful handling when post not found. 6. No route conflict with [...page].astro pagination.
  - Deps: 2.3

- [ ] **2.6**: Create category filter pages at blog/category/[category].astro. Use getStaticPaths to generate a page per Sanity category slug. Fetch posts filtered by category via GROQ. Render same BlogCard grid layout as main blog listing. Display category title as page heading. Add CategoryFilter.tsx React island (or static Astro links) as category nav bar on blog pages.
  - Value: Visitors can find blog posts by topic — category filtering makes the 120+ post archive navigable and helps prospects find content relevant to their needs.
  - Acceptance: 1. /blog/category/[slug] routes generated from Sanity categories. 2. Only posts in that category are shown. 3. Category title displayed as heading. 4. Category filter bar appears on blog listing pages. 5. Graceful empty state when category has no posts.
  - Deps: 2.4

- [ ] **3.1**: Wire Home page (index.astro) to CMS content. Fetch page data from Sanity using getPageBySlug. Render hero section (headline, subheadline, CTA button), 3-4 feature cards (icon, title, description), BEEP method 4-step preview with link to How It Works, 2-3 testimonial cards from CMS, and bottom CTA banner. Fallback to placeholder content when CMS unavailable.
  - Value: Visitors see a compelling, content-rich home page that communicates Beep2B value proposition -- the primary conversion landing page is live with CMS-managed content.
  - Acceptance: 1. Home page renders hero with CMS headline and CTA. 2. Feature cards display from CMS. 3. BEEP preview shows 4 steps with link. 4. Testimonials render from CMS. 5. CTA banner at bottom with configurable link.
  - Deps: 2.7

- [ ] **3.2**: Build How It Works page with 4-step BEEP method visual layout. Each step (Build, Engage, Educate, Promote) has number/icon, heading, 2-3 sentence description. Alternating left/right layout for visual interest. Wire to CMS page content with fallback to hardcoded BEEP descriptions. CTA button at bottom linking to discovery call.
  - Value: Visitors understand exactly how the BEEP methodology works -- this page converts interest into understanding, moving prospects toward booking a call.
  - Acceptance: 1. /how-it-works shows 4 distinct BEEP steps. 2. Alternating layout (text left/right). 3. Each step has icon/number, heading, description. 4. CTA button at bottom. 5. Content from CMS with hardcoded fallback.
  - Deps: 2.7

- [ ] **3.3**: Build Services page with 3 service sections on one page: LinkedIn Marketing, Thought Leadership Marketing, LinkedIn Training. Each section has heading, description, key benefits list, and CTA link. Wire to CMS page content with fallback to hardcoded service descriptions. Professional layout with consistent spacing.
  - Value: Visitors see exactly what services Beep2B offers and can navigate to a call booking -- the services page is the core sales content that drives conversions.
  - Acceptance: 1. /services shows 3 distinct service sections. 2. Each has heading, description, benefits list, CTA. 3. Content from CMS with hardcoded fallback. 4. Responsive layout. 5. CTAs link to configurable booking URL.
  - Deps: 2.7

- [ ] **3.4**: Build About page (/about) and Contact page (/contact). About page: company story paragraph (founded 2014, members in 22 countries), mission statement, philosophy paragraph on systematic social selling. Wire to CMS getPageBySlug with hardcoded fallback text. CTA button at bottom linking to siteSettings.ctaDefaultLink or fallback URL. Contact page: ContactForm.tsx React island with client:load. 4 fields: name (required, text input), email (required, type=email with regex validation), company (optional, text input), message (required, textarea). On submit: POST JSON body to import.meta.env.PUBLIC_FORM_ACTION. Success state: green text Message sent. Error state: red text Something went wrong. Disable submit button while request is pending.
  - Value: Visitors learn the company story building trust, and can reach out directly via validated contact form -- completing the visitor journey from awareness to action.
  - Acceptance: 1. /about shows company story, mission, philosophy, CTA. 2. /contact has working form with 4 fields. 3. Form validates required fields client-side. 4. Submits to PUBLIC_FORM_ACTION URL. 5. Shows success/error messages after submission.
  - Deps: 2.7

- [ ] **3.5**: Enhance blog post page with author bio card (name, image, bio text) at bottom and Related Posts section showing 3 posts from the same category. Fetch related posts via GROQ query filtering by shared category, excluding current post. Author bio card uses author reference data already in post query.
  - Value: Blog readers discover more content and see author credibility -- related posts increase page views and time on site, author cards build trust in the content.
  - Acceptance: 1. Blog post pages show author card with name, image, bio below content. 2. Related Posts section shows 3 posts from same category. 3. Related posts exclude current post. 4. Graceful handling when no related posts found. 5. Back to blog link present.
  - Deps: 2.5


## Verification

- [ ] **1.8**: Verify responsive layout across all breakpoints and confirm npm run build succeeds with zero errors. Check: Header desktop nav visible >1024px, hamburger <768px. All 6 pages render with blue theme. Cards stack on mobile, grid on desktop. Footer consistent. Fix any build warnings or layout breaks found.
  - Value: Confirms Epic 1 deliverable: a complete, responsive, navigable marketing site that builds to static HTML — this is the foundation all CMS content will be layered onto.
  - Acceptance: 1. npm run build completes with exit code 0. 2. dist/ contains HTML for all 6 routes. 3. No TypeScript or build errors. 4. Header responsive behavior verified. 5. All pages use consistent blue theme.
  - Deps: 1.6, 1.7


## Integration

- [ ] **2.7**: Implement graceful empty-state handling on all CMS-dependent pages. Wrap Sanity fetch calls in try/catch. Blog listing shows No posts yet when empty. Blog post returns 404 gracefully. Category pages show empty message. Home page sections show placeholder when CMS unavailable. Ensure npm run build succeeds when SANITY_PROJECT_ID is empty or invalid.
  - Value: The site never crashes when CMS has no content -- site owner can deploy immediately and add content later without the build breaking.
  - Acceptance: 1. npm run build succeeds with empty/invalid SANITY_PROJECT_ID. 2. Blog listing shows placeholder when no posts. 3. Category pages show empty message. 4. No unhandled exceptions during build. 5. Pages render graceful fallback content.
  - Deps: 2.4, 2.5, 2.6


## Polish

- [ ] **3.6**: Implement SEO across all pages. Add page-specific <title> and <meta description> to BaseLayout via props. Add Open Graph tags (og:title, og:description, og:image, og:url) and canonical URL to every page. Add Organization structured data (JSON-LD) on home page. Install @astrojs/sitemap, configure in astro.config.mjs. Create public/robots.txt allowing all crawlers with sitemap reference.
  - Value: Every page is search-engine ready -- proper meta tags, OG tags, and sitemap ensure the site can be discovered by prospects searching for LinkedIn lead generation help.
  - Acceptance: 1. Every page has unique <title> and <meta description>. 2. OG tags present on all pages. 3. Canonical URL on every page. 4. Home page has Organization JSON-LD. 5. sitemap.xml generated at /sitemap-index.xml. 6. robots.txt exists at site root.
  - Deps: 3.1, 3.2, 3.3, 3.4

- [ ] **3.7**: Final build verification and layout consistency check. Run npm run build and confirm exit code 0. Verify in built dist/ output: all routes generate HTML files (index.html, how-it-works/index.html, services/index.html, about/index.html, contact/index.html, blog/index.html). Check every page includes Header and Footer components. Verify Tailwind blue-800 primary color (#1e40af) is applied to headings and CTAs. Fix any build errors, missing imports, or broken component references discovered during verification.
  - Value: The complete site is production-ready -- consistent visual quality across every page and breakpoint delivers the professional impression that converts B2B prospects.
  - Acceptance: 1. npm run build exits with code 0. 2. dist/ contains index.html for all 6+ routes. 3. Every page HTML includes Header nav links and Footer element. 4. No TypeScript or build errors in output. 5. All pages reference globals.css with blue theme CSS variables.
  - Deps: 3.5, 3.6
