// Hash-based color function for tag pills (matches main page implementation)
function hashTagColor(tag) {
  let hash = 0;
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash; // Convert to 32-bit integer
  }

  const colors = [
    'rgb(59, 130, 246)',  // blue
    'rgb(16, 185, 129)',  // green
    'rgb(249, 115, 22)',  // orange
    'rgb(168, 85, 247)',  // purple
    'rgb(236, 72, 153)',  // pink
    'rgb(234, 179, 8)',   // yellow
    'rgb(20, 184, 166)',  // teal
    'rgb(244, 63, 94)'    // red
  ];

  const index = Math.abs(hash) % colors.length;
  return colors[index];
}

// Fetch stats from API and render dashboard
async function loadDashboard() {
  try {
    const response = await fetch('/api/stats');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();

    // Render stats cards
    renderStatsCards(data);

    // Render tag distribution bar chart
    renderTagChart(data.tag_counts);

    // Render recent links
    renderRecentLinks(data.recent);

  } catch (error) {
    console.error('Failed to load dashboard:', error);
    showError('Failed to load dashboard data. Please try again.');
  }
}

// Render the three stat cards
function renderStatsCards(data) {
  const totalLinksEl = document.getElementById('total-links');
  const totalTagsEl = document.getElementById('total-tags');
  const mostUsedTagEl = document.getElementById('most-used-tag');

  // Display total links
  totalLinksEl.textContent = data.total_links || 0;

  // Display total tags
  totalTagsEl.textContent = data.total_tags || 0;

  // Display most used tag
  const tagCounts = data.tag_counts || {};
  const tagEntries = Object.entries(tagCounts);

  if (tagEntries.length === 0) {
    mostUsedTagEl.textContent = 'None';
  } else {
    const mostUsed = tagEntries.sort((a, b) => b[1] - a[1])[0];
    mostUsedTagEl.textContent = `${mostUsed[0]} (${mostUsed[1]})`;
  }
}

// Create a single bar row element for the tag chart
function createChartBarRow(tag, count, maxCount) {
  const barRow = document.createElement('div');
  barRow.className = 'chart-bar-row';

  // Tag label
  const label = document.createElement('div');
  label.className = 'chart-label';
  label.textContent = tag;
  barRow.appendChild(label);

  // Bar container (for the colored bar)
  const barContainer = document.createElement('div');
  barContainer.className = 'chart-bar-container';

  const bar = document.createElement('div');
  bar.className = 'chart-bar';

  // Calculate width as percentage of max count
  const widthPercent = (count / maxCount) * 100;
  bar.style.width = `${widthPercent}%`;

  // Apply the same hash-based color as tag pills
  bar.style.backgroundColor = hashTagColor(tag);

  barContainer.appendChild(bar);
  barRow.appendChild(barContainer);

  // Count label
  const countLabel = document.createElement('div');
  countLabel.className = 'chart-count';
  countLabel.textContent = count;
  barRow.appendChild(countLabel);

  return barRow;
}

// Render horizontal bar chart for tag distribution
function renderTagChart(tagCounts) {
  const container = document.getElementById('chart-container');
  container.innerHTML = ''; // Clear existing content

  const tagEntries = Object.entries(tagCounts || {});

  // Handle empty state
  if (tagEntries.length === 0) {
    container.innerHTML = '<p class="empty-state">No tags yet. Add some bookmarks to see your tag distribution!</p>';
    return;
  }

  // Sort tags by count (descending)
  tagEntries.sort((a, b) => b[1] - a[1]);

  // Find max count for proportional bar widths
  const maxCount = tagEntries[0][1];

  // Create bar for each tag
  const chartBars = document.createElement('div');
  chartBars.className = 'chart-bars';

  tagEntries.forEach(([tag, count]) => {
    const barRow = createChartBarRow(tag, count, maxCount);
    chartBars.appendChild(barRow);
  });

  container.appendChild(chartBars);
}

// Render recent links list
function renderRecentLinks(recent) {
  const container = document.getElementById('recent-container');
  container.innerHTML = ''; // Clear existing content

  if (!recent || recent.length === 0) {
    container.innerHTML = '<p class="empty-state">No recent links yet.</p>';
    return;
  }

  const linksList = document.createElement('ul');
  linksList.className = 'recent-links-list';

  recent.forEach(link => {
    const li = document.createElement('li');
    li.className = 'recent-link-item';

    const title = document.createElement('a');
    title.href = link.url || '#';
    title.textContent = link.title;
    title.target = '_blank';
    title.rel = 'noopener noreferrer';
    title.className = 'recent-link-title';

    const date = document.createElement('span');
    date.className = 'recent-link-date';
    date.textContent = new Date(link.created_at).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });

    li.appendChild(title);
    li.appendChild(date);
    linksList.appendChild(li);
  });

  container.appendChild(linksList);
}

// Show error message to user
function showError(message) {
  const main = document.querySelector('main');
  const errorDiv = document.createElement('div');
  errorDiv.className = 'error-message';
  errorDiv.textContent = message;
  main.prepend(errorDiv);
}

// Load dashboard when page loads
document.addEventListener('DOMContentLoaded', loadDashboard);
