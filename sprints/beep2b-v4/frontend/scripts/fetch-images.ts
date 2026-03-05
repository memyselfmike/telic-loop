/**
 * Script to pre-fetch background images from Pixabay
 * Run this before build or during dev to cache images locally
 */

import { prefetchImages, DEFAULT_BACKGROUNDS } from '../src/lib/pixabay';

async function main() {
  try {
    await prefetchImages(DEFAULT_BACKGROUNDS);
    console.log('✅ All background images fetched and cached successfully!');
    process.exit(0);
  } catch (error) {
    console.error('❌ Error fetching images:', error);
    process.exit(1);
  }
}

main();
