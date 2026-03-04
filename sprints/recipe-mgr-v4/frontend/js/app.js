/**
 * Recipe Manager SPA - Main Application
 * Hash-based router with shared state and API helpers
 */

// Shared application state
window.appState = {
    currentWeek: getMondayOfCurrentWeek(),
    currentView: 'recipes'
};

// API Helper Function
async function fetchJSON(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        // Handle 204 No Content
        if (response.status === 204) {
            return null;
        }

        return await response.json();
    } catch (error) {
        throw error;
    }
}

// Date Helper: Get Monday of current week
function getMondayOfCurrentWeek() {
    const today = new Date();
    const day = today.getDay();
    const diff = day === 0 ? -6 : 1 - day; // Adjust when day is Sunday
    const monday = new Date(today);
    monday.setDate(today.getDate() + diff);
    return monday.toISOString().split('T')[0];
}

// Date Helper: Format date for display
function formatDate(isoDate) {
    const date = new Date(isoDate + 'T00:00:00');
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// Date Helper: Get date for a specific day of week
function getDateForDayOfWeek(weekStart, dayOfWeek) {
    const date = new Date(weekStart + 'T00:00:00');
    date.setDate(date.getDate() + dayOfWeek);
    return date.toISOString().split('T')[0];
}

// Date Helper: Add weeks to a date
function addWeeks(isoDate, weeks) {
    const date = new Date(isoDate + 'T00:00:00');
    date.setDate(date.getDate() + (weeks * 7));
    return date.toISOString().split('T')[0];
}

// Modal Management
const modal = {
    escapeHandler: null,

    show(content) {
        const modalContainer = document.getElementById('modal-container');
        const modalBody = document.getElementById('modal-body');
        modalBody.innerHTML = content;
        modalContainer.classList.remove('hidden');

        // Close on overlay click
        modalContainer.onclick = (e) => {
            if (e.target === modalContainer) {
                this.hide();
            }
        };

        // Close button
        const closeBtn = document.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.onclick = () => this.hide();
        }

        // Close on Escape key
        this.escapeHandler = (e) => {
            if (e.key === 'Escape') {
                this.hide();
            }
        };
        document.addEventListener('keydown', this.escapeHandler);
    },

    hide() {
        const modalContainer = document.getElementById('modal-container');
        modalContainer.classList.add('hidden');

        // Remove escape key listener
        if (this.escapeHandler) {
            document.removeEventListener('keydown', this.escapeHandler);
            this.escapeHandler = null;
        }
    }
};

// View Router
const router = {
    views: {},

    register(name, mountFn) {
        this.views[name] = mountFn;
    },

    navigate(viewName) {
        if (!this.views[viewName]) {
            return;
        }

        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.dataset.view === viewName) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Update state
        appState.currentView = viewName;

        // Mount view
        const mainContent = document.getElementById('main-content');
        mainContent.innerHTML = '';
        this.views[viewName](mainContent);
    }
};

// Handle hash changes
function handleHashChange() {
    const hash = window.location.hash.slice(1) || 'recipes';
    router.navigate(hash);
}

// Error Display Helper
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background-color: var(--danger);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        z-index: 1001;
        max-width: 400px;
    `;
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);

    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Success Message Helper
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background-color: var(--success);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        z-index: 1001;
        max-width: 400px;
    `;
    successDiv.textContent = message;
    document.body.appendChild(successDiv);

    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    // Set up navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.hash = link.dataset.view;
        });
    });

    // Handle hash changes
    window.addEventListener('hashchange', handleHashChange);

    // Initial route
    handleHashChange();
});
