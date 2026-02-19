# Implementation Plan (rendered from state)

Generated: 2026-02-19T10:45:53.388275


## Foundation

- [x] **1.1**: Verify Astro project configuration: astro.config.mjs has React integration and Tailwind v4 via @tailwindcss/vite plugin, tsconfig.json extends astro/tsconfigs/strict with jsx:react-jsx, package.json has dev/build/preview scripts. Confirm npm run dev starts on port 4321 and npm run build produces dist/ with zero errors. This is brownfield verification -- all config files already exist.
  - Value: Confirms the build pipeline foundation works so every subsequent page and component can ship reliably to static HTML -- without a working build, no visitor can see the site.
  - Acceptance: 1. npm run dev starts Astro dev server on port 4321. 2. npm run build exits 0 and produces dist/ with index.html. 3. astro.config.mjs includes react() and tailwindcss vite plugin. 4. tsconfig.json compiles without errors.

- [x] **1.2**: Verify shadcn/ui component library and blue B2B theme. Confirm globals.css has @import tailwindcss and @theme block with primary blue #1e40af, brand colors, Inter font stack. Verify src/components/ui/ contains all 10 required components: Button, Card, Input, Textarea, Label, NavigationMenu, Sheet, Badge, Separator, Pagination. Confirm src/lib/utils.ts exports cn() utility. Verify components render with correct blue theme on ui-test page.
  - Value: A professional, consistent UI component library gives visitors confidence in the brand -- every button, card, and form element reflects B2B quality rather than default unstyled HTML.
  - Acceptance: 1. global.css has @theme block with --color-primary-800: #1e40af and Inter font. 2. All 10 .tsx files exist in src/components/ui/. 3. src/lib/utils.ts exports cn(). 4. Components use CSS custom properties for theming. 5. npm run build succeeds.
  - Deps: 1.1

- [x] **1.3**: Verify BaseLayout.astro provides complete HTML shell: doctype, lang, charset, viewport meta tag, globals.css import, Inter font loading (Google Fonts or system stack), Open Graph meta tags support (og:title, og:description, og:url), canonical URL, and slot for page content. Confirm Header.astro and Footer.astro are included in the layout. Fix any missing head elements.
  - Value: Every page gets consistent HTML structure, SEO metadata, and styling -- visitors and search engines both see a properly structured professional site.
  - Acceptance: 1. BaseLayout.astro has valid HTML5 shell with lang, charset, viewport meta. 2. Imports global.css. 3. Has slot for content. 4. Supports title and description props for SEO. 5. Includes Header and Footer components.
  - Deps: 1.2

- [x] **2.1**: Create Sanity Studio project in sanity/ directory. Set up sanity.config.ts with project ID and dataset. Note: Sanity Studio only exposes env vars prefixed SANITY_STUDIO_ to browser code -- either hardcode project ID in config or use SANITY_STUDIO_PROJECT_ID. Create sanity.cli.ts. Add package.json with sanity and @sanity/vision dependencies. Configure npm scripts for sanity dev (port 3333). Use defineConfig from sanity, defineType/defineField for schema API. Verify npx sanity dev launches Studio UI.
  - Value: The site owner gets a content management dashboard — Sanity Studio is the tool they will use to manage all blog posts and page content without touching code.
  - Acceptance: 1. sanity/ directory exists with sanity.config.ts, sanity.cli.ts, package.json. 2. Config reads SANITY_PROJECT_ID and SANITY_DATASET from env. 3. npm install in sanity/ succeeds. 4. Studio starts without schema errors (empty schemas OK at this point).
  - Deps: 1.8


## Core

- [x] **1.4**: Verify Header.astro and MobileNav.tsx: Header displays site logo/brand name, desktop navigation linking all 6 pages (Home, How It Works, Services, About, Blog, Contact) with active route highlighting. MobileNav.tsx is a React island (client:load) using shadcn Sheet component for hamburger menu below 768px. Desktop nav hidden on mobile, hamburger hidden on desktop. Fix any navigation issues.
  - Value: Visitors can navigate between all pages on any device -- desktop users see clean horizontal nav, mobile users tap a hamburger menu that slides out with all page links.
  - Acceptance: 1. Header shows logo and 6 nav links on desktop (>1024px). 2. MobileNav renders hamburger that opens Sheet with all 6 links. 3. Desktop nav hidden below 768px, hamburger hidden above md breakpoint. 4. client:load directive on MobileNav. 5. Active route highlighting works.
  - Deps: 1.3

