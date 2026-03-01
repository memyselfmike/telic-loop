const express = require('express');
const router = express.Router();
const store = require('./store');

// GET /api/notes - List all notes
router.get('/notes', (req, res) => {
  const notes = store.getAllNotes();
  res.status(200).json(notes);
});

// POST /api/notes - Create a note
router.post('/notes', (req, res) => {
  const { title, body } = req.body;

  if (!title || typeof title !== 'string' || title.trim() === '') {
    return res.status(400).json({ error: 'title is required and must be a non-empty string' });
  }

  if (!body || typeof body !== 'string' || body.trim() === '') {
    return res.status(400).json({ error: 'body is required and must be a non-empty string' });
  }

  const newNote = store.createNote(title.trim(), body.trim());
  res.status(201).json(newNote);
});

// GET /api/notes/:id - Get single note
router.get('/notes/:id', (req, res) => {
  const note = store.getNoteById(req.params.id);
  if (!note) {
    return res.status(404).json({ error: 'Note not found' });
  }
  res.status(200).json(note);
});

// DELETE /api/notes/:id - Delete a note
router.delete('/notes/:id', (req, res) => {
  const deleted = store.deleteNote(req.params.id);
  if (!deleted) {
    return res.status(404).json({ error: 'Note not found' });
  }
  res.status(204).send();
});

module.exports = router;
