// DOM elements
const newNoteBtn = document.getElementById('new-note-btn');
const newNoteForm = document.getElementById('new-note-form');
const cancelBtn = document.getElementById('cancel-btn');
const notesList = document.getElementById('notes-list');

// State
let notes = [];

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  loadNotes();
  setupEventListeners();
});

// Event listeners
function setupEventListeners() {
  newNoteBtn.addEventListener('click', showNewNoteForm);
  cancelBtn.addEventListener('click', hideNewNoteForm);
  newNoteForm.addEventListener('submit', handleCreateNote);
}

function showNewNoteForm() {
  newNoteForm.classList.remove('hidden');
  newNoteBtn.classList.add('hidden');
  document.getElementById('note-title').focus();
}

function hideNewNoteForm() {
  newNoteForm.classList.add('hidden');
  newNoteBtn.classList.remove('hidden');
  newNoteForm.reset();
}

// API calls
async function loadNotes() {
  try {
    const response = await fetch('/api/notes');
    if (!response.ok) {
      throw new Error('Failed to load notes');
    }
    notes = await response.json();
    renderNotes();
  } catch (error) {
    notesList.innerHTML = '<p class="error">Failed to load notes. Please refresh the page.</p>';
  }
}

async function handleCreateNote(event) {
  event.preventDefault();

  const title = document.getElementById('note-title').value.trim();
  const body = document.getElementById('note-body').value.trim();

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
      const error = await response.json();
      throw new Error(error.error || 'Failed to create note');
    }

    const newNote = await response.json();
    notes.push(newNote);
    renderNotes();
    hideNewNoteForm();
  } catch (error) {
    alert('Failed to create note: ' + error.message);
  }
}

async function deleteNote(noteId) {
  if (!confirm('Are you sure you want to delete this note?')) {
    return;
  }

  try {
    const response = await fetch(`/api/notes/${noteId}`, {
      method: 'DELETE'
    });

    if (!response.ok && response.status !== 404) {
      throw new Error('Failed to delete note');
    }

    // Remove from local state
    notes = notes.filter(note => note.id !== noteId);
    renderNotes();
  } catch (error) {
    alert('Failed to delete note: ' + error.message);
  }
}

// Rendering
function renderNotes() {
  if (notes.length === 0) {
    notesList.innerHTML = '<p class="empty-state">No notes yet. Click "New Note" to create one!</p>';
    return;
  }

  notesList.innerHTML = notes
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .map(note => createNoteCard(note))
    .join('');

  // Add event listeners to all note cards
  document.querySelectorAll('.note-card').forEach(card => {
    const noteId = card.dataset.noteId;
    const note = notes.find(n => n.id === noteId);

    // Toggle expand/collapse on title click
    const titleElement = card.querySelector('.note-title');
    titleElement.addEventListener('click', () => toggleNoteExpansion(card, note));

    // Delete button
    const deleteBtn = card.querySelector('.delete-btn');
    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteNote(noteId);
    });
  });
}

function createNoteCard(note) {
  const preview = getBodyPreview(note.body);
  const dateStr = formatDate(note.createdAt);

  return `
    <div class="note-card" data-note-id="${note.id}">
      <div class="note-header">
        <h3 class="note-title">${escapeHtml(note.title)}</h3>
        <button class="delete-btn" title="Delete note">×</button>
      </div>
      <div class="note-meta">${dateStr}</div>
      <div class="note-body-preview">${escapeHtml(preview)}</div>
      <div class="note-body-full hidden">${escapeHtml(note.body)}</div>
    </div>
  `;
}

function toggleNoteExpansion(cardElement, note) {
  const preview = cardElement.querySelector('.note-body-preview');
  const fullBody = cardElement.querySelector('.note-body-full');
  const isExpanded = !fullBody.classList.contains('hidden');

  if (isExpanded) {
    // Collapse
    preview.classList.remove('hidden');
    fullBody.classList.add('hidden');
    cardElement.classList.remove('expanded');
  } else {
    // Expand
    preview.classList.add('hidden');
    fullBody.classList.remove('hidden');
    cardElement.classList.add('expanded');
  }
}

// Utility functions
function getBodyPreview(body) {
  if (body.length <= 80) {
    return body;
  }
  return body.substring(0, 80) + '...';
}

function formatDate(isoString) {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
