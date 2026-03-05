import { CollectionConfig } from 'payload/types';

export const FormSubmissions: CollectionConfig = {
  slug: 'form-submissions',
  admin: {
    useAsTitle: 'name',
    defaultColumns: ['name', 'email', 'company', 'createdAt'],
    group: 'Content',
  },
  access: {
    read: () => true, // Admin only in production
    create: () => true, // Allow public form submissions
  },
  fields: [
    {
      name: 'name',
      type: 'text',
      required: true,
      label: 'Name',
    },
    {
      name: 'email',
      type: 'email',
      required: true,
      label: 'Email',
    },
    {
      name: 'company',
      type: 'text',
      label: 'Company',
    },
    {
      name: 'message',
      type: 'textarea',
      required: true,
      label: 'Message',
    },
    {
      name: 'status',
      type: 'select',
      defaultValue: 'new',
      options: [
        { label: 'New', value: 'new' },
        { label: 'In Progress', value: 'in-progress' },
        { label: 'Contacted', value: 'contacted' },
        { label: 'Closed', value: 'closed' },
      ],
      admin: {
        description: 'Track the status of this inquiry',
      },
    },
  ],
  timestamps: true,
};
