import { createClient } from '@sanity/client'
import imageUrlBuilder from '@sanity/image-url'
import type { SanityImageSource } from '@sanity/image-url/lib/types/types'

// Environment variables with fallbacks for graceful degradation
const projectId = import.meta.env.SANITY_PROJECT_ID || ''
const dataset = import.meta.env.SANITY_DATASET || 'production'
const apiVersion = '2024-01-01' // Use current date for stable API behavior
const token = import.meta.env.SANITY_API_TOKEN || ''

// Lazy client initialization to avoid errors when SANITY_PROJECT_ID is missing
let _client: ReturnType<typeof createClient> | null = null

function getClient() {
  if (!projectId) {
    throw new Error('SANITY_PROJECT_ID is required')
  }
  if (!_client) {
    _client = createClient({
      projectId,
      dataset,
      apiVersion,
      useCdn: true, // Use CDN for fast, cached reads
      token, // Optional - needed for draft content or mutations
      perspective: 'published', // Only fetch published content (not drafts)
    })
  }
  return _client
}

// Export for backwards compatibility (will throw if projectId is missing)
export const client = new Proxy({} as ReturnType<typeof createClient>, {
  get(_target, prop) {
    return (getClient() as any)[prop]
  }
})

// Image URL builder for optimized image URLs
export function urlForImage(source: SanityImageSource) {
  if (!source) return ''
  if (!projectId) return ''
  const builder = imageUrlBuilder(getClient())
  return builder.image(source).url()
}

// TypeScript interfaces for Sanity document types

export interface SanityImage {
  _type: 'image'
  asset: {
    _ref: string
    _type: 'reference'
  }
  alt?: string
  hotspot?: {
    x: number
    y: number
    height: number
    width: number
  }
}

export interface SanitySlug {
  _type: 'slug'
  current: string
}

export interface Author {
  _id: string
  _type: 'author'
  name: string
  slug: SanitySlug
  image?: SanityImage
  bio?: string
}

export interface Category {
  _id: string
  _type: 'category'
  title: string
  slug: SanitySlug
  description?: string
}

export interface Post {
  _id: string
  _type: 'post'
  title: string
  slug: SanitySlug
  author: Author
  publishedAt: string
  categories: Category[]
  featuredImage?: SanityImage
  excerpt?: string
  body: any[] // Portable Text blocks
}

export interface PageSection {
  _type: 'hero' | 'features' | 'testimonials' | 'textBlock' | 'cta'
  _key: string
  [key: string]: any
}

export interface Page {
  _id: string
  _type: 'page'
  title: string
  slug: SanitySlug
  sections?: PageSection[]
}

export interface Testimonial {
  _id: string
  _type: 'testimonial'
  name: string
  company?: string
  role?: string
  quote: string
  image?: SanityImage
}

export interface SiteSettings {
  _id: string
  _type: 'siteSettings'
  title: string
  description: string
  logo?: SanityImage
  socialLinks?: {
    linkedin?: string
    twitter?: string
    facebook?: string
  }
  footerText?: string
  ctaDefaultLink?: string
}

export interface NavigationItem {
  label: string
  href: string
  children?: {
    label: string
    href: string
  }[]
}

export interface Navigation {
  _id: string
  _type: 'navigation'
  items: NavigationItem[]
}

// GROQ Query Helpers

/**
 * Get all published posts with pagination
 * @param start - Starting index (0-based)
 * @param end - Ending index (exclusive)
 * @returns Array of posts with author and category data expanded
 */
export async function getAllPosts(start = 0, end = 10): Promise<Post[]> {
  if (!projectId || !dataset) {
    console.warn('[sanity.ts] Missing SANITY_PROJECT_ID or SANITY_DATASET - returning empty results')
    return []
  }

  try {
    const query = `*[_type == "post"] | order(publishedAt desc) [${start}...${end}] {
      _id,
      _type,
      title,
      slug,
      "author": author->{
        _id,
        _type,
        name,
        slug,
        image,
        bio
      },
      publishedAt,
      "categories": categories[]->{
        _id,
        _type,
        title,
        slug,
        description
      },
      featuredImage,
      excerpt,
      body
    }`

    const posts = await getClient().fetch<Post[]>(query)
    return posts || []
  } catch (error) {
    console.error('[sanity.ts] Error fetching posts:', error)
    return []
  }
}

/**
 * Get total count of published posts
 * @returns Total number of posts
 */
export async function getPostCount(): Promise<number> {
  if (!projectId || !dataset) {
    return 0
  }

  try {
    const query = `count(*[_type == "post"])`
    const count = await getClient().fetch<number>(query)
    return count || 0
  } catch (error) {
    console.error('[sanity.ts] Error fetching post count:', error)
    return 0
  }
}

/**
 * Get a single post by slug
 * @param slug - Post slug
 * @returns Post with expanded author and categories, or null if not found
 */