- [x] **1.5**: Verify Footer.astro: multi-column layout with navigation links to all pages, social media link placeholders (LinkedIn icon + URL), copyright text with dynamic year, and company tagline. Dark background with light text using Tailwind. Footer wired into BaseLayout so it appears on every page. Responsive: stacks to single column on mobile, multi-column grid on desktop.
  - Value: Every page has a consistent footer giving visitors secondary navigation paths and social proof -- no page feels like a dead end, reinforcing the professional brand.
  - Acceptance: 1. Footer.astro renders nav links, social placeholders, copyright with current year. 2. BaseLayout includes Footer below slot. 3. Footer visible on all pages. 4. Responsive stacking on mobile, grid on desktop. 5. npm run build succeeds.
  - Deps: 1.3

- [x] **1.6**: Verify Home page (index.astro) placeholder content: hero section with headline, subheadline, CTA button; 6 feature cards with icons, titles, descriptions; BEEP method 4-step preview (Build, Engage, Educate, Promote); 3 testimonial cards with quotes; bottom CTA banner. Confirm page uses BaseLayout, applies blue theme consistently, and responsive grid layout works (1/2/3 columns).
  - Value: Visitors landing on the homepage immediately see a professional marketing page that communicates value, method, and social proof -- the most critical page for first impressions.
  - Acceptance: 1. index.astro has hero with headline and CTA. 2. Feature cards section with 3+ cards. 3. BEEP method preview with 4 steps. 4. Testimonial cards present. 5. CTA banner at bottom. Responsive grid works.
  - Deps: 1.4, 1.5

- [x] **1.7**: Verify 4 content pages have appropriate placeholder content. How It Works: 4-step BEEP method (Build, Engage, Educate, Promote) with visual layout and descriptions. Services: 3 service sections (LinkedIn Marketing, Thought Leadership, LinkedIn Training) with benefits lists. About: company story, stats, mission, values. Contact: form placeholder with ContactForm.tsx React island (client:load). All use BaseLayout.
  - Value: Visitors can browse every page of the site and see meaningful content that communicates what Beep2B does -- the full site structure is navigable and informative.
  - Acceptance: 1. /how-it-works has 4 BEEP steps with descriptions. 2. /services has 3 service sections. 3. /about has company story and stats. 4. /contact has ContactForm React island with client:load. 5. All pages use BaseLayout with blue theme.
  - Deps: 1.4, 1.5

- [x] **1.8**: Verify blog listing page (blog/[...page].astro) with placeholder content: BlogCard.astro component showing image area, title, date, category badges, excerpt. Responsive card grid (1 col mobile, 2 col tablet, 3 col desktop). Pagination via paginate() with prev/next links. Category filter nav with links to /blog/category/[slug]. Confirm no conflicting blog/index.astro exists.
  - Value: Visitors see a professional blog listing layout ready for content marketing posts -- the card grid and pagination structure is ready for real CMS data in Epic 2.
  - Acceptance: 1. /blog renders grid of BlogCards with placeholder data. 2. BlogCard shows image area, title, date, Badge categories, excerpt. 3. Grid responsive: 1/2/3 columns at breakpoints. 4. Pagination links present. 5. No blog/index.astro conflicts.
  - Deps: 1.4, 1.5

- [x] **2.2**: Create 4 Sanity TypeScript schemas in sanity/schemas/: post.ts (title, slug, author ref, publishedAt, categories refs, featuredImage with alt text, excerpt max 200 chars, body as Portable Text), author.ts (name, slug, image, bio), category.ts (title, slug, description), page.ts (title, slug, sections array with hero/features/testimonials/textBlock/cta object types per PRD 2.4). Create schemas/index.ts registering these 4 schemas. Task 2.2b handles the remaining 3 schemas (testimonial, siteSettings, navigation).
  - Value: Defines the content model that lets the site owner create and organize all website content — blog posts, page sections, testimonials — through a structured, intuitive CMS interface.
  - Acceptance: 1. sanity/schemas/ contains post.ts, author.ts, category.ts, page.ts, index.ts. 2. post.ts has all 8 fields per PRD 2.1 (title, slug, author ref, publishedAt, categories array ref, featuredImage, excerpt, body). 3. page.ts sections array includes 5 object types: hero, features, testimonials, textBlock, cta with fields per PRD 2.4. 4. schemas/index.ts exports exactly these 4 schemas. 5. Studio loads with these 4 types visible (no validation errors).
  - Deps: 2.1

