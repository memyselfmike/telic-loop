// Modal - Book form and detail modals (IIFE pattern)
(function() {
  const modalContainer = document.getElementById('modalContainer');

  function closeModal() {
    modalContainer.innerHTML = '';
  }

  function renderStars(rating, interactive = false) {
    if (!interactive) {
      if (!rating) return '<span class="star-rating"></span>';
      let stars = '<span class="star-rating">';
      for (let i = 1; i <= 5; i++) {
        stars += `<span class="star ${i <= rating ? 'filled' : ''}">★</span>`;
      }
      stars += '</span>';
      return stars;
    }

    let stars = '<div class="star-rating interactive" id="ratingInput">';
    for (let i = 1; i <= 5; i++) {
      stars += `<span class="star ${rating && i <= rating ? 'filled' : ''}" data-rating="${i}">★</span>`;
    }
    stars += '</div>';
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

  function openFormModal(book = null) {
    const isEdit = !!book;
    const title = isEdit ? 'Edit Book' : 'Add Book';

    const html = `
      <div class="modal-overlay">
        <div class="modal">
          <div class="modal-header">
            <h2 class="modal-title">${title}</h2>
            <button class="modal-close" id="closeModal">&times;</button>
          </div>
          <div class="modal-body">
            <form id="bookForm">
              <div class="form-group">
                <label class="form-label required" for="titleInput">Title</label>
                <input type="text" id="titleInput" required value="${book?.title || ''}">
              </div>

              <div class="form-group">
                <label class="form-label required" for="authorInput">Author</label>
                <input type="text" id="authorInput" required value="${book?.author || ''}">
              </div>

              <div class="form-group">
                <label class="form-label" for="genreInput">Genre</label>
                <input type="text" id="genreInput" value="${book?.genre || ''}">
              </div>

              <div class="form-group">
                <label class="form-label" for="coverUrlInput">Cover URL</label>
                <input type="url" id="coverUrlInput" value="${book?.cover_url || ''}">
                <div class="cover-preview" id="coverPreview">
                  ${book?.cover_url ? `<img src="${book.cover_url}" alt="Cover preview">` : '📚'}
                </div>
              </div>

              <div class="form-group">
                <label class="form-label" for="statusInput">Status</label>
                <select id="statusInput">
                  <option value="want_to_read" ${book?.status === 'want_to_read' ? 'selected' : ''}>Want to Read</option>
                  <option value="reading" ${book?.status === 'reading' ? 'selected' : ''}>Reading</option>
                  <option value="finished" ${book?.status === 'finished' ? 'selected' : ''}>Finished</option>
                  <option value="abandoned" ${book?.status === 'abandoned' ? 'selected' : ''}>Abandoned</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label">Rating</label>
                ${renderStars(book?.rating, true)}
                <input type="hidden" id="ratingValue" value="${book?.rating || ''}">
              </div>

              <div class="form-group">
                <label class="form-label" for="notesInput">Notes</label>
                <textarea id="notesInput" rows="4">${book?.notes || ''}</textarea>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" id="cancelBtn">Cancel</button>
            <button class="btn btn-primary" id="submitBtn">${isEdit ? 'Save Changes' : 'Add Book'}</button>
          </div>
        </div>
      </div>
    `;

    modalContainer.innerHTML = html;

    // Event listeners
    document.getElementById('closeModal').addEventListener('click', closeModal);
    document.getElementById('cancelBtn').addEventListener('click', closeModal);

    // Cover URL preview
    const coverUrlInput = document.getElementById('coverUrlInput');
    const coverPreview = document.getElementById('coverPreview');

    coverUrlInput.addEventListener('input', () => {
      const url = coverUrlInput.value.trim();
      if (url) {
        coverPreview.innerHTML = `<img src="${url}" alt="Cover preview" onerror="this.parentElement.innerHTML='📚'">`;
      } else {
        coverPreview.innerHTML = '📚';
      }
    });

    // Rating stars
    const ratingInput = document.getElementById('ratingInput');
    const ratingValue = document.getElementById('ratingValue');

    ratingInput.querySelectorAll('.star').forEach(star => {
      star.addEventListener('click', () => {
        const rating = parseInt(star.dataset.rating);
        ratingValue.value = rating;

        ratingInput.querySelectorAll('.star').forEach((s, idx) => {
          if (idx < rating) {
            s.classList.add('filled');
          } else {
            s.classList.remove('filled');
          }
        });
      });
    });

    // Form submission
    document.getElementById('submitBtn').addEventListener('click', async () => {
      const form = document.getElementById('bookForm');
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }

      const data = {
        title: document.getElementById('titleInput').value.trim(),
        author: document.getElementById('authorInput').value.trim(),
        genre: document.getElementById('genreInput').value.trim() || null,
        cover_url: document.getElementById('coverUrlInput').value.trim() || null,
        status: document.getElementById('statusInput').value,
        rating: ratingValue.value ? parseInt(ratingValue.value) : null,
        notes: document.getElementById('notesInput').value.trim() || null
      };

      try {
        if (isEdit) {
          await window.BookAPI.updateBook(book.id, data);
          window.Toast.success('Book updated successfully!');
        } else {
          await window.BookAPI.createBook(data);
          window.Toast.success('Book added successfully!');
        }

        closeModal();
        window.Library.refresh();
      } catch (error) {
        window.Toast.error('Failed to save book: ' + error.message);
      }
    });

    // Close on overlay click
    modalContainer.querySelector('.modal-overlay').addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-overlay')) {
        closeModal();
      }
    });
  }

  function openDetailModal(book) {
    const coverHtml = book.cover_url
      ? `<img src="${book.cover_url}" alt="${book.title}">`
      : '📚';

    const html = `
      <div class="modal-overlay">
        <div class="modal">
          <div class="modal-header">
            <h2 class="modal-title">Book Details</h2>
            <button class="modal-close" id="closeModal">&times;</button>
          </div>
          <div class="modal-body">
            <div class="book-detail">
              <div class="book-detail-header">
                <div class="book-detail-cover">${coverHtml}</div>
                <div class="book-detail-info">
                  <h2>${book.title}</h2>
                  <p class="book-detail-author">by ${book.author}</p>
                  <div class="book-detail-meta">
                    <span class="status-badge ${book.status}">${formatStatus(book.status)}</span>
                    ${book.genre ? `<span><strong>Genre:</strong> ${book.genre}</span>` : ''}
                    ${book.rating ? `<div>${renderStars(book.rating)}</div>` : ''}
                  </div>
                </div>
              </div>
              ${book.notes ? `
                <div class="book-detail-notes">
                  <h3>Notes</h3>
                  <p>${book.notes}</p>
                </div>
              ` : ''}
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-danger" id="deleteBtn">Delete</button>
            <button class="btn btn-primary" id="editBtn">Edit</button>
          </div>
        </div>
      </div>
    `;

    modalContainer.innerHTML = html;

    // Event listeners
    document.getElementById('closeModal').addEventListener('click', closeModal);

    document.getElementById('editBtn').addEventListener('click', () => {
      closeModal();
      openFormModal(book);
    });

    document.getElementById('deleteBtn').addEventListener('click', () => {
      if (confirm(`Are you sure you want to delete "${book.title}"?`)) {
        deleteBook(book.id);
      }
    });

    // Close on overlay click
    modalContainer.querySelector('.modal-overlay').addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-overlay')) {
        closeModal();
      }
    });
  }

  async function deleteBook(bookId) {
    try {
      await window.BookAPI.deleteBook(bookId);
      window.Toast.success('Book deleted successfully!');
      closeModal();
      window.Library.refresh();
    } catch (error) {
      window.Toast.error('Failed to delete book: ' + error.message);
    }
  }

  // Public API
  window.Modal = {
    openAdd: function() {
      openFormModal();
    },

    openEdit: function(book) {
      openFormModal(book);
    },

    openDetail: function(book) {
      openDetailModal(book);
    },

    close: closeModal
  };
})();
