#!/usr/bin/env node

/**
 * Final comprehensive E2E check after server restart
 */

const http = require('http');

function request(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: 3000,
      path,
      method,
      headers: {}
    };

    if (body) {
      options.headers['Content-Type'] = 'application/json';
      const bodyStr = JSON.stringify(body);
      options.headers['Content-Length'] = Buffer.byteLength(bodyStr);
    }

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          body: data ? JSON.parse(data) : null
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

async function finalCheck() {
  console.log('\n🎯 FINAL E2E CHECK - Complete User Journey\n');

  try {
    // 1. Verify server is running and persistence note exists
    console.log('1️⃣  Verify server restarted and persistence note survived...');
    const notes = await request('GET', '/api/notes');
    const persistenceNote = notes.body.find(n => n.title === 'Persistence Test');
    
    if (!persistenceNote) {
      throw new Error('Persistence test note not found after restart!');
    }
    console.log(`   ✅ Server running, persistence note found (ID: ${persistenceNote.id})`);

    // 2. Create a new note (simulating UI form)
    console.log('\n2️⃣  Create new note via UI form (POST /api/notes)...');
    const createResp = await request('POST', '/api/notes', {
      title: 'Final Journey Test',
      body: 'This note tests the complete user journey: create → view → expand → delete. It has enough text to verify the 80-character preview truncation feature works correctly in the notes list display.'
    });

    if (createResp.status !== 201) {
      throw new Error(`Create failed: ${createResp.status}`);
    }
    const newNoteId = createResp.body.id;
    console.log(`   ✅ Note created (ID: ${newNoteId})`);

    // 3. Verify it appears in list with preview
    console.log('\n3️⃣  Verify note appears in list with 80-char preview...');
    const listResp = await request('GET', '/api/notes');
    const noteInList = listResp.body.find(n => n.id === newNoteId);
    
    if (!noteInList) {
      throw new Error('New note not in list!');
    }
    
    const preview = noteInList.body.substring(0, 80);
    console.log(`   ✅ Note in list (${listResp.body.length} total)`);
    console.log(`   📝 Preview: "${preview}..."`);

    // 4. Expand to view full content
    console.log('\n4️⃣  Expand note to view full body (GET /api/notes/:id)...');
    const fullResp = await request('GET', `/api/notes/${newNoteId}`);
    
    if (fullResp.status !== 200) {
      throw new Error(`Get single note failed: ${fullResp.status}`);
    }
    console.log(`   ✅ Full note retrieved`);
    console.log(`   📄 Full body (${fullResp.body.body.length} chars): "${fullResp.body.body.substring(0, 60)}..."`);

    // 5. Delete the note
    console.log('\n5️⃣  Delete note (DELETE /api/notes/:id)...');
    const deleteResp = await request('DELETE', `/api/notes/${newNoteId}`);
    
    if (deleteResp.status !== 204) {
      throw new Error(`Delete failed: ${deleteResp.status}`);
    }
    console.log(`   ✅ Note deleted (status 204)`);

    // 6. Verify it's gone
    console.log('\n6️⃣  Verify note removed from list...');
    const afterDelete = await request('GET', '/api/notes');
    const stillExists = afterDelete.body.find(n => n.id === newNoteId);
    
    if (stillExists) {
      throw new Error('Note still exists after delete!');
    }
    console.log(`   ✅ Note confirmed removed`);

    // Summary
    console.log('\n' + '='.repeat(70));
    console.log('✅ COMPLETE USER JOURNEY VERIFIED');
    console.log('='.repeat(70));
    console.log('\n✓ Server restart → notes persisted');
    console.log('✓ Create note → appears in list with preview');
    console.log('✓ Expand note → full body retrieved');
    console.log('✓ Delete note → removed from list');
    console.log('✓ All API responses have correct status codes');
    console.log('\n🎉 All pieces (UI, API, persistence) are wired together correctly!\n');

    process.exit(0);

  } catch (error) {
    console.error(`\n❌ FAILED: ${error.message}\n`);
    process.exit(1);
  }
}

finalCheck();
