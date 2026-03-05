import { buildConfig } from 'payload'
import { mongooseAdapter } from '@payloadcms/db-mongodb'
import { lexicalEditor } from '@payloadcms/richtext-lexical'
import path from 'path'
import { fileURLToPath } from 'url'

import { Users } from './collections/Users'
import { Posts } from './collections/Posts'
import { Categories } from './collections/Categories'
import { Testimonials } from './collections/Testimonials'
import { Media } from './collections/Media'
import { FormSubmissions } from './collections/FormSubmissions'
import { seed } from './seed'

const filename = fileURLToPath(import.meta.url)
const dirname = path.dirname(filename)

export default buildConfig({
  secret: process.env.PAYLOAD_SECRET || 'your-secret-key-change-in-production',
  admin: {
    user: Users.slug,
    meta: {
      titleSuffix: '- Beep2B CMS',
      favicon: '/favicon.ico',
      ogImage: '/og-image.jpg',
    },
  },
  collections: [Users, Posts, Categories, Testimonials, Media, FormSubmissions],
  editor: lexicalEditor({}),
  db: mongooseAdapter({
    url: process.env.MONGODB_URI || 'mongodb://localhost:27017/beep2b',
  }),
  cors: process.env.NODE_ENV === 'production'
    ? ['https://beep2b.com', 'https://www.beep2b.com']
    : ['http://localhost:4321', 'http://localhost:3000'],
  csrf: process.env.NODE_ENV === 'production'
    ? ['https://beep2b.com', 'https://www.beep2b.com']
    : ['http://localhost:4321', 'http://localhost:3000'],
  typescript: {
    outputFile: path.resolve(dirname, 'payload-types.ts'),
  },
  graphQL: {
    schemaOutputFile: path.resolve(dirname, 'generated-schema.graphql'),
  },
  onInit: async (payload) => {
    await seed(payload)
  },
})
