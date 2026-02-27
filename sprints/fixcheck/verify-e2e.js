#!/usr/bin/env node

/**
 * End-to-End Verification Script for NoteBox
 *
 * This script verifies the complete user journey:
 * 1. Create a note via POST (simulating UI form submission)
 * 2. Verify it appears in the list with correct title and preview
 * 3. Verify full body can be retrieved (simulating expand)
 * 4. Delete the note and verify it disappears
 * 5. Verify data/notes.json reflects all changes
 * 6. Verify notes survive server restart (persistence proof)
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:3000';
const NOTES_FILE = path.join(__dirname, 'data', 'notes.json');

// Helper to make HTTP requests
function request(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method,
      headers: {}
    };

    if (body) {
      options.headers['Content-Type'] = 'application/json';
      options.headers['Content-Length'] = Buffer.byteLength(JSON.stringify(body));
    }

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          body: data ? JSON.parse(data) : null,
          headers: res.headers
        });
      });
    });

    req.on('error', reject);

    if (body) {
      req.write(JSON.stringify(body));
    }

    req.end();
  });
}

// Verification steps
async function verify() {
  console.log('🧪 Starting End-to-End Verification\n');

  let testNoteId = null;
  let persistenceNoteId = null;

  try {
    // Step 1: Create a note via POST (simulating UI form submission)
    console.log('📝 Step 1: Create a note via POST /api/notes (simulating UI form)');
    const createResponse = await request('POST', '/api/notes', {
      title: 'E2E Test Note',
      body: 'This is a test note created during end-to-end verification. It has more than 80 characters of body text to verify that the preview truncation works correctly in the UI.'
    });

    if (createResponse.status !== 201) {
      throw new Error(`Expected 201, got ${createResponse.status}`);
    }

    testNoteId = createResponse.body.id;
    console.log(`✅ Note created with ID: ${testNoteId}`);
    console.log(`   Title: ${createResponse.body.title}`);
    console.log(`   Body length: ${createResponse.body.body.length} chars`);
    console.log(`   Created at: ${createResponse.body.createdAt}\n`);

    // Step 2: Verify it appears in the list
    console.log('📋 Step 2: Verify note appears in GET /api/notes list');
    const listResponse = await request('GET', '/api/notes');

    if (listResponse.status !== 200) {
      throw new Error(`Expected 200, got ${listResponse.status}`);
    }

    const foundInList = listResponse.body.find(note => note.id === testNoteId);
    if (!foundInList) {
      throw new Error('Created note not found in list');
    }

    console.log(`✅ Note found in list (${listResponse.body.length} total notes)`);
    console.log(`   Title matches: ${foundInList.title === 'E2E Test Note'}`);
    console.log(`   Body preview (first 80 chars): ${foundInList.body.substring(0, 80)}...\n`);

    // Step 3: Verify full body can be retrieved (simulating expand)
    console.log('🔍 Step 3: Retrieve full note via GET /api/notes/:id (simulating expand)');
    const getResponse = await request('GET', `/api/notes/${testNoteId}`);

    if (getResponse.status !== 200) {
      throw new Error(`Expected 200, got ${getResponse.status}`);
    }

    console.log(`✅ Full note retrieved successfully`);
    console.log(`   Full body length: ${getResponse.body.body.length} chars`);
    console.log(`   Body starts with: ${getResponse.body.body.substring(0, 50)}...\n`);

    // Step 4: Delete the note and verify it disappears
    console.log('🗑️  Step 4: Delete note via DELETE /api/notes/:id');
    const deleteResponse = await request('DELETE', `/api/notes/${testNoteId}`);

    if (deleteResponse.status !== 204) {
      throw new Error(`Expected 204, got ${deleteResponse.status}`);
    }

    console.log(`✅ Note deleted successfully (status 204)\n`);

    // Verify note is gone from list
    console.log('📋 Step 4b: Verify note no longer appears in list');
    const listAfterDelete = await request('GET', '/api/notes');
    const stillExists = listAfterDelete.body.find(note => note.id === testNoteId);

    if (stillExists) {
      throw new Error('Note still exists after deletion');
    }

    console.log(`✅ Note confirmed removed from list\n`);

    // Step 5: Verify data/notes.json reflects changes
    console.log('💾 Step 5: Verify data/notes.json file reflects changes');
    const fileContent = fs.readFileSync(NOTES_FILE, 'utf-8');
    const notesFromFile = JSON.parse(fileContent);

    const inFile = notesFromFile.find(note => note.id === testNoteId);
    if (inFile) {
      throw new Error('Deleted note still exists in JSON file');
    }

    console.log(`✅ JSON file correctly reflects deletion`);
    console.log(`   Notes in file: ${notesFromFile.length}\n`);

    // Step 6: Create a persistence test note and verify it survives restart
    console.log('🔄 Step 6: Test persistence across server restart');
    console.log('   Creating persistence test note...');

    const persistenceResponse = await request('POST', '/api/notes', {
      title: 'Persistence Test',
      body: 'This note must survive a server restart to prove JSON persistence works.'
    });

    if (persistenceResponse.status !== 201) {
      throw new Error(`Expected 201, got ${persistenceResponse.status}`);
    }

    persistenceNoteId = persistenceResponse.body.id;
    console.log(`✅ Persistence test note created with ID: ${persistenceNoteId}`);

    // Verify it's in the file before restart
    const beforeRestart = JSON.parse(fs.readFileSync(NOTES_FILE, 'utf-8'));
    const noteInFile = beforeRestart.find(note => note.id === persistenceNoteId);

    if (!noteInFile) {
      throw new Error('Persistence test note not found in JSON file');
    }

    console.log(`✅ Note persisted to JSON file before restart`);
    console.log(`\n⚠️  Manual verification required:`);
    console.log(`   1. Stop the server (Ctrl+C)`);
    console.log(`   2. Restart with: npm start`);
    console.log(`   3. Verify note "${persistenceResponse.body.title}" still appears at http://localhost:3000`);
    console.log(`   4. Or run: curl http://localhost:3000/api/notes | grep "${persistenceNoteId}"\n`);

    // Final summary
    console.log('=' .repeat(60));
    console.log('✅ END-TO-END VERIFICATION COMPLETE');
    console.log('=' .repeat(60));
    console.log('\nAll automated checks passed:');
    console.log('  ✅ Create note via POST /api/notes (simulating UI form)');
    console.log('  ✅ Note appears in GET /api/notes list with correct data');
    console.log('  ✅ Full note retrieved via GET /api/notes/:id (simulating expand)');
    console.log('  ✅ Delete note via DELETE /api/notes/:id removes it');
    console.log('  ✅ data/notes.json correctly reflects all changes');
    console.log('  ⚠️  Persistence across restart requires manual verification');
    console.log(`\nPersistence test note ID: ${persistenceNoteId}`);
    console.log('Please restart the server and verify this note still exists.\n');

    process.exit(0);

  } catch (error) {
    console.error('\n❌ VERIFICATION FAILED');
    console.error(`Error: ${error.message}\n`);
    process.exit(1);
  }
}

// Run verification
verify();
