import type { Payload } from "payload";

export async function seed(payload: Payload) {
  // Check if data already exists
  const existingCategories = await payload.find({
    collection: "categories",
    limit: 1,
  });

  if (existingCategories.docs.length > 0) {
    payload.logger.info("Database already seeded, skipping...");
    return;
  }

  payload.logger.info("Seeding database...");

  // Create admin user
  try {
    await payload.create({
      collection: "users",
      data: {
        email: "admin@beep2b.com",
        password: "changeme",
        name: "Admin User",
      },
    });
    payload.logger.info("✓ Created admin user (admin@beep2b.com / changeme)");
  } catch (error) {
    payload.logger.info("Admin user may already exist");
  }

  // Seed categories (9 from PRD)
  const categories = [
    "Authority Marketing",
    "B2B",
    "LinkedIn Marketing",
    "LinkedIn Profile",
    "LinkedIn Tips",
    "LinkedIn Training",
    "Relationship Selling",
    "Social Selling",
    "Thought Leadership",
  ];

  const createdCategories = [];
  for (const title of categories) {
    const category = await payload.create({
      collection: "categories",
      data: {
        title,
        slug: title.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
      },
    });
    createdCategories.push(category);
  }
  payload.logger.info(`✓ Created ${categories.length} categories`);

  // Seed testimonials (3 from PRD with full copy and star ratings)
  const testimonials = [
    {
      name: "Sarah M.",
      company: "B2B SaaS",
      role: "Founder",
      quote:
        "Within 3 months of implementing BEEP, I was having 4 to 5 qualified discovery calls a week.",
      rating: 5,
    },
    {
      name: "James K.",
      company: "Enterprise Software",
      role: "Sales Director",
      quote:
        "The methodology is so systematic. I knew exactly what to do every day, and the results were predictable.",
      rating: 5,
    },
    {
      name: "Anja W.",
      company: "Marketing Agency",
      role: "VP Marketing",
      quote:
        "We trained our whole team. Within 6 weeks, 3 reps had LinkedIn as their top lead source.",
      rating: 5,
    },
  ];

  for (const testimonial of testimonials) {
    await payload.create({
      collection: "testimonials",
      data: testimonial,
    });
  }
  payload.logger.info(`✓ Created ${testimonials.length} testimonials`);

  // Create placeholder media entries for featured images
  // In a real scenario, you would upload actual images
  // For now, we'll create media records that reference the cached Pixabay images
  const mediaImages = [
    {
      alt: "LinkedIn Marketing Strategy",
      filename: "linkedin-marketing.jpg",
      mimeType: "image/jpeg",
      filesize: 150000,
      width: 1200,
      height: 675,
      url: "/images/technology-abstract.jpg",
    },
    {
      alt: "Professional Networking",
      filename: "professional-networking.jpg",
      mimeType: "image/jpeg",
      filesize: 150000,
      width: 1200,
      height: 675,
      url: "/images/networking-professional.jpg",
    },
    {
      alt: "LinkedIn Profile Optimization",
      filename: "linkedin-profile.jpg",
      mimeType: "image/jpeg",
      filesize: 150000,
      width: 1200,
      height: 675,
      url: "/images/digital-marketing.jpg",
    },
  ];

  const createdMedia = [];
  for (const media of mediaImages) {
    try {
      const mediaDoc = await payload.create({
        collection: "media",
        data: media,
      });
      createdMedia.push(mediaDoc);
    } catch (error) {
      payload.logger.warn(`Could not create media: ${error}`);
    }
  }
  payload.logger.info(`✓ Created ${createdMedia.length} media assets`);

  // Seed sample blog posts (3 with realistic B2B/LinkedIn content)
  const posts = [
    {
      title: "Why Most LinkedIn Outreach Fails And How to Fix It",
      author: "Beep2B Team",
      date: new Date("2026-02-15").toISOString(),
      categories: [
        createdCategories.find((c) => c.title === "LinkedIn Marketing")?.id,
        createdCategories.find((c) => c.title === "B2B")?.id,
      ],
      featuredImage: createdMedia[0]?.id,
      excerpt:
        "The average LinkedIn connection request has a 40% acceptance rate, but only 2% lead to conversations. Learn why most outreach falls flat and the four critical fixes that triple your response rate.",
      content: {
        root: {
          type: "root",
          children: [
            {
              type: "paragraph",
              children: [
                {
                  type: "text",
                  text: "After analyzing over 50,000 LinkedIn outreach messages, we discovered something surprising: the problem is not what most people think.",
                },
              ],
            },
            {
              type: "heading",
              tag: "h2",
              children: [
                {
                  type: "text",
                  text: "The Four Fatal Flaws",
                },
              ],
            },
            {
              type: "paragraph",
              children: [
                {
                  type: "text",
                  text: "Generic connection requests that could be sent to anyone. Immediate sales pitches before building trust. Asking for meetings without providing value first. No systematic follow-up process.",
                },
              ],
            },
            {
              type: "heading",
              tag: "h2",
              children: [
                {
                  type: "text",
                  text: "The BEEP Alternative",
                },
              ],
            },
            {
              type: "paragraph",
              children: [
                {
                  type: "text",
                  text: "Our BEEP methodology flips this script. Instead of pitching immediately, we Build genuine connections, Engage in meaningful conversations, Educate through valuable content, and only then Promote our services to a warmed audience.",
                },
              ],
            },
          ],
          direction: "ltr",
          format: "",
          indent: 0,
          version: 1,
        },
      },
    },
    {
      title: "How to Build Authority on LinkedIn in 90 Days",
      author: "Beep2B Team",
      date: new Date("2026-02-01").toISOString(),
      categories: [
        createdCategories.find((c) => c.title === "Thought Leadership")?.id,
        createdCategories.find((c) => c.title === "Authority Marketing")?.id,
      ],
      featuredImage: createdMedia[1]?.id,
      excerpt:
        "Thought leadership is not about going viral. It is about consistent, strategic content that positions you as the go-to expert in your niche. Here is our proven 90-day playbook.",
      content: {
        root: {
          type: "root",
          children: [
            {
              type: "paragraph",
              children: [
                {
                  type: "text",
                  text: "Most B2B professionals approach LinkedIn content with the wrong mindset. They chase likes and viral posts when they should be building credibility.",
                },
              ],
            },
            {
              type: "heading",
              tag: "h2",
              children: [
                {
                  type: "text",
                  text: "The 90-Day Authority Blueprint",
                },
              ],
            },
            {
              type: "paragraph",
              children: [
                {
                  type: "text",
                  text: "Days 1-30: Define your niche and publish 3 times per week on your core expertise. Days 31-60: Engage deeply with your target audience content. Comment thoughtfully on 10 posts daily. Days 61-90: Launch a LinkedIn newsletter and invite your warmed network to subscribe.",
                },
              ],
            },
          ],
          direction: "ltr",
          format: "",
          indent: 0,
          version: 1,
        },
      },
    },
    {
      title: "The Anatomy of a High-Converting LinkedIn Profile",
      author: "Beep2B Team",
      date: new Date("2026-01-15").toISOString(),
      categories: [
        createdCategories.find((c) => c.title === "LinkedIn Profile")?.id,
        createdCategories.find((c) => c.title === "LinkedIn Tips")?.id,
      ],
      featuredImage: createdMedia[2]?.id,
      excerpt:
        "Your LinkedIn profile is your digital storefront. These seven elements turn browsers into buyers and connection requests into qualified leads.",
      content: {
        root: {
          type: "root",
          children: [
            {
              type: "paragraph",
              children: [
                {
                  type: "text",
                  text: "Before anyone accepts your connection request, they check your profile. Here is what they need to see in the first 5 seconds.",
                },
              ],
            },
            {
              type: "heading",
              tag: "h2",
              children: [
                {
                  type: "text",
                  text: "The 7 Essential Elements",
                },
              ],
            },
            {
              type: "paragraph",
              children: [
                {
                  type: "text",
                  text: "A professional headshot because profiles with photos get 14x more views. A headline that speaks to your buyer pain point, not your job title. A banner image that reinforces your value proposition. An About section that tells a story, not a resume. Featured content showcasing your best work. Recommendations from clients in your target market. A clear call-to-action in your contact info.",
                },
              ],
            },
          ],
          direction: "ltr",
          format: "",
          indent: 0,
          version: 1,
        },
      },
    },
  ];

  for (const post of posts) {
    await payload.create({
      collection: "posts",
      data: post,
    });
  }
  payload.logger.info(`✓ Created ${posts.length} sample blog posts`);

  payload.logger.info("✅ Database seeding complete!");
}
