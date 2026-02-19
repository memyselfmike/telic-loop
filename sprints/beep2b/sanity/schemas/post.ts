import { defineField, defineType } from 'sanity'
import { altTextField, requiredValidation, slugField } from './fieldHelpers'
import { createPortableTextBlock } from './portableTextConfig'

export default defineType({
  name: 'post',
  title: 'Blog Post',
  type: 'document',
  fields: [
    defineField({
      name: 'title',
      title: 'Title',
      type: 'string',
      validation: requiredValidation,
    }),
    slugField('title', 'URL slug for this post — used in /blog/[slug]'),
    defineField({
      name: 'author',
      title: 'Author',
      type: 'reference',
      to: [{ type: 'author' }],
      validation: requiredValidation,
    }),
    defineField({
      name: 'publishedAt',
      title: 'Published At',
      type: 'datetime',
      description: 'Publication date and time',
      validation: requiredValidation,
    }),
    defineField({
      name: 'categories',
      title: 'Categories',
      type: 'array',
      of: [
        {
          type: 'reference',
          to: [{ type: 'category' }],
        },
      ],
      validation: (Rule) => Rule.required().min(1),
    }),
    defineField({
      name: 'featuredImage',
      title: 'Featured Image',
      type: 'image',
      options: {
        hotspot: true,
      },
      fields: [altTextField()],
    }),
    defineField({
      name: 'excerpt',
      title: 'Excerpt',
      type: 'text',
      rows: 3,
      description: 'Short summary shown on blog listing cards (max 200 characters)',
      validation: (Rule) => Rule.max(200),
    }),
    defineField({
      name: 'body',
      title: 'Body',
      type: 'array',
      of: [
        createPortableTextBlock({
          includeH4: true,
          includeCode: true,
          includeLinkBlank: true,
        }),
        {
          type: 'image',
          options: { hotspot: true },
          fields: [
            altTextField(),
            {
              name: 'caption',
              type: 'string',
              title: 'Caption',
            },
          ],
        },
      ],
      validation: requiredValidation,
    }),
  ],
  preview: {
    select: {
      title: 'title',
      author: 'author.name',
      media: 'featuredImage',
      date: 'publishedAt',
    },
    prepare({ title, author, media, date }) {
      const formattedDate = date
        ? new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })
        : 'No date'
      return {
        title,
        subtitle: author ? `by ${author} · ${formattedDate}` : formattedDate,
        media,
      }
    },
  },
})
