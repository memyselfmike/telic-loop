import { defineField, defineType } from 'sanity'
import { requiredValidation, slugField } from './fieldHelpers'
import { createPortableTextBlock } from './portableTextConfig'

// Section: Hero
const heroSection = defineField({
  name: 'hero',
  title: 'Hero Section',
  type: 'object',
  fields: [
    defineField({
      name: 'heading',
      title: 'Heading',
      type: 'string',
      validation: requiredValidation,
    }),
    defineField({
      name: 'subheading',
      title: 'Subheading',
      type: 'text',
      rows: 3,
    }),
    defineField({
      name: 'ctaText',
      title: 'CTA Button Text',
      type: 'string',
    }),
    defineField({
      name: 'ctaLink',
      title: 'CTA Button Link',
      type: 'string',
    }),
    defineField({
      name: 'backgroundImage',
      title: 'Background Image',
      type: 'image',
      options: { hotspot: true },
      fields: [
        defineField({
          name: 'alt',
          title: 'Alt Text',
          type: 'string',
        }),
      ],
    }),
  ],
  preview: {
    select: { title: 'heading' },
    prepare({ title }) {
      return { title: `Hero: ${title || 'Untitled'}` }
    },
  },
})

// Helper: Feature Item object definition
const featureItemObject = {
  type: 'object' as const,
  name: 'featureItem',
  title: 'Feature Item',
  fields: [
    defineField({
      name: 'icon',
      title: 'Icon',
      type: 'string',
      description: 'Icon name or emoji (e.g., "chart", "users", "🚀")',
    }),
    defineField({
      name: 'title',
      title: 'Title',
      type: 'string',
      validation: requiredValidation,
    }),
    defineField({
      name: 'description',
      title: 'Description',
      type: 'text',
      rows: 3,
    }),
  ],
  preview: {
    select: { title: 'title', subtitle: 'description' },
  },
}

// Section: Features
const featuresSection = defineField({
  name: 'features',
  title: 'Features Section',
  type: 'object',
  fields: [
    defineField({
      name: 'heading',
      title: 'Section Heading',
      type: 'string',
    }),
    defineField({
      name: 'items',
      title: 'Feature Items',
      type: 'array',
      of: [featureItemObject],
    }),
  ],
  preview: {
    select: { title: 'heading' },
    prepare({ title }) {
      return { title: `Features: ${title || 'Untitled'}` }
    },
  },
})

// Section: Testimonials
const testimonialsSection = defineField({
  name: 'testimonials',
  title: 'Testimonials Section',
  type: 'object',
  fields: [
    defineField({
      name: 'heading',
      title: 'Section Heading',
      type: 'string',
    }),
    defineField({
      name: 'items',
      title: 'Testimonials',
      type: 'array',
      of: [
        {
          type: 'reference',
          to: [{ type: 'testimonial' }],
        },
      ],
    }),
  ],
  preview: {
    select: { title: 'heading' },
    prepare({ title }) {
      return { title: `Testimonials: ${title || 'Untitled'}` }
    },
  },
})

// Helper: Portable Text block configuration
const portableTextBlock = createPortableTextBlock()

// Section: Text Block
const textBlockSection = defineField({
  name: 'textBlock',
  title: 'Text Block Section',
  type: 'object',
  fields: [
    defineField({
      name: 'heading',
      title: 'Heading',
      type: 'string',
    }),
    defineField({
      name: 'body',
      title: 'Body',
      type: 'array',
      of: [portableTextBlock],
    }),
  ],
  preview: {
    select: { title: 'heading' },
    prepare({ title }) {
      return { title: `Text Block: ${title || 'Untitled'}` }
    },
  },
})

// Section: CTA
const ctaSection = defineField({
  name: 'cta',
  title: 'CTA Section',
  type: 'object',
  fields: [
    defineField({
      name: 'heading',
      title: 'Heading',
      type: 'string',
      validation: requiredValidation,
    }),
    defineField({
      name: 'description',
      title: 'Description',
      type: 'text',
      rows: 3,
    }),
    defineField({
      name: 'buttonText',
      title: 'Button Text',
      type: 'string',
    }),
    defineField({
      name: 'buttonLink',
      title: 'Button Link',
      type: 'string',
    }),
  ],
  preview: {
    select: { title: 'heading' },
    prepare({ title }) {
      return { title: `CTA: ${title || 'Untitled'}` }
    },
  },
})

export default defineType({
  name: 'page',
  title: 'Page',
  type: 'document',
  fields: [
    defineField({
      name: 'title',
      title: 'Title',
      type: 'string',
      description: 'Internal page identifier (e.g., "Home", "About")',
      validation: (Rule) => Rule.required(),
    }),
    slugField('title', 'Must match route (e.g., "home", "about", "services")'),
    defineField({
      name: 'sections',
      title: 'Page Sections',
      type: 'array',
      of: [heroSection, featuresSection, testimonialsSection, textBlockSection, ctaSection],
      description: 'Add and reorder page sections to build the page layout',
    }),
  ],
  preview: {
    select: {
      title: 'title',
      slug: 'slug.current',
    },
    prepare({ title, slug }) {
      return {
        title,
        subtitle: slug ? `/${slug}` : 'No slug',
      }
    },
  },
})
