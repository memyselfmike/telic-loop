import type { SchemaTypeDefinition } from 'sanity'

import author from './author'
import category from './category'
import post from './post'
import page from './page'

export const schemaTypes: SchemaTypeDefinition[] = [
  author,
  category,
  post,
  page,
]
