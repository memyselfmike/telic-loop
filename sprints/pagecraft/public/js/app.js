// PageCraft - App State Management

const AppState = {
  currentTemplate: null,
  sections: [],
  accentColor: '#3b82f6'
};

async function loadTemplate(templateName) {
  try {
    const response = await fetch(`/templates/${templateName}.json`);
    if (!response.ok) {
      throw new Error(`Failed to load template: ${response.statusText}`);
    }
    const data = await response.json();

    AppState.currentTemplate = templateName;
    AppState.sections = data.sections || [];

    renderSections();
    renderPreview();

    // Hide template selector, show editor
    document.getElementById('template-selector').style.display = 'none';
    document.querySelector('.editor-container').style.display = 'grid';

  } catch (error) {
    console.error('Error loading template:', error);
    alert(`Failed to load template: ${error.message}`);
  }
}

function renderSections() {
  const sectionList = document.getElementById('section-list');
  sectionList.innerHTML = '';

  AppState.sections.forEach((section, index) => {
    const div = document.createElement('div');
    div.className = 'section-block';
    div.draggable = true;
    div.dataset.index = index;
    div.innerHTML = `
      <strong>${section.type}</strong>
      <p style="font-size: 0.875rem; color: #6b7280; margin-top: 0.5rem;">
        ${section.content.headline || section.content.title || 'Section ' + (index + 1)}
      </p>
    `;
    sectionList.appendChild(div);
  });
}

function renderPreview() {
  const previewContent = document.getElementById('preview-content');
  previewContent.innerHTML = '';

  AppState.sections.forEach(section => {
    const sectionDiv = document.createElement('div');
    sectionDiv.className = `section section-${section.type}`;
    sectionDiv.innerHTML = renderSectionContent(section);
    previewContent.appendChild(sectionDiv);
  });

  // Apply accent color
  document.documentElement.style.setProperty('--accent-color', AppState.accentColor);
}

function renderHeroSection(content) {
  return `
    <h1>${content.headline || 'Hero Headline'}</h1>
    <p>${content.subheadline || 'Hero subheadline'}</p>
    <button>${content.cta_text || 'Get Started'}</button>
  `;
}

function renderFeaturesSection(content) {
  const features = content.features || [];
  return `
    <h2>Features</h2>
    <div class="features-grid">
      ${features.map(f => `
        <div class="feature-card">
          <div style="font-size: 3rem;">${f.icon || '⭐'}</div>
          <h3>${f.title || 'Feature'}</h3>
          <p>${f.description || ''}</p>
        </div>
      `).join('')}
    </div>
  `;
}

function renderTestimonialsSection(content) {
  const testimonials = content.testimonials || [];
  return `
    <h2>What Our Customers Say</h2>
    <div class="testimonials-grid">
      ${testimonials.map(t => `
        <div class="testimonial-card">
          <blockquote>"${t.quote || ''}"</blockquote>
          <cite>- ${t.author || 'Anonymous'}</cite>
        </div>
      `).join('')}
    </div>
  `;
}

function renderPricingSection(content) {
  const tiers = content.tiers || [];
  return `
    <h2>Pricing</h2>
    <div class="pricing-grid">
      ${tiers.map(tier => `
        <div class="pricing-card">
          <h3>${tier.name || 'Plan'}</h3>
          <div class="price">${tier.price || '$0'}</div>
          <ul>
            ${(tier.features || []).map(f => `<li>${f}</li>`).join('')}
          </ul>
          <button>${tier.cta_text || 'Choose Plan'}</button>
        </div>
      `).join('')}
    </div>
  `;
}

function renderCtaSection(content) {
  return `
    <h2>${content.headline || 'Ready to Get Started?'}</h2>
    <p>${content.description || 'Join us today'}</p>
    <button>${content.button_text || 'Get Started'}</button>
  `;
}

