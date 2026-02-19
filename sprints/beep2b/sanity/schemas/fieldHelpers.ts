import { defineField } from 'sanity'

/**
 * Reusable field definitions for common schema patterns.
 * Eliminates code duplication across schema files.
 */

/**
 * Standard alt text field for images.
 * Use within image field's `fields` array for accessibility compliance.
 * @param description - Optional custom description (defaults to standard SEO/accessibility text)
 */
export const altTextField = (description?: string) =>
  defineField({
    name: 'alt',
    title: 'Alt Text',
    type: 'string',
    description: description || 'Describe the image for accessibility and SEO',
  })

/**
 * Standard slug field for documents.
 * Generates URL-friendly slugs from a source field.
 * @param source - The field name to generate the slug from (e.g., 'title', 'name')
 * @param description - Optional custom description
 */
export const slugField = (source: string, description?: string) =>
  defineField({
    name: 'slug',
    title: 'Slug',
    type: 'slug',
    options: {
      source,
      maxLength: 96,
    },
    description,
    validation: (Rule) => Rule.required(),
  })
