const express = require('express');
const router = express.Router();
const search = require('../search');

// GET /api/search?q= - Full-text search
router.get('/', async (req, res) => {
  try {
    const { q } = req.query;

    if (!q || q.trim() === '') {
      return res.json([]);
    }

    const results = await search.search(q);
    res.json(results);
  } catch (error) {
    console.error('Error searching books:', error);
    res.status(500).json({ error: 'Search failed' });
  }
});

module.exports = router;
