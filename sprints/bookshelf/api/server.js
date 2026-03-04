const express = require('express');
const cors = require('cors');
const db = require('./db');
const search = require('./search');
const booksRouter = require('./routes/books');
const searchRouter = require('./routes/search');
const statsRouter = require('./routes/stats');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/', async (req, res) => {
  try {
    // Test database connection
    await db.query('SELECT 1');
    res.json({ status: 'ok' });
  } catch (error) {
    console.error('Health check failed:', error);
    res.status(503).json({ status: 'error', message: 'Database connection failed' });
  }
});

// API routes
app.use('/api/books', booksRouter);
app.use('/api/search', searchRouter);
app.use('/api/stats', statsRouter);

// Initialize search on startup
async function initializeServices() {
  try {
    // Wait for database to be ready
    await db.query('SELECT 1');
    console.log('[Database] Connected successfully');

    // Initialize MeiliSearch
    await search.init();
    console.log('[MeiliSearch] Initialized successfully');
  } catch (error) {
    console.error('Service initialization error:', error);
    process.exit(1);
  }
}

// Start server
app.listen(PORT, async () => {
  console.log(`Bookshelf API server listening on port ${PORT}`);
  await initializeServices();
});

// Handle shutdown gracefully
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing database pool...');
  await db.end();
  process.exit(0);
});
