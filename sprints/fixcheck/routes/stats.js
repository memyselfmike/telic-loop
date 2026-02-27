const express = require('express');
const router = express.Router();
const persistence = require('../persistence');

/**
 * GET /api/stats
 * Returns aggregate statistics computed from all notes:
 * - totalNotes: count of all notes
 * - averageBodyLength: mean body length rounded to integer (0 when no notes)
 * - newestDate: ISO string of most recent createdAt (null when no notes)
 * - oldestDate: ISO string of earliest createdAt (null when no notes)
 */
router.get('/', (req, res) => {
  try {
    const notes = persistence.readNotes();

    // Handle zero-notes edge case
    if (notes.length === 0) {
      return res.status(200).json({
        totalNotes: 0,
        averageBodyLength: 0,
        newestDate: null,
        oldestDate: null
      });
    }

    // Compute totalNotes
    const totalNotes = notes.length;

    // Compute averageBodyLength (mean of body.length, rounded to integer)
    const totalBodyLength = notes.reduce((sum, note) => sum + note.body.length, 0);
    const averageBodyLength = Math.round(totalBodyLength / totalNotes);

    // Compute newestDate (max createdAt)
    const newestDate = notes.reduce((max, note) => {
      return note.createdAt > max ? note.createdAt : max;
    }, notes[0].createdAt);

    // Compute oldestDate (min createdAt)
    const oldestDate = notes.reduce((min, note) => {
      return note.createdAt < min ? note.createdAt : min;
    }, notes[0].createdAt);

    res.status(200).json({
      totalNotes,
      averageBodyLength,
      newestDate,
      oldestDate
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to compute statistics' });
  }
});

module.exports = router;
