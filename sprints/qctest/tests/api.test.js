const { describe, it, before, after } = require('node:test');
const assert = require('node:assert');
const request = require('supertest');
const express = require('express');
const routes = require('../routes');
const store = require('../store');
const fs = require('fs');
const path = require('path');

// Create a test app instance
function createTestApp() {
  const app = express();
  app.use(express.json());
  app.use(routes);
  return app;
}

const DATA_FILE = path.join(__dirname, '..', 'data', 'notes.json');

describe('API Tests', () => {
  let app;

  before(() => {
    app = createTestApp();
    // Clean up any existing test data
    if (fs.existsSync(DATA_FILE)) {
      fs.unlinkSync(DATA_FILE);
    }
  });

  after(() => {
    // Clean up test data after all tests
    if (fs.existsSync(DATA_FILE)) {
      fs.unlinkSync(DATA_FILE);
    }
  });

  describe('GET /api/notes', () => {
    it('should return empty array initially', async () => {
      const response = await request(app)
        .get('/api/notes')
        .expect(200);

      assert.strictEqual(Array.isArray(response.body), true, 'Response should be an array');
      assert.strictEqual(response.body.length, 0, 'Array should be empty initially');
    });
  });

  describe('POST /api/notes', () => {
    it('should create a new note and return 201', async () => {
      const newNote = {
        title: 'Test Note',
        body: 'This is a test note body'
      };

      const response = await request(app)
        .post('/api/notes')
        .send(newNote)
        .expect(201);

      assert.strictEqual(typeof response.body.id, 'string', 'Response should contain an id');
      assert.strictEqual(response.body.title, newNote.title, 'Title should match');
      assert.strictEqual(response.body.body, newNote.body, 'Body should match');
      assert.strictEqual(typeof response.body.createdAt, 'string', 'Should have createdAt timestamp');
    });

    it('should return 400 when title is missing', async () => {
      const invalidNote = {
        body: 'Body without title'
      };

      const response = await request(app)
        .post('/api/notes')
        .send(invalidNote)
        .expect(400);

      assert.strictEqual(typeof response.body.error, 'string', 'Should return error message');
      assert.match(response.body.error, /title/i, 'Error should mention title');
    });

    it('should return 400 when title is empty string', async () => {
      const invalidNote = {
        title: '',
        body: 'Body with empty title'
      };

      const response = await request(app)
        .post('/api/notes')
        .send(invalidNote)
        .expect(400);

      assert.strictEqual(typeof response.body.error, 'string', 'Should return error message');
    });

    it('should return 400 when body is missing', async () => {
      const invalidNote = {
        title: 'Title without body'
      };

      const response = await request(app)
        .post('/api/notes')
        .send(invalidNote)
        .expect(400);

      assert.strictEqual(typeof response.body.error, 'string', 'Should return error message');
      assert.match(response.body.error, /body/i, 'Error should mention body');
    });

    it('should return 400 when body is empty string', async () => {
      const invalidNote = {
        title: 'Title',
        body: ''
      };

      const response = await request(app)
        .post('/api/notes')
        .send(invalidNote)
        .expect(400);

      assert.strictEqual(typeof response.body.error, 'string', 'Should return error message');
    });
  });

  describe('GET /api/notes/:id', () => {
    let createdNoteId;

    before(async () => {
      // Create a note to test retrieval
      const response = await request(app)
        .post('/api/notes')
        .send({
          title: 'Note for GET test',
          body: 'This note will be retrieved by ID'
        });
      createdNoteId = response.body.id;
    });

    it('should return the created note by ID', async () => {
      const response = await request(app)
        .get(`/api/notes/${createdNoteId}`)
        .expect(200);

      assert.strictEqual(response.body.id, createdNoteId, 'ID should match');
      assert.strictEqual(response.body.title, 'Note for GET test', 'Title should match');
      assert.strictEqual(response.body.body, 'This note will be retrieved by ID', 'Body should match');
    });

    it('should return 404 for non-existent ID', async () => {
      const response = await request(app)
        .get('/api/notes/non-existent-id-12345')
        .expect(404);

      assert.strictEqual(typeof response.body.error, 'string', 'Should return error message');
      assert.match(response.body.error, /not found/i, 'Error should mention not found');
    });
  });

  describe('DELETE /api/notes/:id', () => {
    let noteToDelete;

    before(async () => {
      // Create a note to delete
      const response = await request(app)
        .post('/api/notes')
        .send({
          title: 'Note to delete',
          body: 'This note will be deleted'
        });
      noteToDelete = response.body.id;
    });

    it('should delete a note and return 204', async () => {
      const response = await request(app)
        .delete(`/api/notes/${noteToDelete}`)
        .expect(204);

      // Verify the response body is empty for 204
      assert.strictEqual(response.text, '', 'Response body should be empty');
    });

    it('should return 404 when deleting the same note again', async () => {
      const response = await request(app)
        .delete(`/api/notes/${noteToDelete}`)
        .expect(404);

      assert.strictEqual(typeof response.body.error, 'string', 'Should return error message');
    });

    it('should return 404 when deleting non-existent note', async () => {
      const response = await request(app)
        .delete('/api/notes/never-existed-id-99999')
        .expect(404);

      assert.strictEqual(typeof response.body.error, 'string', 'Should return error message');
    });
  });

  describe('CRUD Integration - Persistence Verification', () => {
    it('should persist notes and retrieve them after creation', async () => {
      // Create a note
      const createResponse = await request(app)
        .post('/api/notes')
        .send({
          title: 'Persistence Test',
          body: 'This note should persist and be retrievable'
        })
        .expect(201);

      const noteId = createResponse.body.id;

      // Retrieve it by ID
      const getByIdResponse = await request(app)
        .get(`/api/notes/${noteId}`)
        .expect(200);

      assert.strictEqual(getByIdResponse.body.id, noteId, 'Retrieved note ID should match');
      assert.strictEqual(getByIdResponse.body.title, 'Persistence Test', 'Title should match');
      assert.strictEqual(getByIdResponse.body.body, 'This note should persist and be retrievable', 'Body should match');

      // Retrieve it in the list
      const getAllResponse = await request(app)
        .get('/api/notes')
        .expect(200);

      const foundNote = getAllResponse.body.find(note => note.id === noteId);
      assert.ok(foundNote, 'Note should be in the list');
      assert.strictEqual(foundNote.title, 'Persistence Test', 'Title in list should match');
    });

    it('should confirm note removal after deletion', async () => {
      // Create a note
      const createResponse = await request(app)
        .post('/api/notes')
        .send({
          title: 'Note to Remove',
          body: 'This will be deleted and verified'
        })
        .expect(201);

      const noteId = createResponse.body.id;

      // Delete it
      await request(app)
        .delete(`/api/notes/${noteId}`)
        .expect(204);

      // Verify it's gone from GET by ID
      await request(app)
        .get(`/api/notes/${noteId}`)
        .expect(404);

      // Verify it's gone from the list
      const getAllResponse = await request(app)
        .get('/api/notes')
        .expect(200);

      const foundNote = getAllResponse.body.find(note => note.id === noteId);
      assert.strictEqual(foundNote, undefined, 'Deleted note should not be in the list');
    });
  });
});
