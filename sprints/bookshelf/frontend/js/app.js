// App - Main application entry point (IIFE pattern)
(function() {
  const addBookBtn = document.getElementById('addBookBtn');
  const statsBtn = document.getElementById('statsBtn');
  const libraryView = document.getElementById('libraryView');
  const statsView = document.getElementById('statsView');

  let currentView = 'library'; // 'library' or 'stats'

  // Toast notification system
  window.Toast = {
    success: function(message) {
      showToast(message, 'success');
    },

    error: function(message) {
      showToast(message, 'error');
    }
  };

  function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toastContainer');

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    toastContainer.appendChild(toast);

    // Auto-dismiss after 3 seconds
    setTimeout(() => {
      toast.style.animation = 'slideInRight 0.2s reverse';
      setTimeout(() => {
        toast.remove();
      }, 200);
    }, 3000);
  }

  function switchToLibrary() {
    currentView = 'library';
    libraryView.style.display = 'block';
    statsView.style.display = 'none';
    statsBtn.classList.remove('active');

    window.Search.clear();
    window.Library.refresh();
  }

  function switchToStats() {
    currentView = 'stats';
    libraryView.style.display = 'none';
    statsView.style.display = 'block';
    statsBtn.classList.add('active');

    window.Stats.show();
  }

  // Initialize on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', function() {
    // Initialize library view
    window.Library.init();

    // Add Book button
    addBookBtn.addEventListener('click', () => {
      window.Modal.openAdd();
    });

    // Stats button - toggle between library and stats
    statsBtn.addEventListener('click', () => {
      if (currentView === 'library') {
        switchToStats();
      } else {
        switchToLibrary();
      }
    });

    // Update stats button text based on current view
    const updateStatsButton = () => {
      if (currentView === 'stats') {
        statsBtn.textContent = '📚 Library';
      } else {
        statsBtn.textContent = '📊 Stats';
      }
    };

    // Watch for view changes
    const originalSwitchToLibrary = switchToLibrary;
    const originalSwitchToStats = switchToStats;

    switchToLibrary = function() {
      originalSwitchToLibrary();
      updateStatsButton();
    };

    switchToStats = function() {
      originalSwitchToStats();
      updateStatsButton();
    };

    updateStatsButton();
  });
})();
