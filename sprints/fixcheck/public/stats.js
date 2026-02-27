// Stats Dashboard Client-Side Logic

/**
 * Fetches stats from the API and renders the dashboard
 */
async function loadStats() {
  const dashboard = document.getElementById('stats-dashboard');

  try {
    const response = await fetch('/api/stats');

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const stats = await response.json();
    renderStatsDashboard(stats);
  } catch (error) {
    dashboard.innerHTML = `<div class="error">Failed to load statistics. Please try again later.</div>`;
    console.error('Error loading stats:', error);
  }
}

/**
 * Renders the stats dashboard with four stat cards
 */
function renderStatsDashboard(stats) {
  const dashboard = document.getElementById('stats-dashboard');

  // Format dates for display (or show "N/A" if null)
  const newestDateFormatted = stats.newestDate
    ? new Date(stats.newestDate).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    : 'N/A';

  const oldestDateFormatted = stats.oldestDate
    ? new Date(stats.oldestDate).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    : 'N/A';

  dashboard.innerHTML = `
    <div class="stat-card">
      <div class="stat-label">Total Notes</div>
      <div class="stat-value">${stats.totalNotes}</div>
    </div>

    <div class="stat-card">
      <div class="stat-label">Average Body Length</div>
      <div class="stat-value">${stats.averageBodyLength}</div>
      <div class="stat-unit">characters</div>
    </div>

    <div class="stat-card">
      <div class="stat-label">Newest Note</div>
      <div class="stat-value stat-date">${newestDateFormatted}</div>
    </div>

    <div class="stat-card">
      <div class="stat-label">Oldest Note</div>
      <div class="stat-value stat-date">${oldestDateFormatted}</div>
    </div>
  `;
}

// Load stats when the page loads
document.addEventListener('DOMContentLoaded', loadStats);
