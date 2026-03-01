const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const DATA_DIR = path.join(__dirname, 'data');
const DATA_FILE = path.join(DATA_DIR, 'notes.json');

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

function readNotes() {
  try {
    const data = fs.readFileSync(DATA_FILE, 'utf-8');
    return JSON.parse(data);
  } catch (err) {
    if (err.code === 'ENOENT') {
      return [];
    }
    throw err;
  }
}

function writeNotes(notes) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(notes, null, 2), 'utf-8');
}

function getAllNotes() {
  return readNotes();
}

function getNoteById(id) {
  const notes = readNotes();
  return notes.find(note => note.id === id) || null;
}

function createNote(title, body) {
  const notes = readNotes();
  const newNote = {
    id: crypto.randomUUID(),
    title,
    body,
    createdAt: new Date().toISOString()
  };
  notes.push(newNote);
  writeNotes(notes);
  return newNote;
}

function deleteNote(id) {
  const notes = readNotes();
  const filtered = notes.filter(note => note.id !== id);
  if (filtered.length === notes.length) {
    return false; // Note not found
  }
  writeNotes(filtered);
  return true;
}

module.exports = {
  getAllNotes,
  getNoteById,
  createNote,
  deleteNote
};
