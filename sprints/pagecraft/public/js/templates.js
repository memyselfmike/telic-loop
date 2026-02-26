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
      <h3>${template.name}</h3>
      <p style="color: #6b7280; margin-top: 0.5rem;">${template.description}</p>
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

// Initialize template cards on load
document.addEventListener('DOMContentLoaded', () => {
  renderTemplateCards();
});