function renderSectionContent(section) {
  switch (section.type) {
    case 'hero':
      return renderHeroSection(section.content);
    case 'features':
      return renderFeaturesSection(section.content);
    case 'testimonials':
      return renderTestimonialsSection(section.content);
    case 'pricing':
      return renderPricingSection(section.content);
    case 'cta':
      return renderCtaSection(section.content);
    default:
      return '<p>Unknown section type</p>';
  }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  // Viewport toggle
  const viewportToggle = document.getElementById('toggle-viewport');
  const previewFrame = document.getElementById('preview-frame');

  if (viewportToggle) {
    viewportToggle.addEventListener('click', () => {
      if (previewFrame.classList.contains('desktop')) {
        previewFrame.classList.remove('desktop');
        previewFrame.classList.add('mobile');
        viewportToggle.textContent = 'Desktop';
      } else {
        previewFrame.classList.remove('mobile');
        previewFrame.classList.add('desktop');
        viewportToggle.textContent = 'Mobile';
      }
    });
  }

  // Accent color picker
  const colorPicker = document.getElementById('accent-color');
  if (colorPicker) {
    colorPicker.addEventListener('change', (e) => {
      AppState.accentColor = e.target.value;
      renderPreview();
    });
  }

  // Export button
  const exportBtn = document.getElementById('export-btn');
  if (exportBtn) {
    exportBtn.addEventListener('click', exportHTML);
  }
});

function exportHTML() {
  const previewContent = document.getElementById('preview-content');
  if (!previewContent) return;

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Landing Page</title>
  <style>
    ${getCombinedCSS()}
  </style>
</head>
<body>
  ${previewContent.innerHTML}
</body>
</html>`;

  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'landing-page.html';
  a.click();
  URL.revokeObjectURL(url);
}

function getCombinedCSS() {
  // Return inline CSS for export
  return `
    :root { --accent-color: ${AppState.accentColor}; }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    .section { padding: 3rem 2rem; }
    .section-hero { background: linear-gradient(135deg, var(--accent-color) 0%, #1e40af 100%); color: white; text-align: center; padding: 5rem 2rem; }
    .section-hero h1 { font-size: 3rem; margin-bottom: 1rem; }
    .section-hero p { font-size: 1.25rem; margin-bottom: 2rem; }
    .section-hero button { background: white; color: var(--accent-color); border: none; padding: 1rem 2rem; font-size: 1rem; font-weight: 600; border-radius: 8px; cursor: pointer; }
    .section-features { background: white; }
    .section-features h2 { text-align: center; font-size: 2.5rem; margin-bottom: 3rem; color: var(--accent-color); }
    .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; max-width: 1000px; margin: 0 auto; }
    .feature-card { text-align: center; padding: 2rem; }
    .feature-card h3 { font-size: 1.5rem; margin: 1rem 0; color: var(--accent-color); }
    .section-testimonials { background: #f9fafb; }
    .section-testimonials h2 { text-align: center; font-size: 2.5rem; margin-bottom: 3rem; color: var(--accent-color); }
    .testimonials-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; max-width: 1200px; margin: 0 auto; }
    .testimonial-card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
    .testimonial-card blockquote { font-style: italic; margin-bottom: 1rem; font-size: 1.125rem; }
    .testimonial-card cite { font-weight: 600; color: var(--accent-color); }
    .section-pricing { background: white; }
    .section-pricing h2 { text-align: center; font-size: 2.5rem; margin-bottom: 3rem; color: var(--accent-color); }
    .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem; max-width: 1000px; margin: 0 auto; }
    .pricing-card { border: 2px solid #e5e7eb; border-radius: 8px; padding: 2rem; text-align: center; }
    .pricing-card h3 { font-size: 1.5rem; margin-bottom: 1rem; color: var(--accent-color); }
    .pricing-card .price { font-size: 2.5rem; font-weight: 700; margin: 1rem 0; color: var(--accent-color); }
    .pricing-card ul { list-style: none; margin: 2rem 0; text-align: left; }
    .pricing-card li { padding: 0.5rem 0; border-bottom: 1px solid #e5e7eb; }
    .pricing-card button { background: var(--accent-color); color: white; border: none; padding: 0.75rem 2rem; font-size: 1rem; font-weight: 600; border-radius: 8px; cursor: pointer; width: 100%; }
    .section-cta { background: var(--accent-color); color: white; text-align: center; padding: 5rem 2rem; }
    .section-cta h2 { font-size: 2.5rem; margin-bottom: 1rem; }
    .section-cta p { font-size: 1.25rem; margin-bottom: 2rem; }
    .section-cta button { background: white; color: var(--accent-color); border: none; padding: 1rem 2rem; font-size: 1.125rem; font-weight: 600; border-radius: 8px; cursor: pointer; }
  `;
}
