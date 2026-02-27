const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const { readNotes, writeNotes } = require('../persistence');

/**
 * GET /api/notes
 * Returns all notes
 */
router.get('/', (req, res) => {
  try {
    const notes = readNotes();
    res.status(200).json(notes);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve notes' });
  }
});

/**
 * POST /api/notes
 * Creates a new note
 * Body: { title: string, body: string }
 * Returns 201 with created note or 400 if validation fails
 */
router.post('/', (req, res) => {
  try {
    const { title, body } = req.body;

    // Validate both fields are present and non-empty
    if (!title || typeof title !== 'string' || title.trim() === '') {
      return res.status(400).json({ error: 'Title is required and must be non-empty' });
    }

    if (!body || typeof body !== 'string' || body.trim() === '') {
      return res.status(400).json({ error: 'Body is required and must be non-empty' });
    }

    // Create new note with generated ID and timestamp
    const newNote = {
      id: crypto.randomUUID(),
      title: title.trim(),
      body: body.trim(),
      createdAt: new Date().toISOString()
    };

    // Persist the note
    const notes = readNotes();
    notes.push(newNote);
    writeNotes(notes);

    res.status(201).json(newNote);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create note' });
  }
});

/**
 * GET /api/notes/:id
 * Returns a specific note by ID
 * Returns 200 with note or 404 if not found
 */
router.get('/:id', (req, res) => {
  try {
    const { id } = req.params;
    const notes = readNotes();
    const note = notes.find(n => n.id === id);

    if (!note) {
      return res.status(404).json({ error: 'Note not found' });
    }

    res.status(200).json(note);
  } catch (error) {
    res.status(500).json({ error: 'Failed to retrieve note' });
  }
});

/**
 * DELETE /api/notes/:id
 * Deletes a note by ID
 * Returns 204 on success or 404 if not found
 */
router.delete('/:id', (req, res) => {
  try {
    const { id } = req.params;
    const notes = readNotes();
    const noteIndex = notes.findIndex(n => n.id === id);

    if (noteIndex === -1) {
      return res.status(404).json({ error: 'Note not found' });
    }

    // Remove the note and persist
    notes.splice(noteIndex, 1);
    writeNotes(notes);

    res.status(204).send();
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete note' });
  }
});

module.exports = router;
