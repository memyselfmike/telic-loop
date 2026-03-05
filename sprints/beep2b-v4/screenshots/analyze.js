const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

  // ========= HOW IT WORKS =========
  console.log('\n=== HOW IT WORKS PAGE ===');
  await page.goto('http://localhost:4321/how-it-works', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1500);

  // Check hero heading
  const hiwHero = await page.evaluate(() => {
    const headings = document.querySelectorAll('h1, h2, h3');
    return Array.from(headings).slice(0, 3).map(h => {
      const s = getComputedStyle(h);
      return { tag: h.tagName, text: h.textContent.trim().substring(0,60), fontSize: s.fontSize, fontWeight: s.fontWeight, color: s.color };
    });
  });
  console.log('Headings:', JSON.stringify(hiwHero, null, 2));

  // Check all buttons on the page
  const hiwButtons = await page.evaluate(() => {
    const allLinks = document.querySelectorAll('a');
    const btns = Array.from(allLinks).filter(a => {
      const s = getComputedStyle(a);
      return a.textContent.includes('Book') || a.textContent.includes('View') || a.textContent.includes('Learn') || a.textContent.includes('Call') || a.textContent.includes('Schedule');
    });
    return btns.map(b => {
      const s = getComputedStyle(b);
      return { text: b.textContent.trim().substring(0,40), padding: s.padding, display: s.display, fontSize: s.fontSize, bg: s.backgroundColor, borderRadius: s.borderRadius, className: b.className };
    });
  });
  console.log('CTA links:', JSON.stringify(hiwButtons, null, 2));

  // Check section labels
  const sectionLabels = await page.evaluate(() => {
    const labels = document.querySelectorAll('.section-label');
    return Array.from(labels).map(l => {
      const r = l.getBoundingClientRect();
      const s = getComputedStyle(l);
      const parentS = getComputedStyle(l.parentElement);
      return { text: l.textContent.trim(), left: Math.round(r.left), textAlign: parentS.textAlign, parentClass: l.parentElement.className };
    });
  });
  console.log('Section labels:', JSON.stringify(sectionLabels, null, 2));

  // Check animated elements
  const animations = await page.evaluate(() => {
    const all = document.querySelectorAll('*');
    const animated = [];
    for (const el of all) {
      const s = getComputedStyle(el);
      if (s.animationName !== 'none' || s.opacity === '0') {
        animated.push({ tag: el.tagName, class: el.className.substring(0,60), opacity: s.opacity, animation: s.animationName });
      }
    }
    return animated.slice(0, 10);
  });
  console.log('Animated/hidden elements:', JSON.stringify(animations, null, 2));

  // Check for invisible content (opacity: 0 that should animate in)
  const invisible = await page.evaluate(() => {
    const all = document.querySelectorAll('*');
    const results = [];
    for (const el of all) {
      const s = getComputedStyle(el);
      if (s.opacity === '0' && el.textContent.trim().length > 0 && el.offsetHeight > 0) {
        results.push({ tag: el.tagName, class: el.className.substring(0,60), text: el.textContent.trim().substring(0,40) });
      }
    }
    return results;
  });
  console.log('Invisible elements (opacity:0):', JSON.stringify(invisible, null, 2));

  // ========= SERVICES =========
  console.log('\n=== SERVICES PAGE ===');
  await page.goto('http://localhost:4321/services', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1500);

  const svcHeadings = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('h1, h2, h3, h4')).slice(0, 8).map(h => {
      const s = getComputedStyle(h);
      return { tag: h.tagName, text: h.textContent.trim().substring(0,60), fontSize: s.fontSize, fontWeight: s.fontWeight };
    });
  });
  console.log('Headings:', JSON.stringify(svcHeadings, null, 2));

  // Check service number display
  const svcNumbers = await page.evaluate(() => {
    const nums = document.querySelectorAll('[class*=number], [class*=num], .service-number');
    return Array.from(nums).map(n => {
      const s = getComputedStyle(n);
      return { text: n.textContent.trim(), fontSize: s.fontSize, fontWeight: s.fontWeight, opacity: s.opacity, color: s.color };
    });
  });
  console.log('Service numbers:', JSON.stringify(svcNumbers, null, 2));

  // Service buttons
  const svcButtons = await page.evaluate(() => {
    const allLinks = document.querySelectorAll('a');
    const btns = Array.from(allLinks).filter(a => {
      return a.textContent.includes('Book') || a.textContent.includes('Learn') || a.textContent.includes('Schedule');
    });
    return btns.map(b => {
      const s = getComputedStyle(b);
      return { text: b.textContent.trim().substring(0,40), padding: s.padding, bg: s.backgroundColor, className: b.className };
    });
  });
  console.log('Service buttons:', JSON.stringify(svcButtons, null, 2));

  // Check service blocks existence
  const svcBlocks = await page.evaluate(() => {
    const blocks = document.querySelectorAll('[class*=service-block], [class*=service-card], section > div > div');
    return { count: blocks.length };
  });
  console.log('Service blocks:', JSON.stringify(svcBlocks));

  // ========= ABOUT =========
  console.log('\n=== ABOUT PAGE ===');
  await page.goto('http://localhost:4321/about', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1500);

  const aboutHeadings = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('h1, h2, h3')).slice(0, 10).map(h => {
      const s = getComputedStyle(h);
      return { tag: h.tagName, text: h.textContent.trim().substring(0,60), fontSize: s.fontSize, fontWeight: s.fontWeight };
    });
  });
  console.log('Headings:', JSON.stringify(aboutHeadings, null, 2));

  // Values cards
  const valuesCards = await page.evaluate(() => {
    const cards = document.querySelectorAll('[class*=value-card], [class*=values] [class*=card]');
    if (cards.length === 0) {
      // Try broader search
      const allCards = document.querySelectorAll('[class*=card]');
      return { found: allCards.length, broad: true, samples: Array.from(allCards).slice(0,4).map(c => c.className) };
    }
    return Array.from(cards).map(c => ({
      class: c.className,
      heading: c.querySelector('h3, h4')?.textContent.trim()
    }));
  });
  console.log('Values cards:', JSON.stringify(valuesCards, null, 2));

  // Stats counters
  const stats = await page.evaluate(() => {
    const statEls = document.querySelectorAll('[class*=stat], [class*=counter], [class*=number]');
    return Array.from(statEls).slice(0, 6).map(s => ({
      class: s.className.substring(0,40),
      text: s.textContent.trim().substring(0,40),
      fontSize: getComputedStyle(s).fontSize
    }));
  });
  console.log('Stats:', JSON.stringify(stats, null, 2));

  // Section labels on about
  const aboutLabels = await page.evaluate(() => {
    const labels = document.querySelectorAll('.section-label');
    return Array.from(labels).map(l => {
      const r = l.getBoundingClientRect();
      return { text: l.textContent.trim(), left: Math.round(r.left) };
    });
  });
  console.log('About section labels:', JSON.stringify(aboutLabels, null, 2));

  // ========= CONTACT =========
  console.log('\n=== CONTACT PAGE ===');
  await page.goto('http://localhost:4321/contact', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1500);

  // Check form fields
  const contactForm = await page.evaluate(() => {
    const form = document.querySelector('form');
    if (!form) return 'No form found';
    const inputs = form.querySelectorAll('input, textarea, select');
    return Array.from(inputs).map(i => {
      const s = getComputedStyle(i);
      return { type: i.type || i.tagName, name: i.name, placeholder: i.placeholder, padding: s.padding, bg: s.backgroundColor, border: s.border };
    });
  });
  console.log('Form fields:', JSON.stringify(contactForm, null, 2));

  // Check split layout
  const contactLayout = await page.evaluate(() => {
    const main = document.querySelector('main') || document.querySelector('[class*=contact]');
    if (!main) return 'no main';
    const children = main.querySelectorAll(':scope > section, :scope > div');
    return Array.from(children).slice(0, 5).map(c => ({
      tag: c.tagName,
      class: c.className.substring(0, 60),
      display: getComputedStyle(c).display,
      gridTemplate: getComputedStyle(c).gridTemplateColumns,
      width: c.getBoundingClientRect().width
    }));
  });
  console.log('Contact layout:', JSON.stringify(contactLayout, null, 2));

  // Submit button
  const submitBtn = await page.evaluate(() => {
    const btn = document.querySelector('button[type=submit], input[type=submit]');
    if (!btn) return 'No submit button';
    const s = getComputedStyle(btn);
    return { text: btn.textContent.trim(), padding: s.padding, bg: s.backgroundColor, color: s.color, fontSize: s.fontSize, width: s.width, borderRadius: s.borderRadius };
  });
  console.log('Submit button:', JSON.stringify(submitBtn, null, 2));

  // ========= BLOG =========
  console.log('\n=== BLOG PAGE ===');
  await page.goto('http://localhost:4321/blog', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1500);

  // Blog cards
  const blogCards = await page.evaluate(() => {
    const cards = document.querySelectorAll('[class*=blog-card], [class*=post-card], article');
    return Array.from(cards).slice(0, 4).map(c => {
      const img = c.querySelector('img');
      const title = c.querySelector('h2, h3, h4');
      const link = c.querySelector('a[class*=read], a[href*=blog]');
      return {
        class: c.className.substring(0,40),
        hasImg: !!img,
        imgSrc: img ? img.src.substring(0,60) : null,
        imgAlt: img ? img.alt : null,
        imgLoaded: img ? img.complete && img.naturalWidth > 0 : false,
        title: title ? title.textContent.trim() : null,
        readMore: link ? { text: link.textContent.trim(), padding: getComputedStyle(link).padding } : null
      };
    });
  });
  console.log('Blog cards:', JSON.stringify(blogCards, null, 2));

  // Category filter
  const categories = await page.evaluate(() => {
    const cats = document.querySelectorAll('[class*=categor], [class*=filter], [class*=tag]');
    return Array.from(cats).slice(0, 12).map(c => ({
      tag: c.tagName,
      text: c.textContent.trim().substring(0, 30),
      class: c.className.substring(0, 40),
      padding: getComputedStyle(c).padding,
      bg: getComputedStyle(c).backgroundColor
    }));
  });
  console.log('Category filters:', JSON.stringify(categories, null, 2));

  // Pagination
  const pagination = await page.evaluate(() => {
    const pag = document.querySelector('[class*=paginat], nav[aria-label*=paginat]');
    return pag ? { exists: true, class: pag.className, html: pag.innerHTML.substring(0, 200) } : { exists: false };
  });
  console.log('Pagination:', JSON.stringify(pagination, null, 2));

  // ========= BLOG POST =========
  console.log('\n=== BLOG POST PAGE ===');
  await page.goto('http://localhost:4321/blog/the-anatomy-of-a-high-converting-linkedin-profile', { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(1500);

  // Featured image
  const featuredImg = await page.evaluate(() => {
    const imgs = document.querySelectorAll('img');
    const featured = Array.from(imgs).filter(i => i.width > 400);
    return featured.map(i => ({
      src: i.src.substring(0, 80),
      alt: i.alt,
      width: i.width,
      height: i.height,
      loaded: i.complete && i.naturalWidth > 0,
      naturalWidth: i.naturalWidth
    }));
  });
  console.log('Featured images:', JSON.stringify(featuredImg, null, 2));

  // Title, author, date
  const postMeta = await page.evaluate(() => {
    const h1 = document.querySelector('h1');
    const author = document.querySelector('[class*=author], [class*=meta]');
    const date = document.querySelector('time, [class*=date]');
    return {
      title: h1 ? { text: h1.textContent.trim(), fontSize: getComputedStyle(h1).fontSize, fontWeight: getComputedStyle(h1).fontWeight } : null,
      author: author ? { text: author.textContent.trim().substring(0, 60) } : null,
      date: date ? { text: date.textContent.trim() } : null
    };
  });
  console.log('Post meta:', JSON.stringify(postMeta, null, 2));

  // Content body
  const postContent = await page.evaluate(() => {
    const content = document.querySelector('[class*=content], article, .prose');
    if (!content) return 'No content container';
    const h2s = content.querySelectorAll('h2');
    const ps = content.querySelectorAll('p');
    const uls = content.querySelectorAll('ul');
    const blockquotes = content.querySelectorAll('blockquote');
    return {
      h2Count: h2s.length,
      pCount: ps.length,
      ulCount: uls.length,
      blockquoteCount: blockquotes.length,
      firstP: ps[0] ? ps[0].textContent.trim().substring(0, 80) : null,
      h2Samples: Array.from(h2s).map(h => h.textContent.trim())
    };
  });
  console.log('Post content:', JSON.stringify(postContent, null, 2));

  // Related posts
  const related = await page.evaluate(() => {
    const section = document.querySelector('[class*=related]');
    return section ? { exists: true, html: section.innerHTML.substring(0, 300) } : { exists: false };
  });
  console.log('Related posts:', JSON.stringify(related, null, 2));

  await browser.close();
  console.log('\nDone!');
})();
