// Library - Book grid display module (IIFE pattern)
(function() {
  let currentFilter = 'all';
  let books = [];
  let isLoading = false;

  const bookGrid = document.getElementById('bookGrid');
  const filterTabs = document.querySelectorAll('.filter-tab');

  function renderStars(rating) {
    if (!rating) {
      return '<span class="star-rating"></span>';
    }

    let stars = '<span class="star-rating">';
    for (let i = 1; i <= 5; i++) {
      stars += `<span class="star ${i <= rating ? 'filled' : ''}">★</span>`;
    }
    stars += '</span>';
    return stars;
  }

  function renderBookCard(book) {
    const coverHtml = book.cover_url
      ? `<img src="${book.cover_url}" alt="${book.title}" onerror="this.style.display='none'; this.parentElement.innerHTML='📚'">`
      : '📚';

    return `
      <div class="book-card" data-book-id="${book.id}" tabindex="0">
        <div class="book-cover">
          ${coverHtml}
        </div>
        <div class="book-info">
          <h3 class="book-title">${book.title}</h3>
          <p class="book-author">${book.author}</p>
          <div class="book-meta">
            <span class="status-badge ${book.status}">${formatStatus(book.status)}</span>
            ${renderStars(book.rating)}
          </div>
        </div>
      </div>
    `;
  }

  function formatStatus(status) {
    const statusMap = {
      'want_to_read': 'Want to Read',
      'reading': 'Reading',
      'finished': 'Finished',
      'abandoned': 'Abandoned'
    };
    return statusMap[status] || status;
  }

  function renderLoadingSkeleton() {
    const skeletons = Array.from({ length: 8 }, () => `
      <div class="skeleton-card">
        <div class="skeleton-cover skeleton"></div>
        <div class="skeleton-info">
          <div class="skeleton-title skeleton"></div>
          <div class="skeleton-author skeleton"></div>
          <div class="skeleton-meta skeleton"></div>
        </div>
      </div>
    `).join('');

    bookGrid.innerHTML = skeletons;
  }

  function renderEmptyState(message = 'No books found') {
    bookGrid.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📚</div>
        <h3 class="empty-state-title">${message}</h3>
        <p class="empty-state-message">
          ${message === 'No books found' ? 'Try adjusting your filters or add your first book!' : ''}
        </p>
      </div>
    `;
  }

  function renderBooks(booksToRender) {
    if (!booksToRender || booksToRender.length === 0) {
      renderEmptyState();
      return;
    }

    bookGrid.innerHTML = booksToRender.map(renderBookCard).join('');

    // Attach click handlers
    bookGrid.querySelectorAll('.book-card').forEach(card => {
      card.addEventListener('click', () => {
        const bookId = card.dataset.bookId;
        const book = books.find(b => b.id === bookId);
        if (book && window.Modal) {
          window.Modal.openDetail(book);
        }
      });

      card.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          card.click();
        }
      });
    });
  }

  async function fetchAndRender(status = null) {
    if (isLoading) return;

    isLoading = true;
    renderLoadingSkeleton();

    try {
      books = await window.BookAPI.getBooks(status);
      renderBooks(books);
    } catch (error) {
      console.error('Failed to load books:', error);
      bookGrid.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">⚠️</div>
          <h3 class="empty-state-title">Failed to load books</h3>
          <p class="empty-state-message">${error.message}</p>
        </div>
      `;
    } finally {
      isLoading = false;
    }
  }

  // Filter tab handlers
  filterTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const status = tab.dataset.status;

      // Update active tab
      filterTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      // Fetch filtered books
      currentFilter = status;
      const filterStatus = status === 'all' ? null : status;
      fetchAndRender(filterStatus);
    });
  });

  // Public API
  window.Library = {
    init: function() {
      fetchAndRender();
    },

    refresh: function() {
      const filterStatus = currentFilter === 'all' ? null : currentFilter;
      fetchAndRender(filterStatus);
    },

    renderBooks: renderBooks
  };
})();
