import { promises as fs } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { randomUUID } from 'crypto';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_DIR = join(__dirname, 'data');
const LINKS_FILE = join(DATA_DIR, 'links.json');

// Promise-based mutex to prevent concurrent file access race conditions
let lockPromise = Promise.resolve();

function withLock(fn) {
  const currentLock = lockPromise;
  let releaseLock;
  lockPromise = new Promise(resolve => { releaseLock = resolve; });
  return currentLock.then(() => fn().finally(releaseLock));
}

/**
 * Generate a unique UUID for a link
 */
export function generateId() {
  return randomUUID();
}

/**
 * Ensure the data directory and links.json file exist
 */
async function ensureDataFile() {
  try {
    await fs.access(DATA_DIR);
  } catch {
    await fs.mkdir(DATA_DIR, { recursive: true });
  }

  try {
    await fs.access(LINKS_FILE);
  } catch {
    await fs.writeFile(LINKS_FILE, JSON.stringify([], null, 2), 'utf-8');
  }
}

/**
 * Read all links from the JSON file (low-level, no locking)
 * @returns {Promise<Array>} Array of link objects
 */
async function readLinksUnsafe() {
  await ensureDataFile();
  const content = await fs.readFile(LINKS_FILE, 'utf-8');

  try {
    const parsed = JSON.parse(content);
    // Validate it's an array
    if (!Array.isArray(parsed)) {
      throw new Error('links.json must contain an array');
    }
    return parsed;
  } catch (parseError) {
    // If JSON is corrupted, log error with file content for debugging
    console.error('Corrupted links.json detected, resetting to empty array:', parseError);
    console.error('File content length:', content.length, 'bytes');
    console.error('First 200 chars:', content.substring(0, 200));
    console.error('Last 200 chars:', content.substring(Math.max(0, content.length - 200)));

    // Reset to empty array using atomic write (caller must hold lock)
    await writeLinks([]);
    return [];
  }
}

/**
 * Read all links from the JSON file (public API)
 * @returns {Promise<Array>} Array of link objects
 */
export async function readLinks() {
  // For read-only operations, no lock needed
  return readLinksUnsafe();
}

/**
 * Write links to the JSON file with retry logic for Windows EPERM errors
 * @param {Array} links - Array of link objects to save
 */
export async function writeLinks(links) {
  await ensureDataFile();
  const content = JSON.stringify(links, null, 2);

  // Atomic write: write to temp file, then rename
  // This prevents corruption if the process crashes mid-write
  const tempFile = `${LINKS_FILE}.tmp`;
  await fs.writeFile(tempFile, content, 'utf-8');

  // Retry fs.rename on Windows EPERM errors (antivirus/indexing file locks)
  let retries = 3;
  let delay = 10; // ms

  while (retries > 0) {
    try {
      await fs.rename(tempFile, LINKS_FILE);
      return; // Success
    } catch (error) {
      if (error.code === 'EPERM' && retries > 1) {
        // Windows file lock - wait and retry
        await new Promise(resolve => setTimeout(resolve, delay));
        delay *= 2; // Exponential backoff
        retries--;
      } else {
        // Different error or out of retries - throw
        throw error;
      }
    }
  }
}

/**
 * Add a new link (serialized with mutex to prevent race conditions)
 * @param {Object} link - Link object to add
 * @returns {Promise<Array>} Updated links array
 */
export async function addLink(link) {
  return withLock(async () => {
    const links = await readLinksUnsafe();
    links.push(link);
    await writeLinks(links);
    return links;
  });
}

/**
 * Remove a link by ID (serialized with mutex to prevent race conditions)
 * @param {string} id - Link ID to remove
 * @returns {Promise<boolean>} True if link was found and removed, false otherwise
 */
export async function removeLink(id) {
  return withLock(async () => {
    const links = await readLinksUnsafe();
    const index = links.findIndex(l => l.id === id);
    if (index === -1) return false;
    links.splice(index, 1);
    await writeLinks(links);
    return true;
  });
}
