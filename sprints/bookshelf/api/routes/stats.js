const express = require('express');
const router = express.Router();
const db = require('../db');

// GET /api/stats - Reading statistics
router.get('/', async (req, res) => {
  try {
    // Total books count
    const totalResult = await db.query('SELECT COUNT(*) as count FROM books');
    const total_books = parseInt(totalResult.rows[0].count);

    // Books by status
    const statusResult = await db.query(`
      SELECT status, COUNT(*) as count
      FROM books
      GROUP BY status
      ORDER BY status
    `);
    const books_by_status = statusResult.rows.map(row => ({
      status: row.status,
      count: parseInt(row.count)
    }));

    // Genre distribution
    const genreResult = await db.query(`
      SELECT genre, COUNT(*) as count
      FROM books
      WHERE genre IS NOT NULL AND genre != ''
      GROUP BY genre
      ORDER BY count DESC, genre
    `);
    const genres = genreResult.rows.map(row => ({
      genre: row.genre,
      count: parseInt(row.count)
    }));

    // Average rating
    const ratingResult = await db.query(`
      SELECT AVG(rating) as avg_rating
      FROM books
      WHERE rating IS NOT NULL
    `);
    const avgRating = ratingResult.rows[0].avg_rating;
    const average_rating = avgRating ? parseFloat(parseFloat(avgRating).toFixed(1)) : null;

    res.json({
      total_books,
      books_by_status,
      genres,
      average_rating
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: 'Failed to fetch stats' });
  }
});

module.exports = router;
