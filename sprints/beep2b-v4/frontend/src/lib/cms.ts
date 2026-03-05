/**
 * CMS API Client
 * Fetches data from Payload CMS REST API
 */

const CMS_URL = import.meta.env.CMS_URL || 'http://cms:3000';

export interface Post {
  id: string;
  title: string;
  slug: string;
  author: string;
  date: string;
  categories: Category[] | string[];
  featuredImage?: Media;
  excerpt: string;
  content: any; // Lexical rich text
  createdAt: string;
  updatedAt: string;
}

export interface Category {
  id: string;
  title: string;
  slug: string;
}

export interface Media {
  id: string;
  alt: string;
  url: string;
  width?: number;
  height?: number;
  sizes?: {
    thumbnail?: { url: string };
    card?: { url: string };
    feature?: { url: string };
  };
}

export interface PaginatedResponse<T> {
  docs: T[];
  totalDocs: number;
  limit: number;
  totalPages: number;
  page: number;
  pagingCounter: number;
  hasPrevPage: boolean;
  hasNextPage: boolean;
  prevPage: number | null;
  nextPage: number | null;
}

/**
 * Fetch posts from CMS with optional filters
 */
export async function getPosts(options: {
  page?: number;
  limit?: number;
  category?: string;
} = {}): Promise<PaginatedResponse<Post> | null> {
  const { page = 1, limit = 10, category } = options;

  try {
    let url = `${CMS_URL}/api/posts?page=${page}&limit=${limit}&depth=2`;

    if (category) {
      url += `&where[categories.slug][equals]=${category}`;
    }

    const response = await fetch(url);

    if (!response.ok) {
      console.error(`Failed to fetch posts: ${response.status} ${response.statusText}`);
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching posts:', error);
    return null;
  }
}

/**
 * Fetch a single post by slug
 */
export async function getPostBySlug(slug: string): Promise<Post | null> {
  try {
    const url = `${CMS_URL}/api/posts?where[slug][equals]=${slug}&depth=2&limit=1`;
    const response = await fetch(url);

    if (!response.ok) {
      console.error(`Failed to fetch post: ${response.status} ${response.statusText}`);
      return null;
    }

    const data: PaginatedResponse<Post> = await response.json();

    if (data.docs.length === 0) {
      return null;
    }

    return data.docs[0];
  } catch (error) {
    console.error('Error fetching post by slug:', error);
    return null;
  }
}

/**
 * Fetch all categories
 */
export async function getCategories(): Promise<Category[]> {
  try {
    const url = `${CMS_URL}/api/categories?limit=100`;
    const response = await fetch(url);

    if (!response.ok) {
      console.error(`Failed to fetch categories: ${response.status} ${response.statusText}`);
      return [];
    }

    const data: PaginatedResponse<Category> = await response.json();
    return data.docs;
  } catch (error) {
    console.error('Error fetching categories:', error);
    return [];
  }
}

/**
 * Get related posts (same category, excluding current post)
 */
export async function getRelatedPosts(
  categoryId: string,
  excludeId: string,
  limit = 3
): Promise<Post[]> {
  try {
    const url = `${CMS_URL}/api/posts?where[categories][in]=${categoryId}&where[id][not_equals]=${excludeId}&limit=${limit}&depth=2`;
    const response = await fetch(url);

    if (!response.ok) {
      console.error(`Failed to fetch related posts: ${response.status} ${response.statusText}`);
      return [];
    }

    const data: PaginatedResponse<Post> = await response.json();
    return data.docs;
  } catch (error) {
    console.error('Error fetching related posts:', error);
    return [];
  }
}

/**
 * Format date for display
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

/**
 * Get full media URL
 */
export function getMediaUrl(media: Media | string | undefined): string | null {
  if (!media) return null;
  if (typeof media === 'string') return media;
  return media.url || null;
}

/**
 * Get responsive image URL from media sizes
 */
export function getResponsiveImageUrl(
  media: Media | undefined,
  size: 'thumbnail' | 'card' | 'feature' = 'card'
): string | null {
  if (!media) return null;
  return media.sizes?.[size]?.url || media.url || null;
}