- [x] **2.2b**: Create 3 remaining Sanity schemas: testimonial.ts (name required, company optional, role optional, quote required, image optional), siteSettings.ts (title, description, logo, socialLinks object with linkedin/twitter/facebook string fields, footerText, ctaDefaultLink), navigation.ts (items array where each item has label string, href string, optional children array of same shape). Update schemas/index.ts to register all 7 schemas (4 from task 2.2 + these 3). Verify Studio sidebar shows all 7 document types.
  - Value: Completes the content model so site owner can manage testimonials, global site settings, and navigation menus — every editable piece of the site is CMS-controlled.
  - Acceptance: 1. sanity/schemas/ contains testimonial.ts, siteSettings.ts, navigation.ts. 2. schemas/index.ts exports all 7 schemas. 3. Studio shows all 7 document types in sidebar. 4. siteSettings has socialLinks object with linkedin/twitter/facebook string fields.
  - Deps: 2.2

- [x] **2.3**: Create Sanity client library at src/lib/sanity.ts. Configure @sanity/client with project ID, dataset, API version, and useCdn:true from env vars. Create GROQ query helpers: getAllPosts (paginated), getPostBySlug, getPostsByCategory, getAllCategories, getPageBySlug, getSiteSettings, getNavigation. Add @sanity/image-url builder for image URLs.
  - Value: Connects the Astro frontend to Sanity CMS data — without this bridge, no CMS content can appear on the site. Query helpers ensure consistent, efficient data fetching.
  - Acceptance: 1. src/lib/sanity.ts exports configured client and all query functions. 2. Client reads SANITY_PROJECT_ID, SANITY_DATASET, SANITY_API_TOKEN from env. 3. When env vars are empty or missing, client returns empty results (not throws). 4. GROQ queries include proper projections (not fetching entire documents). 5. Image URL builder exported. 6. TypeScript types defined for query results.
  - Deps: 2.2b

- [x] **2.4**: Wire blog listing page (blog/[...page].astro) to Sanity. Replace placeholder data with real Sanity posts via getAllPosts GROQ query in getStaticPaths. Use paginate() with pageSize:10 to generate /blog, /blog/2, /blog/3 etc. Render BlogCard.astro for each post with real data (featured image via image-url, title, publishedAt formatted date, category Badges, excerpt). Prev/next links from page.url.prev/next.
  - Value: Visitors can browse blog posts as a paginated card grid — the content marketing engine is live, showing real CMS content organized for discovery.
  - Acceptance: 1. /blog renders posts from Sanity as BlogCard grid. 2. Max 10 posts per page. 3. Pagination generates /blog/[page] routes. 4. Prev/next links navigate between pages. 5. When no Sanity data, shows placeholder message instead of crashing.
  - Deps: 2.3

- [x] **2.5**: Create individual blog post page at blog/[slug].astro (named param, NOT rest param -- rest param [...slug] would conflict with [...page] pagination route). Use getStaticPaths to generate a page per Sanity post slug. Fetch full post data including body (Portable Text), author, categories. Render Portable Text body using astro-portabletext. Display featured image, title, author name, date, category badges. Style for long-form reading with proper typography.
  - Value: Visitors can read full blog posts with rich formatting — headings, images, links, lists, blockquotes all render correctly, making the blog a credible content marketing channel.
  - Acceptance: 1. /blog/[slug] routes generated from Sanity post slugs via [slug].astro (named param). 2. Portable Text renders headings, paragraphs, images, links, lists via astro-portabletext. 3. Post metadata displayed (title, author, date, categories). 4. Featured image shown if present. 5. Graceful handling when post not found. 6. No route conflict with [...page].astro pagination.
  - Deps: 2.3

- [x] **2.6**: Create category filter pages at blog/category/[category].astro. Use getStaticPaths to generate a page per Sanity category slug. Fetch posts filtered by category via GROQ. Render same BlogCard grid layout as main blog listing. Display category title as page heading. Add CategoryFilter.tsx React island (or static Astro links) as category nav bar on blog pages.
  - Value: Visitors can find blog posts by topic — category filtering makes the 120+ post archive navigable and helps prospects find content relevant to their needs.
  - Acceptance: 1. /blog/category/[slug] routes generated from Sanity categories. 2. Only posts in that category are shown. 3. Category title displayed as heading. 4. Category filter bar appears on blog listing pages. 5. Graceful empty state when category has no posts.
  - Deps: 2.4

