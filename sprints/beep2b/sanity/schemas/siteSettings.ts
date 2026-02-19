import { defineField, defineType } from 'sanity'

export default defineType({
  name: 'siteSettings',
  title: 'Site Settings',
  type: 'document',
  fields: [
    defineField({
      name: 'title',
      title: 'Site Title',
      type: 'string',
      description: 'Site title for meta tags',
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'description',
      title: 'Description',
      type: 'text',
      rows: 3,
      description: 'Default meta description',
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'logo',
      title: 'Logo',
      type: 'image',
      description: 'Site logo',
      options: {
        hotspot: true,
      },
      fields: [
        defineField({
          name: 'alt',
          title: 'Alt Text',
          type: 'string',
          description: 'Describe the logo for accessibility',
        }),
      ],
    }),
    defineField({
      name: 'socialLinks',
      title: 'Social Links',
      type: 'object',
      description: 'Social media profile URLs',
      fields: [
        defineField({
          name: 'linkedin',
          title: 'LinkedIn',
          type: 'string',
          description: 'LinkedIn company profile URL',
        }),
        defineField({
          name: 'twitter',
          title: 'Twitter',
          type: 'string',
          description: 'Twitter/X profile URL',
        }),
        defineField({
          name: 'facebook',
          title: 'Facebook',
          type: 'string',
          description: 'Facebook page URL',
        }),
      ],
    }),
    defineField({
      name: 'footerText',
      title: 'Footer Text',
      type: 'text',
      rows: 2,
      description: 'Footer copyright/tagline',
    }),
    defineField({
      name: 'ctaDefaultLink',
      title: 'Default CTA Link',
      type: 'url',
      description: 'Default CTA destination (booking page URL)',
      validation: (Rule) => Rule.uri({ scheme: ['http', 'https'] }),
    }),
  ],
  preview: {
    select: {
      title: 'title',
      subtitle: 'description',
    },
  },
})
