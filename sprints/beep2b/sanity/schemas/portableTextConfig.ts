import { defineField } from 'sanity'

/**
 * Shared Portable Text block configuration factory
 * Provides consistent rich text editing across schemas with optional extensions
 */

export interface PortableTextOptions {
  includeH4?: boolean
  includeCode?: boolean
  includeLinkBlank?: boolean
}

/**
 * Creates a Portable Text block configuration with optional features
 * @param options - Configuration options for extended features
 * @returns Portable Text block definition
 */
export function createPortableTextBlock(options: PortableTextOptions = {}) {
  const { includeH4 = false, includeCode = false, includeLinkBlank = false } = options

  const styles = [
    { title: 'Normal', value: 'normal' },
    { title: 'H2', value: 'h2' },
    { title: 'H3', value: 'h3' },
    ...(includeH4 ? [{ title: 'H4', value: 'h4' }] : []),
    { title: 'Quote', value: 'blockquote' },
  ]

  const decorators = [
    { title: 'Strong', value: 'strong' },
    { title: 'Emphasis', value: 'em' },
    ...(includeCode ? [{ title: 'Code', value: 'code' }] : []),
    { title: 'Underline', value: 'underline' },
  ]

  const linkFields = [
    {
      name: 'href',
      type: 'url',
      title: 'URL',
      validation: (Rule: any) =>
        Rule.uri({ scheme: ['http', 'https', 'mailto'] }),
    },
    ...(includeLinkBlank
      ? [
          {
            name: 'blank',
            type: 'boolean',
            title: 'Open in new tab',
          },
        ]
      : []),
  ]

  return {
    type: 'block' as const,
    styles,
    lists: [
      { title: 'Bullet', value: 'bullet' },
      { title: 'Numbered', value: 'number' },
    ],
    marks: {
      decorators,
      annotations: [
        {
          name: 'link',
          type: 'object',
          title: 'Link',
          fields: linkFields,
        },
      ],
    },
  }
}