export async function getPostBySlug(slug: string): Promise<Post | null> {
  if (!projectId || !dataset || !slug) {
    return null
  }

  try {
    const query = `*[_type == "post" && slug.current == $slug][0] {
      _id,
      _type,
      title,
      slug,
      "author": author->{
        _id,
        _type,
        name,
        slug,
        image,
        bio
      },
      publishedAt,
      "categories": categories[]->{
        _id,
        _type,
        title,
        slug,
        description
      },
      featuredImage,
      excerpt,
      body
    }`

    const post = await getClient().fetch<Post | null>(query, { slug })
    return post
  } catch (error) {
    console.error(`[sanity.ts] Error fetching post by slug "${slug}":`, error)
    return null
  }
}

/**
 * Get posts filtered by category slug
 * @param categorySlug - Category slug to filter by
 * @param start - Starting index (0-based)
 * @param end - Ending index (exclusive)
 * @returns Array of posts in that category
 */
export async function getPostsByCategory(
  categorySlug: string,
  start = 0,
  end = 10
): Promise<Post[]> {
  if (!projectId || !dataset || !categorySlug) {
    return []
  }

  try {
    const query = `*[_type == "post" && $categorySlug in categories[]->slug.current] | order(publishedAt desc) [${start}...${end}] {
      _id,
      _type,
      title,
      slug,
      "author": author->{
        _id,
        _type,
        name,
        slug,
        image,
        bio
      },
      publishedAt,
      "categories": categories[]->{
        _id,
        _type,
        title,
        slug,
        description
      },
      featuredImage,
      excerpt,
      body
    }`

    const posts = await getClient().fetch<Post[]>(query, { categorySlug })
    return posts || []
  } catch (error) {
    console.error(`[sanity.ts] Error fetching posts by category "${categorySlug}":`, error)
    return []
  }
}

/**
 * Get all unique categories used by published posts
 * @returns Array of categories
 */
export async function getAllCategories(): Promise<Category[]> {
  if (!projectId || !dataset) {
    return []
  }

  try {
    const query = `*[_type == "category"] | order(title asc) {
      _id,
      _type,
      title,
      slug,
      description
    }`

    const categories = await getClient().fetch<Category[]>(query)
    return categories || []
  } catch (error) {
    console.error('[sanity.ts] Error fetching categories:', error)
    return []
  }
}

/**
 * Get a page by slug
 * @param slug - Page slug
 * @returns Page with sections, or null if not found
 */
export async function getPageBySlug(slug: string): Promise<Page | null> {
  if (!projectId || !dataset || !slug) {
    return null
  }

  try {
    const query = `*[_type == "page" && slug.current == $slug][0] {
      _id,
      _type,
      title,
      slug,
      sections[] {
        _type,
        _key,
        ...,
        _type == "testimonials" => {
          "items": items[]->{
            _id,
            _type,
            name,
            company,
            role,
            quote,
            image
          }
        }
      }
    }`

    const page = await getClient().fetch<Page | null>(query, { slug })
    return page
  } catch (error) {
    console.error(`[sanity.ts] Error fetching page by slug "${slug}":`, error)
    return null
  }
}

/**
 * Get global site settings
 * @returns Site settings singleton document, or null if not found
 */
export async function getSiteSettings(): Promise<SiteSettings | null> {
  if (!projectId || !dataset) {
    return null
  }

  try {
    const query = `*[_type == "siteSettings"][0] {
      _id,
      _type,
      title,
      description,
      logo,
      socialLinks,
      footerText,
      ctaDefaultLink
    }`

    const settings = await getClient().fetch<SiteSettings | null>(query)
    return settings
  } catch (error) {
    console.error('[sanity.ts] Error fetching site settings:', error)
    return null
  }
}

/**
 * Get main navigation menu
 * @returns Navigation singleton document, or null if not found
 */
export async function getNavigation(): Promise<Navigation | null> {
  if (!projectId || !dataset) {
    return null
  }

  try {
    const query = `*[_type == "navigation"][0] {
      _id,
      _type,
      items
    }`

    const navigation = await getClient().fetch<Navigation | null>(query)
    return navigation
  } catch (error) {
    console.error('[sanity.ts] Error fetching navigation:', error)
    return null
  }
}

/**
 * Get related posts by matching categories (for "related posts" sections)
 * @param currentPostId - ID of the current post to exclude
 * @param categoryIds - Array of category IDs to match
 * @param limit - Maximum number of related posts to return
 * @returns Array of related posts
 */
export async function getRelatedPosts(
  currentPostId: string,
  categoryIds: string[],
  limit = 3
): Promise<Post[]> {
  if (!projectId || !dataset || !currentPostId || !categoryIds?.length) {
    return []
  }

  try {
    const query = `*[
      _type == "post"
      && _id != $currentPostId
      && count((categories[]._ref)[@ in $categoryIds]) > 0
    ] | order(publishedAt desc) [0...${limit}] {
      _id,
      _type,
      title,
      slug,
      "author": author->{
        _id,
        _type,
        name,
        slug
      },
      publishedAt,
      "categories": categories[]->{
        _id,
        _type,
        title,
        slug
      },
      featuredImage,
      excerpt
    }`

    const posts = await getClient().fetch<Post[]>(query, { currentPostId, categoryIds })
    return posts || []
  } catch (error) {
    console.error('[sanity.ts] Error fetching related posts:', error)
    return []
  }
}
