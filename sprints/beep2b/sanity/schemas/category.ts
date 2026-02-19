import { defineField, defineType } from 'sanity'
import { requiredValidation, slugField, titleDescriptionPreview } from './fieldHelpers'

export default defineType({
  name: 'category',
  title: 'Category',
  type: 'document',
  fields: [
    defineField({
      name: 'title',
      title: 'Title',
      type: 'string',
      description: 'Display name for the category',
      validation: requiredValidation,
    }),
    slugField('title', 'URL-safe identifier used in /blog/category/[slug] routes'),
    defineField({
      name: 'description',
      title: 'Description',
      type: 'text',
      rows: 3,
      description: 'Optional description of this category',
    }),
  ],
  preview: titleDescriptionPreview(),
})
