/**
 * Recipe Manager - Main Application Entry Point
 * Handles SPA routing, navigation, shared state, and utilities
 */

import { showToast } from './ui.js';

// ===== Shared Application State =====
export const appState = {
  currentWeek: getMondayOfCurrentWeek(), // ISO date string (YYYY-MM-DD)
  currentView: 'recipes'
};

// ===== API Helper =====
const API_BASE = '/api';

/**
 * Fetch wrapper with error handling and JSON parsing
 * @param {string} endpoint - API endpoint (e.g., '/recipes')
 * @param {object} options - Fetch options
 * @returns {Promise<any>} Parsed JSON response
 */
export async function apiCall(endpoint, options = {}) {
  try {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    // Handle non-JSON error responses
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch (e) {
        // Response wasn't JSON, use status text
      }
      throw new Error(errorMessage);
    }

    // Parse JSON response
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API call failed:', endpoint, error);
    showToast(error.message || 'Request failed', 'error');
    throw error;
  }
}

// ===== Utility Functions =====

/**
 * Format time in minutes to human-readable string
 * @param {number} minutes - Time in minutes
 * @returns {string} Formatted time (e.g., "1h 30m", "45m")
 */
export function formatTime(minutes) {
  if (!minutes || minutes === 0) return '0m';
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours > 0 && mins > 0) {
    return `${hours}h ${mins}m`;
  } else if (hours > 0) {
    return `${hours}h`;
  } else {
    return `${mins}m`;
  }
}

/**
 * Format ISO date to human-readable string
 * @param {string} isoDate - ISO date string (YYYY-MM-DD)
 * @returns {string} Formatted date (e.g., "Mon, Jan 15")
 */
export function formatDate(isoDate) {
  const date = new Date(isoDate + 'T00:00:00');
  const options = { weekday: 'short', month: 'short', day: 'numeric' };
  return date.toLocaleDateString('en-US', options);
}

/**
 * Get the Monday of the current week
 * @returns {string} ISO date string (YYYY-MM-DD)
 */
export function getMondayOfCurrentWeek() {
  const today = new Date();
  const dayOfWeek = today.getDay(); // 0 = Sunday, 1 = Monday, ...
  const diff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // Adjust to Monday
  const monday = new Date(today);
  monday.setDate(today.getDate() + diff);
  return monday.toISOString().split('T')[0];
}

/**
 * Get Monday of a given week offset from current week
 * @param {number} weekOffset - Offset from current week (-1 = previous, 1 = next)
 * @returns {string} ISO date string (YYYY-MM-DD)
 */
export function getMondayOfWeek(weekOffset = 0) {
  const current = new Date(appState.currentWeek + 'T00:00:00');
  current.setDate(current.getDate() + (weekOffset * 7));
  return current.toISOString().split('T')[0];
}

/**
 * Debounce function to limit function call frequency
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, delay = 300) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

/**
 * Parse tags string into array
 * @param {string} tagsString - Comma-separated tags
 * @returns {string[]} Array of trimmed tags
 */
export function parseTags(tagsString) {
  if (!tagsString || tagsString.trim() === '') return [];
  return tagsString.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
}

/**
 * Format tags array to comma-separated string
 * @param {string[]} tagsArray - Array of tags
 * @returns {string} Comma-separated tags
 */
export function formatTagsString(tagsArray) {
  if (!tagsArray || tagsArray.length === 0) return '';
  return tagsArray.join(', ');
}

// ===== SPA Router =====

const routes = {
  recipes: null, // Will be lazy-loaded
  planner: null,
  shopping: null
};

/**
 * Navigate to a specific view
 * @param {string} viewName - View name ('recipes', 'planner', 'shopping')
 */
export async function navigateTo(viewName) {
  // Update hash without triggering hashchange event
  if (window.location.hash !== `#${viewName}`) {
    window.location.hash = viewName;
  }

  // Update active tab in nav
  document.querySelectorAll('.nav-tab').forEach(tab => {
    if (tab.dataset.view === viewName) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });

  // Update state
  appState.currentView = viewName;

  // Load view module if not already loaded
  if (!routes[viewName]) {
    try {
      const module = await import(`./${viewName}.js`);
      routes[viewName] = module;
    } catch (error) {
      console.error(`Failed to load view: ${viewName}`, error);
      showToast(`Failed to load ${viewName} view`, 'error');
      return;
    }
  }

  // Render the view
  const contentArea = document.getElementById('app-content');
  contentArea.innerHTML = ''; // Clear previous content

  if (routes[viewName] && routes[viewName].render) {
    await routes[viewName].render(contentArea);
  }
}

/**
 * Handle hash change events
 */
function handleHashChange() {
  const hash = window.location.hash.slice(1); // Remove '#'
  const viewName = hash || 'recipes'; // Default to recipes

  if (routes.hasOwnProperty(viewName)) {
    navigateTo(viewName);
  } else {
    // Unknown route, redirect to recipes
    window.location.hash = 'recipes';
  }
}

// ===== Initialization =====

/**
 * Initialize the application
 */
function init() {
  // Set up navigation click handlers
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      const viewName = tab.dataset.view;
      navigateTo(viewName);
    });
  });

  // Set up hash change listener
  window.addEventListener('hashchange', handleHashChange);

  // Initial route
  handleHashChange();
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