- [x] **3.1**: Wire Home page (index.astro) to CMS content. Fetch page data from Sanity using getPageBySlug. Render hero section (headline, subheadline, CTA button), 3-4 feature cards (icon, title, description), BEEP method 4-step preview with link to How It Works, 2-3 testimonial cards from CMS, and bottom CTA banner. Fallback to placeholder content when CMS unavailable.
  - Value: Visitors see a compelling, content-rich home page that communicates Beep2B value proposition -- the primary conversion landing page is live with CMS-managed content.
  - Acceptance: 1. Home page renders hero with CMS headline and CTA. 2. Feature cards display from CMS. 3. BEEP preview shows 4 steps with link. 4. Testimonials render from CMS. 5. CTA banner at bottom with configurable link.
  - Deps: 2.7

- [x] **3.2**: Build How It Works page with 4-step BEEP method visual layout. Each step (Build, Engage, Educate, Promote) has number/icon, heading, 2-3 sentence description. Alternating left/right layout for visual interest. Wire to CMS page content with fallback to hardcoded BEEP descriptions. CTA button at bottom linking to discovery call.
  - Value: Visitors understand exactly how the BEEP methodology works -- this page converts interest into understanding, moving prospects toward booking a call.
  - Acceptance: 1. /how-it-works shows 4 distinct BEEP steps. 2. Alternating layout (text left/right). 3. Each step has icon/number, heading, description. 4. CTA button at bottom. 5. Content from CMS with hardcoded fallback.
  - Deps: 2.7

- [x] **3.3**: Build Services page with 3 service sections on one page: LinkedIn Marketing, Thought Leadership Marketing, LinkedIn Training. Each section has heading, description, key benefits list, and CTA link. Wire to CMS page content with fallback to hardcoded service descriptions. Professional layout with consistent spacing.
  - Value: Visitors see exactly what services Beep2B offers and can navigate to a call booking -- the services page is the core sales content that drives conversions.
  - Acceptance: 1. /services shows 3 distinct service sections. 2. Each has heading, description, benefits list, CTA. 3. Content from CMS with hardcoded fallback. 4. Responsive layout. 5. CTAs link to configurable booking URL.
  - Deps: 2.7

- [x] **3.4**: Build About page (/about) and Contact page (/contact). About page: company story paragraph (founded 2014, members in 22 countries), mission statement, philosophy paragraph on systematic social selling. Wire to CMS getPageBySlug with hardcoded fallback text. CTA button at bottom linking to siteSettings.ctaDefaultLink or fallback URL. Contact page: ContactForm.tsx React island with client:load. 4 fields: name (required, text input), email (required, type=email with regex validation), company (optional, text input), message (required, textarea). On submit: POST JSON body to import.meta.env.PUBLIC_FORM_ACTION. Success state: green text Message sent. Error state: red text Something went wrong. Disable submit button while request is pending.
  - Value: Visitors learn the company story building trust, and can reach out directly via validated contact form -- completing the visitor journey from awareness to action.
  - Acceptance: 1. /about shows company story, mission, philosophy, CTA. 2. /contact has working form with 4 fields. 3. Form validates required fields client-side. 4. Submits to PUBLIC_FORM_ACTION URL. 5. Shows success/error messages after submission.
  - Deps: 2.7

- [x] **3.5**: Enhance blog post page with author bio card (name, image, bio text) at bottom and Related Posts section showing 3 posts from the same category. Fetch related posts via GROQ query filtering by shared category, excluding current post. Author bio card uses author reference data already in post query.
  - Value: Blog readers discover more content and see author credibility -- related posts increase page views and time on site, author cards build trust in the content.
  - Acceptance: 1. Blog post pages show author card with name, image, bio below content. 2. Related Posts section shows 3 posts from same category. 3. Related posts exclude current post. 4. Graceful handling when no related posts found. 5. Back to blog link present.
  - Deps: 2.5


## Integration

- [x] **2.7**: Implement graceful empty-state handling on all CMS-dependent pages. Wrap Sanity fetch calls in try/catch. Blog listing shows No posts yet when empty. Blog post returns 404 gracefully. Category pages show empty message. Home page sections show placeholder when CMS unavailable. Ensure npm run build succeeds when SANITY_PROJECT_ID is empty or invalid.
  - Value: The site never crashes when CMS has no content -- site owner can deploy immediately and add content later without the build breaking.
  - Acceptance: 1. npm run build succeeds with empty/invalid SANITY_PROJECT_ID. 2. Blog listing shows placeholder when no posts. 3. Category pages show empty message. 4. No unhandled exceptions during build. 5. Pages render graceful fallback content.
  - Deps: 2.4, 2.5, 2.6


