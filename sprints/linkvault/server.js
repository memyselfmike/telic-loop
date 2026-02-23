import express from 'express';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { readLinks, addLink, removeLink, generateId } from './storage.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = 3000;

app.use(express.json());
app.use(express.static(join(__dirname, 'public')));

// Explicit route for dashboard page
app.get('/dashboard', (req, res) => {
  res.sendFile(join(__dirname, 'public', 'dashboard.html'));
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// GET /api/links - Retrieve all links
app.get('/api/links', async (req, res) => {
  try {
    const links = await readLinks();
    res.json({ links });
  } catch (error) {
    console.error('Error reading links:', error);
    res.status(500).json({ error: 'Failed to retrieve links' });
  }
});

// POST /api/links - Create a new link
app.post('/api/links', async (req, res) => {
  try {
    const { title, url, tags } = req.body;

    // Validation: title required
    if (!title || title.trim() === '') {
      return res.status(400).json({ error: 'Title is required' });
    }

    // Validation: URL required and must start with http:// or https://
    if (!url || (!url.startsWith('http://') && !url.startsWith('https://'))) {
      return res.status(400).json({ error: 'URL is required and must start with http:// or https://' });
    }

    // Validation: tags must be an array if provided, max 5 tags
    let processedTags = [];
    if (tags) {
      if (!Array.isArray(tags)) {
        return res.status(400).json({ error: 'Tags must be an array' });
      }
      if (tags.length > 5) {
        return res.status(400).json({ error: 'Maximum 5 tags allowed' });
      }
      // Process tags: trim and lowercase
      processedTags = tags.map(tag => tag.trim().toLowerCase()).filter(tag => tag !== '');
    }

    // Create the new link
    const newLink = {
      id: generateId(),
      title: title.trim(),
      url: url.trim(),
      tags: processedTags,
      created_at: new Date().toISOString()
    };

    // Add link using serialized operation (prevents race conditions)
    await addLink(newLink);

    res.status(201).json(newLink);
  } catch (error) {
    console.error('Error creating link:', error);
    res.status(500).json({ error: 'Failed to create link' });
  }
});

// DELETE /api/links/:id - Delete a link by ID
app.delete('/api/links/:id', async (req, res) => {
  try {
    const { id } = req.params;

    // Remove link using serialized operation (prevents race conditions)
    const removed = await removeLink(id);

    // If link not found, return 404
    if (!removed) {
      return res.status(404).json({ error: 'Link not found' });
    }

    // Return 204 No Content
    res.status(204).send();
  } catch (error) {
    console.error('Error deleting link:', error);
    res.status(500).json({ error: 'Failed to delete link' });
  }
});

// GET /api/stats - Retrieve statistics about links
app.get('/api/stats', async (req, res) => {
  try {
    const links = await readLinks();

    // Compute total_links
    const total_links = links.length;

    // Compute unique tags and tag counts
    const tagCountsMap = {};
    for (const link of links) {
      if (Array.isArray(link.tags)) {
        for (const tag of link.tags) {
          tagCountsMap[tag] = (tagCountsMap[tag] || 0) + 1;
        }
      }
    }

    // Compute total_tags (count of unique tags)
    const total_tags = Object.keys(tagCountsMap).length;

    // Compute recent (last 5 links sorted by created_at descending)
    const sortedLinks = [...links].sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return dateB - dateA; // Descending order (newest first)
    });

    const recent = sortedLinks.slice(0, 5).map(link => ({
      title: link.title,
      url: link.url,
      created_at: link.created_at
    }));

    res.json({
      total_links,
      total_tags,
      tag_counts: tagCountsMap,
      recent
    });
  } catch (error) {
    console.error('Error retrieving stats:', error);
    res.status(500).json({ error: 'Failed to retrieve stats' });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
