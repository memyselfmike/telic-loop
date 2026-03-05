import { chromium } from 'playwright';

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  // Navigate to a page first so we can use fetch
  await page.goto('http://localhost:3000/api/posts', { waitUntil: 'networkidle', timeout: 10000 }).catch(() => {});

  // Login via API first
  const loginResult = await page.evaluate(async () => {
    const res = await fetch('/api/users/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'admin@beep2b.com', password: 'changeme' }),
    });
    return await res.json();
  });
  const token = loginResult.token;
  console.log('Logged in as:', loginResult.user?.name, '- Token obtained:', !!token);

  const headers = { 'Authorization': `JWT ${token}` };

  // === POSTS ===
  console.log('\n========== POSTS ==========');
  const postsData = await page.evaluate(async (h) => {
    const r = await fetch('/api/posts?limit=100&depth=2', { headers: h });
    return await r.json();
  }, headers);
  console.log(`Total posts: ${postsData.totalDocs}`);
  postsData.docs?.forEach((post, i) => {
    const cats = post.categories?.map(c => typeof c === 'string' ? c : c.title).join(', ');
    console.log(`  ${i+1}. "${post.title}" (slug: ${post.slug})`);
    console.log(`     Author: ${post.author}, Date: ${post.date}`);
    console.log(`     Categories: ${cats}`);
    console.log(`     Excerpt: ${post.excerpt?.substring(0, 100)}...`);
    console.log(`     Has content: ${!!post.content}, Content type: ${typeof post.content}`);
    console.log(`     Featured image: ${post.featuredImage || 'none'}`);
  });

  // === CATEGORIES ===
  console.log('\n========== CATEGORIES ==========');
  const catsData = await page.evaluate(async (h) => {
    const r = await fetch('/api/categories?limit=100', { headers: h });
    return await r.json();
  }, headers);
  console.log(`Total categories: ${catsData.totalDocs}`);
  catsData.docs?.forEach((cat, i) => {
    console.log(`  ${i+1}. "${cat.title}" (slug: ${cat.slug})`);
  });

  // === TESTIMONIALS ===
  console.log('\n========== TESTIMONIALS ==========');
  const testData = await page.evaluate(async (h) => {
    const r = await fetch('/api/testimonials?limit=100', { headers: h });
    return await r.json();
  }, headers);
  console.log(`Total testimonials: ${testData.totalDocs}`);
  testData.docs?.forEach((t, i) => {
    console.log(`  ${i+1}. ${t.name} - ${t.role} at ${t.company}`);
    console.log(`     Quote: "${t.quote?.substring(0, 100)}..."`);
    console.log(`     Rating: ${t.rating}`);
  });

  // === FORM SUBMISSIONS ===
  console.log('\n========== FORM SUBMISSIONS ==========');
  const formData = await page.evaluate(async (h) => {
    const r = await fetch('/api/form-submissions?limit=100', { headers: h });
    return await r.json();
  }, headers);
  console.log(`Total form submissions: ${formData.totalDocs}`);
  formData.docs?.forEach((f, i) => {
    console.log(`  ${i+1}. Name: ${f.name}, Email: ${f.email}, Subject: ${f.subject}`);
    console.log(`     Message: "${f.message?.substring(0, 80)}..."`);
    console.log(`     Created: ${f.createdAt}`);
  });

  // === MEDIA ===
  console.log('\n========== MEDIA ==========');
  const mediaData = await page.evaluate(async (h) => {
    const r = await fetch('/api/media?limit=100', { headers: h });
    return await r.json();
  }, headers);
  console.log(`Total media items: ${mediaData.totalDocs}`);
  mediaData.docs?.forEach((m, i) => {
    console.log(`  ${i+1}. Filename: ${m.filename}, URL: ${m.url}, MimeType: ${m.mimeType}`);
  });

  // === USERS ===
  console.log('\n========== USERS ==========');
  const usersData = await page.evaluate(async (h) => {
    const r = await fetch('/api/users?limit=100', { headers: h });
    return await r.json();
  }, headers);
  console.log(`Total users: ${usersData.totalDocs}`);
  usersData.docs?.forEach((u, i) => {
    console.log(`  ${i+1}. ${u.name} (${u.email}), Role: ${u.role}`);
  });

  // === Check first post content structure (rich text) ===
  console.log('\n========== POST CONTENT STRUCTURE ==========');
  if (postsData.docs?.length > 0) {
    const firstPostId = postsData.docs[0].id;
    const postDetail = await page.evaluate(async (args) => {
      const r = await fetch(`/api/posts/${args.id}?depth=2`, { headers: args.h });
      return await r.json();
    }, { id: firstPostId, h: headers });
    console.log('Content field:', JSON.stringify(postDetail.content, null, 2)?.substring(0, 2000));
  }

  await browser.close();
  console.log('\n=== Done ===');
})();