## Polish

- [x] **3.6**: Implement SEO across all pages. Add page-specific <title> and <meta description> to BaseLayout via props. Add Open Graph tags (og:title, og:description, og:image, og:url) and canonical URL to every page. Add Organization structured data (JSON-LD) on home page. Install @astrojs/sitemap, configure in astro.config.mjs. Create public/robots.txt allowing all crawlers with sitemap reference.
  - Value: Every page is search-engine ready -- proper meta tags, OG tags, and sitemap ensure the site can be discovered by prospects searching for LinkedIn lead generation help.
  - Acceptance: 1. Every page has unique <title> and <meta description>. 2. OG tags present on all pages. 3. Canonical URL on every page. 4. Home page has Organization JSON-LD. 5. sitemap.xml generated at /sitemap-index.xml. 6. robots.txt exists at site root.
  - Deps: 3.1, 3.2, 3.3, 3.4

- [ ] **3.7**: Final build verification and layout consistency check. Run npm run build and confirm exit code 0. Verify in built dist/ output: all routes generate HTML files (index.html, how-it-works/index.html, services/index.html, about/index.html, contact/index.html, blog/index.html). Check every page includes Header and Footer components. Verify Tailwind blue-800 primary color (#1e40af) is applied to headings and CTAs. Fix any build errors, missing imports, or broken component references discovered during verification.
  - Value: The complete site is production-ready -- consistent visual quality across every page and breakpoint delivers the professional impression that converts B2B prospects.
  - Acceptance: 1. npm run build exits with code 0. 2. dist/ contains index.html for all 6+ routes. 3. Every page HTML includes Header nav links and Footer element. 4. No TypeScript or build errors in output. 5. All pages reference globals.css with blue theme CSS variables.
  - Deps: 3.5, 3.6


## Unphased

- [x] **DEDUP-402067d2-category-siteSettings**: Extract duplicate code block into shared module. Found in: sanity/schemas/category.ts, sanity/schemas/siteSettings.ts. Block starts with: }),
  - Value: Remove code duplication across sanity/schemas/category.ts, sanity/schemas/siteSettings.ts
  - Acceptance: Duplicate block extracted into a shared function/module. Both files import from the shared location. All existing tests still pass.

- [x] **DEDUP-544d65da-category-page**: Extract duplicate code block into shared module. Found in: sanity/schemas/category.ts, sanity/schemas/page.ts, sanity/schemas/post.ts. Block starts with: validation: (Rule) => Rule.required(),
  - Value: Remove code duplication across sanity/schemas/category.ts, sanity/schemas/page.ts, sanity/schemas/post.ts
  - Acceptance: Duplicate block extracted into a shared function/module. Both files import from the shared location. All existing tests still pass.

- [x] **DEDUP-6494f0e7-author-post**: Extract duplicate code block into shared module. Found in: sanity/schemas/author.ts, sanity/schemas/post.ts. Block starts with: type: 'string',
  - Value: Remove code duplication across sanity/schemas/author.ts, sanity/schemas/post.ts
  - Acceptance: Duplicate block extracted into a shared function/module. Both files import from the shared location. All existing tests still pass.

- [x] **DEDUP-9aa6fa7b-page-post**: Extract duplicate code block into shared module. Found in: sanity/schemas/page.ts, sanity/schemas/post.ts. Block starts with: { title: 'Quote', value: 'blockquote' },
  - Value: Remove code duplication across sanity/schemas/page.ts, sanity/schemas/post.ts
  - Acceptance: Duplicate block extracted into a shared function/module. Both files import from the shared location. All existing tests still pass.

- [x] **DEDUP-aad4ccf4-siteSettings-testimonial**: Extract duplicate code block into shared module. Found in: sanity/schemas/siteSettings.ts, sanity/schemas/testimonial.ts. Block starts with: options: {
  - Value: Remove code duplication across sanity/schemas/siteSettings.ts, sanity/schemas/testimonial.ts
  - Acceptance: Duplicate block extracted into a shared function/module. Both files import from the shared location. All existing tests still pass.

- [x] **DEDUP-ccbf2070-category-page**: Extract duplicate code block into shared module. Found in: sanity/schemas/category.ts, sanity/schemas/page.ts. Block starts with: }),
  - Value: Remove code duplication across sanity/schemas/category.ts, sanity/schemas/page.ts
  - Acceptance: Duplicate block extracted into a shared function/module. Both files import from the shared location. All existing tests still pass.

