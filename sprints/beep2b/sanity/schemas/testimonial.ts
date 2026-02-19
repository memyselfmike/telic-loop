import { defineField, defineType } from 'sanity'
import { imageFieldWithAlt } from './fieldHelpers'

export default defineType({
  name: 'testimonial',
  title: 'Testimonial',
  type: 'document',
  fields: [
    defineField({
      name: 'name',
      title: 'Name',
      type: 'string',
      description: "Person's name",
      validation: (Rule) => Rule.required(),
    }),
    defineField({
      name: 'company',
      title: 'Company',
      type: 'string',
      description: 'Company name',
    }),
    defineField({
      name: 'role',
      title: 'Role',
      type: 'string',
      description: 'Job title',
    }),
    defineField({
      name: 'quote',
      title: 'Quote',
      type: 'text',
      rows: 4,
      description: 'Testimonial text',
      validation: (Rule) => Rule.required(),
    }),
    imageFieldWithAlt('image', 'Image', 'Headshot'),
  ],
  preview: {
    select: {
      title: 'name',
      subtitle: 'company',
      media: 'image',
    },
    prepare({ title, subtitle, media }) {
      return {
        title,
        subtitle: subtitle || 'No company',
        media,
      }
    },
  },
})
