import { defineField, defineType } from 'sanity'

export default defineType({
  name: 'navigation',
  title: 'Navigation',
  type: 'document',
  fields: [
    defineField({
      name: 'items',
      title: 'Navigation Items',
      type: 'array',
      description: 'Main navigation menu items',
      of: [
        {
          type: 'object',
          name: 'navItem',
          title: 'Navigation Item',
          fields: [
            defineField({
              name: 'label',
              title: 'Label',
              type: 'string',
              description: 'Display text for the menu item',
              validation: (Rule) => Rule.required(),
            }),
            defineField({
              name: 'href',
              title: 'Link',
              type: 'string',
              description: 'URL or path (e.g., /about or https://external.com)',
              validation: (Rule) => Rule.required(),
            }),
            defineField({
              name: 'children',
              title: 'Sub-items',
              type: 'array',
              description: 'Optional nested menu items (dropdown)',
              of: [
                {
                  type: 'object',
                  name: 'navSubItem',
                  title: 'Sub-item',
                  fields: [
                    defineField({
                      name: 'label',
                      title: 'Label',
                      type: 'string',
                      validation: (Rule) => Rule.required(),
                    }),
                    defineField({
                      name: 'href',
                      title: 'Link',
                      type: 'string',
                      validation: (Rule) => Rule.required(),
                    }),
                  ],
                  preview: {
                    select: {
                      title: 'label',
                      subtitle: 'href',
                    },
                  },
                },
              ],
            }),
          ],
          preview: {
            select: {
              title: 'label',
              subtitle: 'href',
            },
          },
        },
      ],
      validation: (Rule) => Rule.required(),
    }),
  ],
  preview: {
    select: {
      items: 'items',
    },
    prepare({ items }) {
      const count = items?.length || 0
      return {
        title: 'Main Navigation',
        subtitle: `${count} top-level item${count !== 1 ? 's' : ''}`,
      }
    },
  },
})
