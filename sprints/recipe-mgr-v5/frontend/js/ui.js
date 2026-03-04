/**
 * Reusable UI Components
 * Extracted to keep individual modules under 400 lines
 */

/**
 * Show a modal with the given content
 * @param {string} title - Modal title
 * @param {HTMLElement|string} content - Modal body content
 * @param {Function} onClose - Optional callback when modal closes
 * @returns {Object} Modal controls { close, element }
 */
export function showModal(title, content, onClose = null) {
  const modalRoot = document.getElementById('modal-root');

  // Create modal structure
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';

  const modal = document.createElement('div');
  modal.className = 'modal';

  const header = document.createElement('div');
  header.className = 'modal-header';

  const titleEl = document.createElement('h2');
  titleEl.textContent = title;

  const closeBtn = document.createElement('button');
  closeBtn.className = 'btn-icon';
  closeBtn.innerHTML = '✕';
  closeBtn.setAttribute('aria-label', 'Close');

  header.appendChild(titleEl);
  header.appendChild(closeBtn);

  const body = document.createElement('div');
  body.className = 'modal-body';

  if (typeof content === 'string') {
    body.innerHTML = content;
  } else {
    body.appendChild(content);
  }

  modal.appendChild(header);
  modal.appendChild(body);
  overlay.appendChild(modal);
  modalRoot.appendChild(overlay);

  // Close handlers
  const close = () => {
    overlay.remove();
    if (onClose) onClose();
  };

  closeBtn.addEventListener('click', close);

  // Close on overlay click (but not modal content)
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) close();
  });

  // Close on Escape key
  const handleEscape = (e) => {
    if (e.key === 'Escape') {
      close();
      document.removeEventListener('keydown', handleEscape);
    }
  };
  document.addEventListener('keydown', handleEscape);

  // Focus management
  setTimeout(() => {
    const firstInput = modal.querySelector('input, textarea, button, select');
    if (firstInput) firstInput.focus();
  }, 100);

  return { close, element: modal };
}

/**
 * Show a confirmation dialog
 * @param {string} message - Confirmation message
 * @param {string} confirmText - Confirm button text (default: "Confirm")
 * @param {string} cancelText - Cancel button text (default: "Cancel")
 * @returns {Promise<boolean>} True if confirmed, false if cancelled
 */
export function showConfirm(message, confirmText = 'Confirm', cancelText = 'Cancel') {
  return new Promise((resolve) => {
    const content = document.createElement('div');
    content.className = 'confirm-dialog';

    const msg = document.createElement('p');
    msg.textContent = message;
    msg.style.marginBottom = 'var(--space-lg)';

    const actions = document.createElement('div');
    actions.className = 'modal-actions';

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-secondary';
    cancelBtn.textContent = cancelText;

    const confirmBtn = document.createElement('button');
    confirmBtn.className = 'btn btn-danger';
    confirmBtn.textContent = confirmText;

    actions.appendChild(cancelBtn);
    actions.appendChild(confirmBtn);

    content.appendChild(msg);
    content.appendChild(actions);

    const modal = showModal('Confirm', content);

    cancelBtn.addEventListener('click', () => {
      modal.close();
      resolve(false);
    });

    confirmBtn.addEventListener('click', () => {
      modal.close();
      resolve(true);
    });
  });
}

/**
 * Show a toast notification
 * @param {string} message - Toast message
 * @param {string} type - Toast type: 'success', 'error', 'warning', 'info' (default: 'info')
 * @param {number} duration - Duration in ms (default: 3000)
 */
export function showToast(message, type = 'info', duration = 3000) {
  const toastRoot = document.getElementById('toast-root');

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icon = getToastIcon(type);
  const iconSpan = document.createElement('span');
  iconSpan.className = 'toast-icon';
  iconSpan.textContent = icon;

  const messageSpan = document.createElement('span');
  messageSpan.textContent = message;

  toast.appendChild(iconSpan);
  toast.appendChild(messageSpan);

  toastRoot.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.add('toast-visible');
  });

  // Auto-remove after duration
  setTimeout(() => {
    toast.classList.remove('toast-visible');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function getToastIcon(type) {
  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };
  return icons[type] || icons.info;
}

/**
 * Show a loading spinner overlay
 * @returns {Object} Spinner controls { hide }
 */
export function showLoading() {
  const overlay = document.createElement('div');
  overlay.className = 'loading-overlay';
  overlay.innerHTML = '<div class="spinner"></div>';

  document.body.appendChild(overlay);

  return {
    hide: () => overlay.remove()
  };
}

/**
 * Create a form field with label
 * @param {string} label - Field label
 * @param {HTMLElement} input - Input element
 * @param {boolean} required - Whether field is required
 * @returns {HTMLElement} Form field container
 */
export function createFormField(label, input, required = false) {
  const field = document.createElement('div');
  field.className = 'form-field';

  const labelEl = document.createElement('label');
  labelEl.textContent = label;
  if (required) {
    const asterisk = document.createElement('span');
    asterisk.className = 'required';
    asterisk.textContent = ' *';
    labelEl.appendChild(asterisk);
  }

  field.appendChild(labelEl);
  field.appendChild(input);

  return field;
}

/**
 * Create an empty state message
 * @param {string} icon - Emoji icon
 * @param {string} title - Empty state title
 * @param {string} message - Empty state message
 * @returns {HTMLElement} Empty state container
 */
export function createEmptyState(icon, title, message) {
  const container = document.createElement('div');
  container.className = 'empty-state';

  const iconEl = document.createElement('div');
  iconEl.className = 'empty-state-icon';
  iconEl.textContent = icon;

  const titleEl = document.createElement('h3');
  titleEl.textContent = title;

  const messageEl = document.createElement('p');
  messageEl.textContent = message;

  container.appendChild(iconEl);
  container.appendChild(titleEl);
  container.appendChild(messageEl);

  return container;
}
