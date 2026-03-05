/**
 * Pixabay image fetcher with local caching
 * API Key: 54899839-52cb07e8d7437ca93ecb74181
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PIXABAY_API_KEY = '54899839-52cb07e8d7437ca93ecb74181';
const PIXABAY_API_URL = 'https://pixabay.com/api/';
const IMAGE_CACHE_DIR = path.join(__dirname, '../../public/images');

interface PixabayImage {
  id: number;
  pageURL: string;
  type: string;
  tags: string;
  previewURL: string;
  webformatURL: string;
  largeImageURL: string;
  imageWidth: number;
  imageHeight: number;
}

interface PixabayResponse {
  total: number;
  totalHits: number;
  hits: PixabayImage[];
}

/**
 * Fetch an image from Pixabay API
 */
export async function fetchPixabayImage(
  query: string,
  orientation: 'horizontal' | 'vertical' = 'horizontal'
): Promise<string | null> {
  try {
    // Create cache directory if it doesn't exist
    if (!fs.existsSync(IMAGE_CACHE_DIR)) {
      fs.mkdirSync(IMAGE_CACHE_DIR, { recursive: true });
    }

    // Generate filename from query
    const filename = `${query.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.jpg`;
    const cachedPath = path.join(IMAGE_CACHE_DIR, filename);
    const publicPath = `/images/${filename}`;

    // Check if image is already cached
    if (fs.existsSync(cachedPath)) {
      console.log(`Using cached image: ${publicPath}`);
      return publicPath;
    }

    // Fetch from Pixabay API
    const url = new URL(PIXABAY_API_URL);
    url.searchParams.append('key', PIXABAY_API_KEY);
    url.searchParams.append('q', query);
    url.searchParams.append('image_type', 'photo');
    url.searchParams.append('orientation', orientation);
    url.searchParams.append('per_page', '3');
    url.searchParams.append('safesearch', 'true');

    console.log(`Fetching from Pixabay: ${query}`);
    const response = await fetch(url.toString());

    if (!response.ok) {
      throw new Error(`Pixabay API error: ${response.status}`);
    }

    const data: PixabayResponse = await response.json();

    if (data.hits.length === 0) {
      console.warn(`No images found for query: ${query}`);
      return null;
    }

    // Download the first high-quality image
    const imageUrl = data.hits[0].largeImageURL;
    const imageResponse = await fetch(imageUrl);

    if (!imageResponse.ok) {
      throw new Error(`Failed to download image: ${imageResponse.status}`);
    }

    const arrayBuffer = await imageResponse.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // Save to cache
    fs.writeFileSync(cachedPath, buffer);
    console.log(`Cached image: ${publicPath}`);

    return publicPath;
  } catch (error) {
    console.error(`Error fetching Pixabay image for "${query}":`, error);
    return null;
  }
}

/**
 * Pre-fetch and cache multiple images
 */
export async function prefetchImages(queries: string[]): Promise<void> {
  console.log('Pre-fetching background images from Pixabay...');

  for (const query of queries) {
    await fetchPixabayImage(query);
  }

  console.log('Image pre-fetch complete!');
}

/**
 * Get image URL with fallback to gradient
 */
export function getImageUrl(query: string, fallbackGradient: string): string {
  const filename = `${query.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.jpg`;
  const imagePath = path.join(IMAGE_CACHE_DIR, filename);

  if (fs.existsSync(imagePath)) {
    return `/images/${filename}`;
  }

  // Return CSS gradient as fallback
  return fallbackGradient;
}

// Export default queries for common backgrounds
export const DEFAULT_BACKGROUNDS = [
  'business office dark',
  'technology abstract',
  'networking professional',
  'digital marketing',
];
