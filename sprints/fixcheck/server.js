const express = require('express');
const path = require('path');
const app = express();
const PORT = 3000;

// Middleware
app.use(express.json());

// API Routes
const notesRouter = require('./routes/notes');
app.use('/api/notes', notesRouter);

// Serve static files from public/ directory with extension fallback
// This allows / to resolve to index.html and /stats to resolve to stats.html
app.use(express.static(path.join(__dirname, 'public'), {
  extensions: ['html']
}));

// Export app for testing (Supertest compatibility)
module.exports = app;

// Only start server when run directly (not when required by tests)
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`NoteBox server listening on port ${PORT}`);
  });
}
