import { defineField } from 'sanity'

/**
 * Reusable field definitions for common schema patterns.
 * Eliminates code duplication across schema files.
 */

/**
 * Standard required field validation.
 * Use this helper to ensure consistent required field validation across all schemas.
 */
export const requiredValidation = (Rule: any) => Rule.required()

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

/**
 * Standard image field with hotspot and alt text.
 * Use this helper for consistent image field configuration across schemas.
 * @param name - Field name (e.g., 'image', 'logo', 'featuredImage')
 * @param title - Field title displayed in Sanity Studio
 * @param description - Field description/help text
 * @param altDescription - Optional custom description for the alt text field
 * @returns Complete image field definition with hotspot and alt text
 */
export const imageFieldWithAlt = (
  name: string,
  title: string,
  description?: string,
  altDescription?: string
) =>
  defineField({
    name,
    title,
    type: 'image',
    description,
    options: {
      hotspot: true,
    },
    fields: [altTextField(altDescription)],
  })

/**
 * Standard preview configuration for documents with title and description.
 * Use this helper for consistent preview display across schemas.
 * @returns Preview object with title and description selection
 */
export const titleDescriptionPreview = () => ({
  select: {
    title: 'title',
    subtitle: 'description',
  },
})
