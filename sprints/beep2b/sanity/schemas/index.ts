import type { SchemaTypeDefinition } from 'sanity'

import author from './author'
import category from './category'
import post from './post'
import page from './page'
import testimonial from './testimonial'
import siteSettings from './siteSettings'
import navigation from './navigation'

export const schemaTypes: SchemaTypeDefinition[] = [
  author,
  category,
  post,
  page,
  testimonial,
  siteSettings,
  navigation,
]
