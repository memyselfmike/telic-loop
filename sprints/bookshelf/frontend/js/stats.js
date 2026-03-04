// Stats - Reading statistics dashboard (IIFE pattern)
(function() {
  const statsView = document.getElementById('statsView');
  const statsContent = document.getElementById('statsContent');

  function renderStars(rating) {
    let stars = '<span class="star-rating">';
    const fullStars = Math.floor(rating);
    for (let i = 1; i <= 5; i++) {
      stars += `<span class="star ${i <= fullStars ? 'filled' : ''}">★</span>`;
    }
    stars += '</span>';
    return stars;
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

  async function renderStats() {
    try {
      const data = await window.BookAPI.getStats();

      // Build status cards
      const statusCards = [
        { status: 'want_to_read', label: 'Want to Read', count: 0 },
        { status: 'reading', label: 'Reading', count: 0 },
        { status: 'finished', label: 'Finished', count: 0 },
        { status: 'abandoned', label: 'Abandoned', count: 0 }
      ];

      // Map counts from API response
      data.books_by_status.forEach(item => {
        const card = statusCards.find(c => c.status === item.status);
        if (card) card.count = item.count;
      });

      const statusCardsHtml = statusCards.map(card => `
        <div class="stat-card status-card ${card.status}">
          <div class="stat-label">${card.label}</div>
          <div class="stat-value">${card.count}</div>
        </div>
      `).join('');

      // Genre chart
      let genreChartHtml = '';
      if (data.genres && data.genres.length > 0) {
        const maxCount = Math.max(...data.genres.map(g => g.count));

        genreChartHtml = `
          <div class="stat-card" style="grid-column: 1 / -1;">
            <div class="stat-label">Genre Distribution</div>
            <div class="genre-chart">
              ${data.genres.slice(0, 5).map(genre => {
                const percentage = (genre.count / maxCount) * 100;
                return `
                  <div class="genre-item">
                    <div class="genre-label">
                      <span class="genre-name">${genre.genre}</span>
                      <span class="genre-count">${genre.count} book${genre.count !== 1 ? 's' : ''}</span>
                    </div>
                    <div class="genre-bar-container">
                      <div class="genre-bar" style="width: ${percentage}%"></div>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>
        `;
      }

      // Average rating card
      const avgRatingHtml = data.average_rating ? `
        <div class="stat-card">
          <div class="stat-label">Average Rating</div>
          <div class="rating-display">
            ${renderStars(data.average_rating)}
            <span class="rating-number">${data.average_rating}</span>
          </div>
        </div>
      ` : `
        <div class="stat-card">
          <div class="stat-label">Average Rating</div>
          <div class="stat-value" style="font-size: 1.5rem; color: var(--color-text-secondary);">N/A</div>
        </div>
      `;

      const html = `
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">Total Books</div>
            <div class="stat-value">${data.total_books}</div>
          </div>

          ${statusCardsHtml}
          ${avgRatingHtml}
          ${genreChartHtml}
        </div>
      `;

      statsContent.innerHTML = html;
    } catch (error) {
      console.error('Failed to load stats:', error);
      statsContent.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">⚠️</div>
          <h3 class="empty-state-title">Failed to load statistics</h3>
          <p class="empty-state-message">${error.message}</p>
        </div>
      `;
    }
  }

  // Public API
  window.Stats = {
    show: async function() {
      statsView.style.display = 'block';
      await renderStats();
    },

    hide: function() {
      statsView.style.display = 'none';
    },

    refresh: function() {
      if (statsView.style.display === 'block') {
        renderStats();
      }
    }
  };
})();
