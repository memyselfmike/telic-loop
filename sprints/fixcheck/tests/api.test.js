const request = require('supertest');
const fs = require('fs');
const path = require('path');
const app = require('../server');

const NOTES_FILE = path.join(__dirname, '../data/notes.json');

/**
 * Reset notes.json to a clean state before each test
 * to prevent state leakage between tests
 */
function resetNotesFile(initialData = []) {
  const dataDir = path.dirname(NOTES_FILE);
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  fs.writeFileSync(NOTES_FILE, JSON.stringify(initialData, null, 2), 'utf-8');
}

describe('GET /api/notes', () => {
  test('should return empty array when no notes exist', async () => {
    resetNotesFile([]);

    const response = await request(app).get('/api/notes');

    expect(response.status).toBe(200);
    expect(response.body).toEqual([]);
  });

  test('should return populated array when notes exist', async () => {
    const testNotes = [
      { id: '1', title: 'First Note', body: 'First body', createdAt: '2024-01-01T00:00:00.000Z' },
      { id: '2', title: 'Second Note', body: 'Second body', createdAt: '2024-01-02T00:00:00.000Z' }
    ];
    resetNotesFile(testNotes);

    const response = await request(app).get('/api/notes');

    expect(response.status).toBe(200);
    expect(response.body).toEqual(testNotes);
    expect(response.body.length).toBe(2);
  });
});

describe('POST /api/notes', () => {
  beforeEach(() => {
    resetNotesFile([]);
  });

  test('should create note with valid input and return 201', async () => {
    const newNote = {
      title: 'Test Note',
      body: 'This is a test note body'
    };

    const response = await request(app)
      .post('/api/notes')
      .send(newNote);

    expect(response.status).toBe(201);
    expect(response.body).toHaveProperty('id');
    expect(response.body).toHaveProperty('createdAt');
    expect(response.body.title).toBe('Test Note');
    expect(response.body.body).toBe('This is a test note body');

    // Verify persistence
    const notesData = JSON.parse(fs.readFileSync(NOTES_FILE, 'utf-8'));
    expect(notesData.length).toBe(1);
    expect(notesData[0].title).toBe('Test Note');
  });

  test('should return 400 when title is missing', async () => {
    const invalidNote = {
      body: 'Body without title'
    };

    const response = await request(app)
      .post('/api/notes')
      .send(invalidNote);

    expect(response.status).toBe(400);
    expect(response.body).toHaveProperty('error');
    expect(response.body.error).toContain('Title');
  });

  test('should return 400 when body is missing', async () => {
    const invalidNote = {
      title: 'Title without body'
    };

    const response = await request(app)
      .post('/api/notes')
      .send(invalidNote);

    expect(response.status).toBe(400);
    expect(response.body).toHaveProperty('error');
    expect(response.body.error).toContain('Body');
  });

  test('should return 400 when title is empty string', async () => {
    const invalidNote = {
      title: '   ',
      body: 'Valid body'
    };

    const response = await request(app)
      .post('/api/notes')
      .send(invalidNote);

    expect(response.status).toBe(400);
    expect(response.body).toHaveProperty('error');
  });
});

describe('GET /api/notes/:id', () => {
  beforeEach(() => {
    const testNotes = [
      { id: 'note-123', title: 'Findable Note', body: 'This note exists', createdAt: '2024-01-01T00:00:00.000Z' },
      { id: 'note-456', title: 'Another Note', body: 'Another body', createdAt: '2024-01-02T00:00:00.000Z' }
    ];
    resetNotesFile(testNotes);
  });

  test('should return 200 and note when note is found', async () => {
    const response = await request(app).get('/api/notes/note-123');

    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('id', 'note-123');
    expect(response.body).toHaveProperty('title', 'Findable Note');
    expect(response.body).toHaveProperty('body', 'This note exists');
  });

  test('should return 404 when note is not found', async () => {
    const response = await request(app).get('/api/notes/nonexistent-id');

    expect(response.status).toBe(404);
    expect(response.body).toHaveProperty('error');
    expect(response.body.error).toContain('not found');
  });
});

describe('DELETE /api/notes/:id', () => {
  beforeEach(() => {
    const testNotes = [
      { id: 'delete-me', title: 'To Delete', body: 'Will be deleted', createdAt: '2024-01-01T00:00:00.000Z' },
      { id: 'keep-me', title: 'To Keep', body: 'Will stay', createdAt: '2024-01-02T00:00:00.000Z' }
    ];
    resetNotesFile(testNotes);
  });

  test('should return 204 when note is found and deleted', async () => {
    const response = await request(app).delete('/api/notes/delete-me');

    expect(response.status).toBe(204);
    expect(response.body).toEqual({});

    // Verify note was removed from file
    const notesData = JSON.parse(fs.readFileSync(NOTES_FILE, 'utf-8'));
    expect(notesData.length).toBe(1);
    expect(notesData[0].id).toBe('keep-me');
  });

  test('should return 404 when note is not found', async () => {
    const response = await request(app).delete('/api/notes/nonexistent-id');

    expect(response.status).toBe(404);
    expect(response.body).toHaveProperty('error');
    expect(response.body.error).toContain('not found');

    // Verify original notes still exist
    const notesData = JSON.parse(fs.readFileSync(NOTES_FILE, 'utf-8'));
    expect(notesData.length).toBe(2);
  });
});
