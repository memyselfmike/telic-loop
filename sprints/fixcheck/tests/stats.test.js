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

describe('GET /api/stats', () => {
  // Reset before each test to prevent state leakage
  beforeEach(() => {
    resetNotesFile([]);
  });

  test('should handle zero-notes edge case gracefully', async () => {
    const response = await request(app).get('/api/stats');

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      totalNotes: 0,
      averageBodyLength: 0,
      newestDate: null,
      oldestDate: null
    });
  });

  test('should compute correct stats for single note', async () => {
    const testNotes = [
      {
        id: '1',
        title: 'Solo Note',
        body: 'This is exactly 24 chars',
        createdAt: '2024-01-15T10:00:00.000Z'
      }
    ];
    resetNotesFile(testNotes);

    const response = await request(app).get('/api/stats');

    expect(response.status).toBe(200);
    expect(response.body.totalNotes).toBe(1);
    expect(response.body.averageBodyLength).toBe(24);
    expect(response.body.newestDate).toBe('2024-01-15T10:00:00.000Z');
    expect(response.body.oldestDate).toBe('2024-01-15T10:00:00.000Z');
  });

  test('should compute correct stats for multiple notes', async () => {
    const testNotes = [
      {
        id: '1',
        title: 'First',
        body: 'Short',  // 5 chars
        createdAt: '2024-01-10T08:00:00.000Z'
      },
      {
        id: '2',
        title: 'Second',
        body: 'Medium length body here',  // 23 chars
        createdAt: '2024-01-20T12:00:00.000Z'
      },
      {
        id: '3',
        title: 'Third',
        body: 'This is a longer body with more content to test averaging',  // 57 chars
        createdAt: '2024-01-15T10:00:00.000Z'
      }
    ];
    resetNotesFile(testNotes);

    const response = await request(app).get('/api/stats');

    expect(response.status).toBe(200);
    expect(response.body.totalNotes).toBe(3);
    // Average: (5 + 23 + 57) / 3 = 85 / 3 = 28.33... = 28
    expect(response.body.averageBodyLength).toBe(28);
    // Newest: 2024-01-20 (Second)
    expect(response.body.newestDate).toBe('2024-01-20T12:00:00.000Z');
    // Oldest: 2024-01-10 (First)
    expect(response.body.oldestDate).toBe('2024-01-10T08:00:00.000Z');
  });

  test('should handle notes with identical createdAt dates', async () => {
    const sameDate = '2024-01-15T12:00:00.000Z';
    const testNotes = [
      { id: '1', title: 'First', body: 'Body one', createdAt: sameDate },
      { id: '2', title: 'Second', body: 'Body two', createdAt: sameDate },
      { id: '3', title: 'Third', body: 'Body three', createdAt: sameDate }
    ];
    resetNotesFile(testNotes);

    const response = await request(app).get('/api/stats');

    expect(response.status).toBe(200);
    expect(response.body.totalNotes).toBe(3);
    expect(response.body.newestDate).toBe(sameDate);
    expect(response.body.oldestDate).toBe(sameDate);
  });

  test('should update stats after note deletion', async () => {
    // Setup: 3 notes
    const testNotes = [
      {
        id: 'delete-me',
        title: 'To Delete',
        body: 'Very long body content here to affect average significantly',  // 57 chars
        createdAt: '2024-01-25T15:00:00.000Z'  // This is the newest
      },
      {
        id: 'keep-1',
        title: 'Keep First',
        body: 'Short',  // 5 chars
        createdAt: '2024-01-10T08:00:00.000Z'  // This is the oldest
      },
      {
        id: 'keep-2',
        title: 'Keep Second',
        body: 'Medium body',  // 11 chars
        createdAt: '2024-01-15T12:00:00.000Z'
      }
    ];
    resetNotesFile(testNotes);

    // Verify initial stats: 3 notes, avg = (59 + 5 + 11) / 3 = 75 / 3 = 25
    const initialResponse = await request(app).get('/api/stats');
    expect(initialResponse.status).toBe(200);
    expect(initialResponse.body.totalNotes).toBe(3);
    expect(initialResponse.body.averageBodyLength).toBe(25);
    expect(initialResponse.body.newestDate).toBe('2024-01-25T15:00:00.000Z');
    expect(initialResponse.body.oldestDate).toBe('2024-01-10T08:00:00.000Z');

    // Delete the newest note with longest body
    await request(app).delete('/api/notes/delete-me');

    // Verify updated stats: 2 notes, avg = (5 + 11) / 2 = 8
    const updatedResponse = await request(app).get('/api/stats');
    expect(updatedResponse.status).toBe(200);
    expect(updatedResponse.body.totalNotes).toBe(2);
    expect(updatedResponse.body.averageBodyLength).toBe(8);
    expect(updatedResponse.body.newestDate).toBe('2024-01-15T12:00:00.000Z');  // Now keep-2 is newest
    expect(updatedResponse.body.oldestDate).toBe('2024-01-10T08:00:00.000Z');  // keep-1 still oldest
  });

  test('should update stats after deleting all notes', async () => {
    // Setup: 2 notes
    const testNotes = [
      { id: 'note-1', title: 'First', body: 'Body one', createdAt: '2024-01-10T08:00:00.000Z' },
      { id: 'note-2', title: 'Second', body: 'Body two', createdAt: '2024-01-15T12:00:00.000Z' }
    ];
    resetNotesFile(testNotes);

    // Verify initial stats
    const initialResponse = await request(app).get('/api/stats');
    expect(initialResponse.status).toBe(200);
    expect(initialResponse.body.totalNotes).toBe(2);

    // Delete both notes
    await request(app).delete('/api/notes/note-1');
    await request(app).delete('/api/notes/note-2');

    // Verify stats return to zero-notes state
    const finalResponse = await request(app).get('/api/stats');
    expect(finalResponse.status).toBe(200);
    expect(finalResponse.body).toEqual({
      totalNotes: 0,
      averageBodyLength: 0,
      newestDate: null,
      oldestDate: null
    });
  });

  test('should handle notes with empty body strings', async () => {
    const testNotes = [
      { id: '1', title: 'Empty Body', body: '', createdAt: '2024-01-10T08:00:00.000Z' },
      { id: '2', title: 'Normal Body', body: 'Content', createdAt: '2024-01-15T12:00:00.000Z' }
    ];
    resetNotesFile(testNotes);

    const response = await request(app).get('/api/stats');

    expect(response.status).toBe(200);
    expect(response.body.totalNotes).toBe(2);
    // Average: (0 + 7) / 2 = 3.5 = 4
    expect(response.body.averageBodyLength).toBe(4);
  });

  test('should round average body length to nearest integer', async () => {
    const testNotes = [
      { id: '1', title: 'First', body: 'A', createdAt: '2024-01-10T08:00:00.000Z' },  // 1 char
      { id: '2', title: 'Second', body: 'AB', createdAt: '2024-01-15T12:00:00.000Z' }  // 2 chars
    ];
    resetNotesFile(testNotes);

    const response = await request(app).get('/api/stats');

    expect(response.status).toBe(200);
    expect(response.body.totalNotes).toBe(2);
    // Average: (1 + 2) / 2 = 1.5, Math.round(1.5) = 2
    expect(response.body.averageBodyLength).toBe(2);
  });
});
