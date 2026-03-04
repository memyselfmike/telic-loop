// BookAPI - API client module (IIFE pattern)
(function() {
  const BASE_URL = '/api';

  async function request(endpoint, options = {}) {
    try {
      const response = await fetch(`${BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        let errorMessage = `Request failed: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch (e) {
          // Ignore JSON parse error
        }
        throw new Error(errorMessage);
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return null;
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }

  window.BookAPI = {
    // Get all books or filter by status
    getBooks: function(status) {
      const url = status ? `/books?status=${encodeURIComponent(status)}` : '/books';
      return request(url);
    },

    // Get single book by ID
    getBook: function(id) {
      return request(`/books/${id}`);
    },

    // Create new book
    createBook: function(data) {
      return request('/books', {
        method: 'POST',
        body: JSON.stringify(data)
      });
    },

    // Update existing book
    updateBook: function(id, data) {
      return request(`/books/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
      });
    },

    // Delete book
    deleteBook: function(id) {
      return request(`/books/${id}`, {
        method: 'DELETE'
      });
    },

    // Search books
    searchBooks: function(query) {
      return request(`/search?q=${encodeURIComponent(query)}`);
    },

    // Get reading statistics
    getStats: function() {
      return request('/stats');
    }
  };
})();
