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
 * Creates the styles array for Portable Text configuration
 * @param includeH4 - Whether to include H4 heading option
 * @returns Array of style definitions
 */
function createStyles(includeH4: boolean) {
  return [
    { title: 'Normal', value: 'normal' },
    { title: 'H2', value: 'h2' },
    { title: 'H3', value: 'h3' },
    ...(includeH4 ? [{ title: 'H4', value: 'h4' }] : []),
    { title: 'Quote', value: 'blockquote' },
  ]
}

/**
 * Creates the decorators array for Portable Text marks
 * @param includeCode - Whether to include inline code decorator
 * @returns Array of decorator definitions
 */
function createDecorators(includeCode: boolean) {
  return [
    { title: 'Strong', value: 'strong' },
    { title: 'Emphasis', value: 'em' },
    ...(includeCode ? [{ title: 'Code', value: 'code' }] : []),
    { title: 'Underline', value: 'underline' },
  ]
}

/**
 * Creates the link annotation fields
 * @param includeLinkBlank - Whether to include "open in new tab" option
 * @returns Array of link field definitions
 */
function createLinkFields(includeLinkBlank: boolean) {
  return [
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
}

/**
 * Creates a Portable Text block configuration with optional features
 * @param options - Configuration options for extended features
 * @returns Portable Text block definition
 */
export function createPortableTextBlock(options: PortableTextOptions = {}) {
  const { includeH4 = false, includeCode = false, includeLinkBlank = false } = options

  return {
    type: 'block' as const,
    styles: createStyles(includeH4),
    lists: [
      { title: 'Bullet', value: 'bullet' },
      { title: 'Numbered', value: 'number' },
    ],
    marks: {
      decorators: createDecorators(includeCode),
      annotations: [
        {
          name: 'link',
          type: 'object',
          title: 'Link',
          fields: createLinkFields(includeLinkBlank),
        },
      ],
    },
  }
}
