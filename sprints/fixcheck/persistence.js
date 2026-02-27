const fs = require('fs');
const path = require('path');

const NOTES_FILE = path.join(__dirname, 'data', 'notes.json');

/**
 * Read all notes from the JSON file.
 * Returns an empty array if the file does not exist or is empty.
 * @returns {Array} Array of note objects
 */
function readNotes() {
  try {
    // Check if file exists
    if (!fs.existsSync(NOTES_FILE)) {
      return [];
    }

    const fileContent = fs.readFileSync(NOTES_FILE, 'utf-8');

    // Handle empty file
    if (!fileContent || fileContent.trim() === '') {
      return [];
    }

    const notes = JSON.parse(fileContent);

    // Ensure we return an array
    if (!Array.isArray(notes)) {
      return [];
    }

    return notes;
  } catch (error) {
    // Log error but return empty array to maintain resilience
    console.error('Error reading notes:', error.message);
    return [];
  }
}

/**
 * Write notes array to the JSON file atomically.
 * Creates the data directory if it doesn't exist.
 * @param {Array} notes - Array of note objects to persist
 */
function writeNotes(notes) {
  try {
    // Ensure data directory exists
    const dataDir = path.dirname(NOTES_FILE);
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }

    // Serialize with pretty formatting for human readability
    const jsonContent = JSON.stringify(notes, null, 2);

    // Write atomically: write to temp file first, then rename
    const tempFile = `${NOTES_FILE}.tmp`;
    fs.writeFileSync(tempFile, jsonContent, 'utf-8');
    fs.renameSync(tempFile, NOTES_FILE);

  } catch (error) {
    console.error('Error writing notes:', error.message);
    throw error; // Re-throw to let caller handle persistence failures
  }
}

module.exports = {
  readNotes,
  writeNotes
};
