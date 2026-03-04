const MEILI_HOST = process.env.MEILI_HOST || 'http://localhost:7700';
const MEILI_KEY = process.env.MEILI_KEY || '';

const INDEX_NAME = 'books';

// Initialize MeiliSearch index with retry logic
async function init() {
  const maxAttempts = 10;
  const delayMs = 2000;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      console.log(`[MeiliSearch] Initialization attempt ${attempt}/${maxAttempts}...`);

      // Check MeiliSearch health
      const healthResponse = await fetch(`${MEILI_HOST}/health`);
      if (!healthResponse.ok) {
        throw new Error(`MeiliSearch not healthy: ${healthResponse.status}`);
      }

      // Configure index settings
      const settingsUrl = `${MEILI_HOST}/indexes/${INDEX_NAME}/settings`;
      const settingsResponse = await fetch(settingsUrl, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${MEILI_KEY}`
        },
        body: JSON.stringify({
          searchableAttributes: ['title', 'author', 'genre', 'notes'],
          filterableAttributes: ['status', 'genre', 'rating'],
          sortableAttributes: ['date_added']
        })
      });

      if (!settingsResponse.ok) {
        const errorText = await settingsResponse.text();
        throw new Error(`Failed to configure index: ${settingsResponse.status} ${errorText}`);
      }

      console.log(`[MeiliSearch] Index "${INDEX_NAME}" configured successfully`);
      return;
    } catch (error) {
      console.error(`[MeiliSearch] Attempt ${attempt} failed:`, error.message);

      if (attempt < maxAttempts) {
        console.log(`[MeiliSearch] Retrying in ${delayMs}ms...`);
        await new Promise(resolve => setTimeout(resolve, delayMs));
      } else {
        console.error(`[MeiliSearch] Failed to initialize after ${maxAttempts} attempts`);
        throw new Error('MeiliSearch initialization failed');
      }
    }
  }
}

// Add or update a document in the search index
async function addOrUpdate(book) {
  try {
    const documentsUrl = `${MEILI_HOST}/indexes/${INDEX_NAME}/documents`;
    const response = await fetch(documentsUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${MEILI_KEY}`
      },
      body: JSON.stringify([book])
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[MeiliSearch] Failed to add/update document:`, errorText);
    }
  } catch (error) {
    console.error('[MeiliSearch] Error in addOrUpdate:', error);
  }
}

// Remove a document from the search index
async function remove(id) {
  try {
    const documentUrl = `${MEILI_HOST}/indexes/${INDEX_NAME}/documents/${id}`;
    const response = await fetch(documentUrl, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${MEILI_KEY}`
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[MeiliSearch] Failed to remove document:`, errorText);
    }
  } catch (error) {
    console.error('[MeiliSearch] Error in remove:', error);
  }
}

// Search for books
async function search(query) {
  try {
    const searchUrl = `${MEILI_HOST}/indexes/${INDEX_NAME}/search`;
    const response = await fetch(searchUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${MEILI_KEY}`
      },
      body: JSON.stringify({ q: query, limit: 100 })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[MeiliSearch] Search failed:`, errorText);
      return [];
    }

    const result = await response.json();
    return result.hits || [];
  } catch (error) {
    console.error('[MeiliSearch] Error in search:', error);
    return [];
  }
}

module.exports = {
  init,
  addOrUpdate,
  remove,
  search
};
