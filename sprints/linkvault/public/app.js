// State
let allLinks = [];
let activeFilter = null;

// Color palette for tags (deterministic hash-based color assignment)
const TAG_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
  '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
  '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
  '#ec4899', '#f43f5e'
];

// Hash function to deterministically assign color to tag
function getTagColor(tag) {
  let hash = 0;
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash);
  }
  return TAG_COLORS[Math.abs(hash) % TAG_COLORS.length];
}

// DOM elements
const addLinkForm = document.getElementById('addLinkForm');
const linksGrid = document.getElementById('linksGrid');
const emptyState = document.getElementById('emptyState');
const errorMessage = document.getElementById('errorMessage');
const tagFilter = document.getElementById('tagFilter');
const tagFilterPills = document.getElementById('tagFilterPills');

// Show error message
function showError(message) {
  errorMessage.textContent = message;
  errorMessage.classList.add('show');
  setTimeout(() => {
    errorMessage.classList.remove('show');
  }, 5000);
}

// Create a tag pill element
function createTagPill(tag, isClickable = false) {
  const pill = document.createElement('span');
  pill.className = 'tag-pill';
  pill.textContent = tag;
  pill.style.backgroundColor = getTagColor(tag);
  pill.style.color = 'white';

  if (isClickable) {
    pill.addEventListener('click', () => toggleFilter(tag));
    if (activeFilter === tag) {
      pill.classList.add('active');
    }
  }

  return pill;
}

// Toggle tag filter
function toggleFilter(tag) {
  if (activeFilter === tag) {
    activeFilter = null;
  } else {
    activeFilter = tag;
  }
  renderLinks();
  renderTagFilter();
}

// Create a link card element
function createLinkCard(link) {
  const card = document.createElement('div');
  card.className = 'link-card';
  card.dataset.id = link.id;

  // Title (linked)
  const title = document.createElement('h3');
  const titleLink = document.createElement('a');
  titleLink.href = link.url;
  titleLink.textContent = link.title;
  titleLink.target = '_blank';
  titleLink.rel = 'noopener noreferrer';
  title.appendChild(titleLink);

  // URL (truncated)
  const url = document.createElement('div');
  url.className = 'link-url';
  url.textContent = link.url;

  // Tags
  const tagsContainer = document.createElement('div');
  tagsContainer.className = 'link-tags';
  if (link.tags && link.tags.length > 0) {
    link.tags.forEach(tag => {
      tagsContainer.appendChild(createTagPill(tag, false));
    });
  }

  // Delete button
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'delete-btn';
  deleteBtn.textContent = 'Delete';
  deleteBtn.addEventListener('click', () => deleteLink(link.id));

  card.appendChild(title);
  card.appendChild(url);
  card.appendChild(tagsContainer);
  card.appendChild(deleteBtn);

  return card;
}

// Render tag filter pills
function renderTagFilter() {
  // Collect all unique tags
  const allTags = new Set();
  allLinks.forEach(link => {
    if (link.tags && link.tags.length > 0) {
      link.tags.forEach(tag => allTags.add(tag));
    }
  });

  if (allTags.size === 0) {
    tagFilter.style.display = 'none';
    return;
  }

  tagFilter.style.display = 'block';
  tagFilterPills.innerHTML = '';

  // Sort tags alphabetically
  const sortedTags = Array.from(allTags).sort();
  sortedTags.forEach(tag => {
    const pill = createTagPill(tag, true);
    tagFilterPills.appendChild(pill);
  });
}

// Render links grid
function renderLinks() {
  // Filter links if a tag filter is active
  const linksToDisplay = activeFilter
    ? allLinks.filter(link => link.tags && link.tags.includes(activeFilter))
    : allLinks;

  // Show empty state if no links
  if (linksToDisplay.length === 0) {
    linksGrid.innerHTML = '';
    emptyState.style.display = 'block';
    if (activeFilter) {
      emptyState.querySelector('h3').textContent = 'No bookmarks with this tag';
      emptyState.querySelector('p').textContent = `No bookmarks found with tag "${activeFilter}"`;
    } else {
      emptyState.querySelector('h3').textContent = 'No bookmarks yet';
      emptyState.querySelector('p').textContent = 'Start by adding your first bookmark using the form above!';
    }
    return;
  }

  emptyState.style.display = 'none';
  linksGrid.innerHTML = '';

  // Render cards (most recent first)
  linksToDisplay.forEach(link => {
    const card = createLinkCard(link);
    linksGrid.appendChild(card);
  });
}

// Fetch all links from API
async function fetchLinks() {
  try {
    const response = await fetch('/api/links');
    if (!response.ok) {
      throw new Error('Failed to fetch links');
    }
    const data = await response.json();
    allLinks = data.links || [];
    // Sort by created_at descending (most recent first)
    allLinks.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    renderLinks();
    renderTagFilter();
  } catch (error) {
    console.error('Error fetching links:', error);
    showError('Failed to load bookmarks. Please refresh the page.');
  }
}

// Add a new link
async function addLink(title, url, tags) {
  try {
    const response = await fetch('/api/links', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ title, url, tags })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to add bookmark');
    }

    const newLink = await response.json();

    // Prepend to allLinks array (most recent first)
    allLinks.unshift(newLink);

    // Re-render
    renderLinks();
    renderTagFilter();

    // Clear form
    addLinkForm.reset();

  } catch (error) {
    console.error('Error adding link:', error);
    showError(error.message);
  }
}

// Delete a link
async function deleteLink(id) {
  if (!confirm('Are you sure you want to delete this bookmark?')) {
    return;
  }

  try {
    const response = await fetch(`/api/links/${id}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error('Failed to delete bookmark');
    }

    // Remove from allLinks array
    allLinks = allLinks.filter(link => link.id !== id);

    // Re-render
    renderLinks();
    renderTagFilter();

  } catch (error) {
    console.error('Error deleting link:', error);
    showError('Failed to delete bookmark. Please try again.');
  }
}

// Handle form submission
addLinkForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const title = document.getElementById('title').value.trim();
  const url = document.getElementById('url').value.trim();
  const tagsInput = document.getElementById('tags').value.trim();

  // Validate title
  if (!title) {
    showError('Title is required');
    return;
  }

  // Validate URL
  if (!url) {
    showError('URL is required');
    return;
  }
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    showError('URL must start with http:// or https://');
    return;
  }

  // Parse tags (comma-separated)
  let tags = [];
  if (tagsInput) {
    tags = tagsInput
      .split(',')
      .map(tag => tag.trim().toLowerCase())
      .filter(tag => tag !== '');

    if (tags.length > 5) {
      showError('Maximum 5 tags allowed');
      return;
    }
  }

  await addLink(title, url, tags);
});

// Initialize on page load
fetchLinks();
