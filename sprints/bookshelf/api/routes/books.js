const express = require('express');
const router = express.Router();
const db = require('../db');
const search = require('../search');

// GET /api/books - List all books (with optional status filter)
router.get('/', async (req, res) => {
  try {
    const { status } = req.query;

    let query = 'SELECT * FROM books ORDER BY date_added DESC';
    const params = [];

    if (status) {
      query = 'SELECT * FROM books WHERE status = $1 ORDER BY date_added DESC';
      params.push(status);
    }

    const result = await db.query(query, params);
    res.json(result.rows);
  } catch (error) {
    console.error('Error fetching books:', error);
    res.status(500).json({ error: 'Failed to fetch books' });
  }
});

// GET /api/books/:id - Get single book by ID
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await db.query('SELECT * FROM books WHERE id = $1', [id]);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Book not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching book:', error);
    res.status(500).json({ error: 'Failed to fetch book' });
  }
});

// POST /api/books - Create new book
router.post('/', async (req, res) => {
  try {
    const { title, author, genre, cover_url, status, rating, notes, date_finished } = req.body;

    // Validate required fields
    if (!title || !author) {
      return res.status(400).json({ error: 'Title and author are required' });
    }

    // Validate status if provided
    const validStatuses = ['want_to_read', 'reading', 'finished', 'abandoned'];
    if (status && !validStatuses.includes(status)) {
      return res.status(400).json({ error: 'Invalid status value' });
    }

    // Validate rating if provided
    if (rating !== undefined && rating !== null && (rating < 1 || rating > 5)) {
      return res.status(400).json({ error: 'Rating must be between 1 and 5' });
    }

    const result = await db.query(
      `INSERT INTO books (title, author, genre, cover_url, status, rating, notes, date_finished)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
       RETURNING *`,
      [
        title,
        author,
        genre || null,
        cover_url || null,
        status || 'want_to_read',
        rating || null,
        notes || null,
        date_finished || null
      ]
    );

    const book = result.rows[0];

    // Sync to search index (fire-and-forget)
    search.addOrUpdate(book).catch(err =>
      console.error('[Search Sync] Error adding book:', err)
    );

    res.status(201).json(book);
  } catch (error) {
    console.error('Error creating book:', error);
    res.status(500).json({ error: 'Failed to create book' });
  }
});

// PUT /api/books/:id - Update book
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { title, author, genre, cover_url, status, rating, notes, date_finished } = req.body;

    // Check if book exists
    const existingBook = await db.query('SELECT * FROM books WHERE id = $1', [id]);
    if (existingBook.rows.length === 0) {
      return res.status(404).json({ error: 'Book not found' });
    }

    // Validate status if provided
    const validStatuses = ['want_to_read', 'reading', 'finished', 'abandoned'];
    if (status && !validStatuses.includes(status)) {
      return res.status(400).json({ error: 'Invalid status value' });
    }

    // Validate rating if provided
    if (rating !== undefined && rating !== null && (rating < 1 || rating > 5)) {
      return res.status(400).json({ error: 'Rating must be between 1 and 5' });
    }

    // Build update query with only provided fields
    const updates = [];
    const params = [];
    let paramCount = 1;

    if (title !== undefined) {
      updates.push(`title = $${paramCount++}`);
      params.push(title);
    }
    if (author !== undefined) {
      updates.push(`author = $${paramCount++}`);
      params.push(author);
    }
    if (genre !== undefined) {
      updates.push(`genre = $${paramCount++}`);
      params.push(genre);
    }
    if (cover_url !== undefined) {
      updates.push(`cover_url = $${paramCount++}`);
      params.push(cover_url);
    }
    if (status !== undefined) {
      updates.push(`status = $${paramCount++}`);
      params.push(status);
    }
    if (rating !== undefined) {
      updates.push(`rating = $${paramCount++}`);
      params.push(rating);
    }
    if (notes !== undefined) {
      updates.push(`notes = $${paramCount++}`);
      params.push(notes);
    }
    if (date_finished !== undefined) {
      updates.push(`date_finished = $${paramCount++}`);
      params.push(date_finished);
    }

    if (updates.length === 0) {
      return res.json(existingBook.rows[0]);
    }

    params.push(id);
    const query = `UPDATE books SET ${updates.join(', ')} WHERE id = $${paramCount} RETURNING *`;

    const result = await db.query(query, params);
    const book = result.rows[0];

    // Sync to search index (fire-and-forget)
    search.addOrUpdate(book).catch(err =>
      console.error('[Search Sync] Error updating book:', err)
    );

    res.json(book);
  } catch (error) {
    console.error('Error updating book:', error);
    res.status(500).json({ error: 'Failed to update book' });
  }
});

// DELETE /api/books/:id - Delete book
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;

    const result = await db.query('DELETE FROM books WHERE id = $1 RETURNING id', [id]);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Book not found' });
    }

    // Remove from search index (fire-and-forget)
    search.remove(id).catch(err =>
      console.error('[Search Sync] Error removing book:', err)
    );

    res.status(204).send();
  } catch (error) {
    console.error('Error deleting book:', error);
    res.status(500).json({ error: 'Failed to delete book' });
  }
});

module.exports = router;
