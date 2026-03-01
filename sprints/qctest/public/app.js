// DOM elements
const newNoteBtn = document.getElementById('new-note-btn');
const noteForm = document.getElementById('note-form');
const cancelBtn = document.getElementById('cancel-btn');
const notesContainer = document.getElementById('notes-container');
const emptyState = document.getElementById('empty-state');
const titleInput = document.getElementById('note-title');
const bodyInput = document.getElementById('note-body');

// State
let notes = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadNotes();
  setupEventListeners();
});

function setupEventListeners() {
  newNoteBtn.addEventListener('click', showForm);
  cancelBtn.addEventListener('click', hideForm);
  noteForm.addEventListener('submit', handleSubmit);
}

function showForm() {
  noteForm.classList.remove('hidden');
  titleInput.focus();
}

function hideForm() {
  noteForm.classList.add('hidden');
  titleInput.value = '';
  bodyInput.value = '';
}

async function loadNotes() {
  try {
    const response = await fetch('/api/notes');
    if (!response.ok) {
      throw new Error('Failed to load notes');
    }
    notes = await response.json();
    renderNotes();
  } catch (error) {
    alert('Failed to load notes');
  }
}

async function handleSubmit(e) {
  e.preventDefault();

  const title = titleInput.value.trim();
  const body = bodyInput.value.trim();

  if (!title || !body) {
    alert('Title and body are required');
    return;
  }

  try {
    const response = await fetch('/api/notes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ title, body })
    });

    if (!response.ok) {
      throw new Error('Failed to create note');
    }

    const newNote = await response.json();
    notes.unshift(newNote);
    renderNotes();
    hideForm();
  } catch (error) {
    alert('Failed to create note');
  }
}

function renderNotes() {
  if (notes.length === 0) {
    emptyState.classList.remove('hidden');
    notesContainer.innerHTML = '';
    return;
  }

  emptyState.classList.add('hidden');
  notesContainer.innerHTML = notes.map(note => createNoteCardHTML(note)).join('');
  attachCardEventListeners();
}

function createNoteCardHTML(note) {
  const preview = note.body.length > 80 ? note.body.substring(0, 80) + '...' : note.body;
  const date = new Date(note.createdAt).toLocaleString();

  return `
    <div class="note-card" data-id="${note.id}">
      <div class="note-card-header">
        <h3 class="note-title" data-id="${note.id}">${escapeHtml(note.title)}</h3>
        <button class="delete-btn" data-id="${note.id}">Delete</button>
      </div>
      <div class="note-body-preview">${escapeHtml(preview)}</div>
      <div class="note-body-full">${escapeHtml(note.body)}</div>
      <div class="note-meta">Created: ${date}</div>
    </div>
  `;
}

function attachCardEventListeners() {
  // Title click to toggle expand
  document.querySelectorAll('.note-title').forEach(title => {
    title.addEventListener('click', handleTitleClick);
  });

  // Delete button click
  document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', handleDelete);
  });
}

function handleTitleClick(e) {
  const noteId = e.target.dataset.id;
  const card = document.querySelector(`.note-card[data-id="${noteId}"]`);
  const preview = card.querySelector('.note-body-preview');
  const full = card.querySelector('.note-body-full');

  const isExpanded = full.classList.contains('expanded');

  if (isExpanded) {
    full.classList.remove('expanded');
    preview.style.display = 'block';
  } else {
    full.classList.add('expanded');
    preview.style.display = 'none';
  }
}

async function handleDelete(e) {
  const noteId = e.target.dataset.id;

  if (!confirm('Delete this note?')) {
    return;
  }

  try {
    const response = await fetch(`/api/notes/${noteId}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error('Failed to delete note');
    }

    notes = notes.filter(note => note.id !== noteId);
    renderNotes();
  } catch (error) {
    alert('Failed to delete note');
  }
}

function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
