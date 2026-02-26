// PageCraft - Template Management

const TEMPLATES = {
  saas: {
    name: 'SaaS Product',
    description: 'Perfect for software products and services'
  },
  event: {
    name: 'Event/Webinar',
    description: 'Promote events, conferences, and webinars'
  },
  portfolio: {
    name: 'Portfolio Showcase',
    description: 'Showcase your work and projects'
  }
};

function renderTemplateCards() {
  const container = document.getElementById('template-cards');
  if (!container) return;

  container.innerHTML = '';

  Object.entries(TEMPLATES).forEach(([key, template]) => {
    const card = document.createElement('div');
    card.className = 'template-card';
    card.innerHTML = `
      <div class="template-preview">
        ${generateTemplatePreview(key)}
      </div>
      <div class="template-info">
        <h3>${template.name}</h3>
        <p style="color: #6b7280; margin-top: 0.5rem;">${template.description}</p>
      </div>
    `;
    card.addEventListener('click', () => {
      if (AppState.currentTemplate) {
        if (confirm('Switch template? Your current changes will be lost.')) {
          loadTemplate(key);
        }
      } else {
        loadTemplate(key);
      }
    });
    container.appendChild(card);
  });
}

/**
 * Generate SaaS template preview miniature
 * @returns {string} HTML string for SaaS preview
 */
function generateSaasPreview() {
  return `
    <div class="preview-miniature template-saas">
      <div class="mini-section mini-hero">
        <div class="mini-headline"></div>
        <div class="mini-subheadline"></div>
        <div class="mini-button"></div>
      </div>
      <div class="mini-section mini-features">
        <div class="mini-feature-grid">
          <div class="mini-feature"></div>
          <div class="mini-feature"></div>
          <div class="mini-feature"></div>
        </div>
      </div>
    </div>
  `;
}

/**
 * Generate Event template preview miniature
 * @returns {string} HTML string for Event preview
 */
function generateEventPreview() {
  return `
    <div class="preview-miniature template-event">
      <div class="mini-section mini-hero mini-hero-split">
        <div class="mini-hero-content">
          <div class="mini-headline"></div>
          <div class="mini-subheadline"></div>
          <div class="mini-button"></div>
        </div>
      </div>
      <div class="mini-section mini-features">
        <div class="mini-feature-grid mini-feature-grid-2col">
          <div class="mini-feature"></div>
          <div class="mini-feature"></div>
        </div>
      </div>
    </div>
  `;
}

/**
 * Generate Portfolio template preview miniature
 * @returns {string} HTML string for Portfolio preview
 */
function generatePortfolioPreview() {
  return `
    <div class="preview-miniature template-portfolio">
      <div class="mini-section mini-hero mini-hero-left">
        <div class="mini-headline"></div>
        <div class="mini-subheadline"></div>
        <div class="mini-button mini-button-outline"></div>
      </div>
      <div class="mini-section mini-features">
        <div class="mini-feature-list">
          <div class="mini-feature-row"></div>
          <div class="mini-feature-row"></div>
          <div class="mini-feature-row"></div>
        </div>
      </div>
    </div>
  `;
}

/**
 * Generate template preview based on template type
 * @param {string} templateKey - Template identifier (saas, event, portfolio)
 * @returns {string} HTML string for template preview
 */
function generateTemplatePreview(templateKey) {
  const previewGenerators = {
    saas: generateSaasPreview,
    event: generateEventPreview,
    portfolio: generatePortfolioPreview
  };

  const generator = previewGenerators[templateKey];
  return generator ? generator() : '';
}

// Initialize template cards on load
document.addEventListener('DOMContentLoaded', () => {
  renderTemplateCards();
});
