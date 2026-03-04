// Search - Book search module (IIFE pattern)
(function() {
  const searchInput = document.getElementById('searchInput');
  let debounceTimer;
  let isSearchActive = false;

  function debounce(func, delay) {
    return function(...args) {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => func.apply(this, args), delay);
    };
  }

  async function performSearch(query) {
    if (!query || query.trim() === '') {
      clearSearch();
      return;
    }

    isSearchActive = true;
    searchInput.classList.add('active');

    try {
      const results = await window.BookAPI.searchBooks(query);

      if (results.length === 0) {
        const bookGrid = document.getElementById('bookGrid');
        bookGrid.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">🔍</div>
            <h3 class="empty-state-title">No results found</h3>
            <p class="empty-state-message">Try searching with different keywords</p>
          </div>
        `;
      } else {
        window.Library.renderBooks(results);
      }
    } catch (error) {
      console.error('Search failed:', error);
      window.Toast.error('Search failed: ' + error.message);
    }
  }

  function clearSearch() {
    isSearchActive = false;
    searchInput.classList.remove('active');
    window.Library.refresh();
  }

  // Debounced search handler
  const debouncedSearch = debounce(performSearch, 300);

  // Event listeners
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    if (query === '') {
      clearSearch();
    } else {
      debouncedSearch(query);
    }
  });

  // Clear search on Escape key
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      searchInput.value = '';
      clearSearch();
    }
  });

  // Public API
  window.Search = {
    clear: function() {
      searchInput.value = '';
      clearSearch();
    },

    isActive: function() {
      return isSearchActive;
    }
  };
})();