- [x] **SPLIT-FN-sanity-schemas-page-ts**: Split long functions in sanity/schemas/page.ts: featuresSection(53L), textBlockSection(61L). Extract helper functions to keep each function under 50 lines.
  - Value: Improve readability and testability of sanity/schemas/page.ts
  - Acceptance: No function in sanity/schemas/page.ts exceeds 50 lines. All existing tests still pass.

- [x] **SPLIT-FN-sanity-schemas-portableTextConfig-ts**: Split long functions in sanity/schemas/portableTextConfig.ts: createPortableTextBlock(57L). Extract helper functions to keep each function under 50 lines.
  - Value: Improve readability and testability of sanity/schemas/portableTextConfig.ts
  - Acceptance: No function in sanity/schemas/portableTextConfig.ts exceeds 50 lines. All existing tests still pass.

- [B] **STRUCTURE-prd-conformance**: PRD files still missing: astro.config.mjs          # Astro config with React + Tailwind, tailwind.config.mjs       # Tailwind config with shadcn theme, src/layouts/BaseLayout.astro  # HTML shell, head, nav, footer, src/components/ui/               # shadcn/ui components (Button, Card, etc.), src/components/Header.astro      # Site header with navigation, src/components/Footer.astro      # Site footer with links, social, newsletter, src/components/Hero.astro        # Hero section (reusable across pages), src/components/FeatureCard.astro # Feature/benefit card, src/components/BlogCard.astro    # Blog post preview card, src/components/ContactForm.tsx   # React island — interactive form
  - Value: Ensure project structure matches PRD specification
  - Acceptance: All files listed in PRD directory tree exist on disk.

- [x] **VRC-15-gap-1**: Install shadcn Sheet, NavigationMenu, and Pagination components and refactor MobileNav.tsx to use Sheet instead of custom dropdown
  - Value: MobileNav.tsx uses a custom toggle/dropdown instead of shadcn Sheet component -- Epic 1 specifically requires Sheet-based hamburger menu. Also NavigationMenu and Pagination shadcn components are not installed (not in src/components/ui/). Only 7 of 10 required shadcn components exist.
  - Acceptance: Gap 'gap-1' resolved: MobileNav.tsx uses a custom toggle/dropdown instead of shadcn Sheet component -- Epic 1 specifically requires Sheet-based hamburger menu. Also NavigationMenu and Pagination shadcn components are not installed (not in src/components/ui/). Only 7 of 10 required shadcn components exist.

- [x] **VRC-15-gap-2**: Add Inter font loading via Google Fonts link in BaseLayout head and update --font-sans in globals.css to use Inter as primary font
  - Value: globals.css uses generic system font stack (ui-sans-serif, system-ui) instead of Inter font as specified in Epic 1 deliverables. No Inter font is loaded via Google Fonts or local files.
  - Acceptance: Gap 'gap-2' resolved: globals.css uses generic system font stack (ui-sans-serif, system-ui) instead of Inter font as specified in Epic 1 deliverables. No Inter font is loaded via Google Fonts or local files.

- [x] **VRC-40-gap-1**: Task 2.5 already exists
  - Value: Blog post page (blog/[slug].astro) does not exist -- visitors cannot read individual blog posts, BlogCard links 404. Task 2.5 covers this.
  - Acceptance: Gap 'gap-1' resolved: Blog post page (blog/[slug].astro) does not exist -- visitors cannot read individual blog posts, BlogCard links 404. Task 2.5 covers this.


## Verification

- [x] **1.9**: Final build verification and responsive layout check. Run npm run build and confirm zero errors, dist/ contains HTML for all 6 routes (/, /how-it-works, /services, /about, /contact, /blog). Verify responsive behavior: Header desktop nav visible >1024px, hamburger <768px. Cards stack on mobile, grid on tablet/desktop. Footer consistent across pages. Blue theme applied uniformly. Fix any build warnings or layout issues.
  - Value: Confirms the complete Epic 1 deliverable: a visitor can browse a responsive 6-page marketing website with professional blue design that builds to static HTML with zero errors.
  - Acceptance: 1. npm run build exits 0 with no errors. 2. dist/ contains HTML for all 6 page routes. 3. No TypeScript compilation errors. 4. Responsive breakpoints verified. 5. Consistent blue B2B theme across all pages.
  - Deps: 1.6, 1.7, 1.8
