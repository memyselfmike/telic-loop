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
    // Initialize each section with visible:true by default
    AppState.sections = (data.sections || []).map(section => ({
      ...section,
      visible: section.visible !== undefined ? section.visible : true
    }));

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

    const isVisible = section.visible !== false;
    const eyeIcon = isVisible ? '👁️' : '👁️‍🗨️';
    const eyeClass = isVisible ? 'eye-visible' : 'eye-hidden';

    div.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: start;">
        <div style="flex: 1;">
          <strong>${section.type}</strong>
          <p style="font-size: 0.875rem; color: #6b7280; margin-top: 0.5rem;">
            ${section.content.headline || section.content.title || 'Section ' + (index + 1)}
          </p>
        </div>
        <button class="eye-toggle ${eyeClass}" data-index="${index}" title="${isVisible ? 'Hide section' : 'Show section'}">
          ${eyeIcon}
        </button>
      </div>
    `;
    sectionList.appendChild(div);
  });

  // Attach event listeners to eye toggle buttons
  document.querySelectorAll('.eye-toggle').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const index = parseInt(btn.dataset.index, 10);
      toggleSectionVisibility(index);
    });
  });
}

function renderPreview() {
  const previewContent = document.getElementById('preview-content');
  previewContent.innerHTML = '';

  // Add template-specific class to preview container
  previewContent.className = 'preview-content';
  if (AppState.currentTemplate) {
    previewContent.classList.add(`template-${AppState.currentTemplate}`);
  }

  // Only render visible sections - completely omit hidden sections from DOM
  AppState.sections.forEach(section => {
    if (section.visible !== false) {
      const sectionDiv = document.createElement('div');
      sectionDiv.className = `section section-${section.type}`;
      sectionDiv.innerHTML = renderSectionContent(section);
      previewContent.appendChild(sectionDiv);
    }
  });

  // Apply accent color
  document.documentElement.style.setProperty('--accent-color', AppState.accentColor);
}

// Helper function to add data attributes for inline editing
function makeEditable(sectionId, field, content) {
  return `data-section-id="${sectionId}" data-field="${field}"`;
}

function renderHeroSection(section) {
  const content = section.content;
  const sectionId = section.id;
  return `
    <h1 ${makeEditable(sectionId, 'headline')}>${content.headline || 'Hero Headline'}</h1>
    <p ${makeEditable(sectionId, 'subheadline')}>${content.subheadline || 'Hero subheadline'}</p>
    <button ${makeEditable(sectionId, 'cta_text')}>${content.cta_text || 'Get Started'}</button>
  `;
}

function renderFeaturesSection(section) {
  const content = section.content;
  const sectionId = section.id;
  const features = content.features || [];
  return `
    <h2>Features</h2>
    <div class="features-grid">
      ${features.map((f, index) => `
        <div class="feature-card">
          <div style="font-size: 3rem;">${f.icon || '⭐'}</div>
          <h3 ${makeEditable(sectionId, `features.${index}.title`)}>${f.title || 'Feature'}</h3>
          <p ${makeEditable(sectionId, `features.${index}.description`)}>${f.description || ''}</p>
        </div>
      `).join('')}
    </div>
  `;
}

function renderTestimonialsSection(section) {
  const content = section.content;
  const sectionId = section.id;
  const testimonials = content.testimonials || [];
  return `
    <h2>What Our Customers Say</h2>
    <div class="testimonials-grid">
      ${testimonials.map((t, index) => `
        <div class="testimonial-card">
          <blockquote ${makeEditable(sectionId, `testimonials.${index}.quote`)}>"${t.quote || ''}"</blockquote>
          <cite ${makeEditable(sectionId, `testimonials.${index}.author`)}>- ${t.author || 'Anonymous'}</cite>
        </div>
      `).join('')}
    </div>
  `;
}

function renderPricingSection(section) {
  const content = section.content;
  const sectionId = section.id;
  const tiers = content.tiers || [];
  return `
    <h2>Pricing</h2>
    <div class="pricing-grid">
      ${tiers.map((tier, index) => `
        <div class="pricing-card">
          <h3 ${makeEditable(sectionId, `tiers.${index}.name`)}>${tier.name || 'Plan'}</h3>
          <div class="price" ${makeEditable(sectionId, `tiers.${index}.price`)}>${tier.price || '$0'}</div>
          <ul>
            ${(tier.features || []).map((f, fIndex) => `<li ${makeEditable(sectionId, `tiers.${index}.features.${fIndex}`)}>${f}</li>`).join('')}
          </ul>
          <button ${makeEditable(sectionId, `tiers.${index}.cta_text`)}>${tier.cta_text || 'Choose Plan'}</button>
        </div>
      `).join('')}
    </div>
  `;
}

function renderCtaSection(section) {
  const content = section.content;
  const sectionId = section.id;
  return `
    <h2 ${makeEditable(sectionId, 'headline')}>${content.headline || 'Ready to Get Started?'}</h2>
    <p ${makeEditable(sectionId, 'description')}>${content.description || 'Join us today'}</p>
    <button ${makeEditable(sectionId, 'button_text')}>${content.button_text || 'Get Started'}</button>
  `;
}

function renderSectionContent(section) {
  switch (section.type) {
    case 'hero':
      return renderHeroSection(section);
    case 'features':
      return renderFeaturesSection(section);
    case 'testimonials':
      return renderTestimonialsSection(section);
    case 'pricing':
      return renderPricingSection(section);
    case 'cta':
      return renderCtaSection(section);
    default:
      return '<p>Unknown section type</p>';
  }
}

function toggleSectionVisibility(index) {
  if (index >= 0 && index < AppState.sections.length) {
    AppState.sections[index].visible = !AppState.sections[index].visible;
    renderSections();
    renderPreview();
  }
}

function showTemplateSelector() {
  if (confirm('Switch template? Your current changes will be lost.')) {
    // Clear current template state so clicking a new template doesn't show another confirmation
    AppState.currentTemplate = null;
    AppState.sections = [];
    // Show template selector
    document.getElementById('template-selector').style.display = 'block';
    // Hide editor
    document.querySelector('.editor-container').style.display = 'none';
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

  // Change Template button
  const changeTemplateBtn = document.getElementById('change-template-btn');
  if (changeTemplateBtn) {
    changeTemplateBtn.addEventListener('click', showTemplateSelector);
  }
});

function exportHTML() {
  const previewContent = document.getElementById('preview-content');
  if (!previewContent) return;

  // Wrap content in a div with the template class
  const templateClass = AppState.currentTemplate ? `template-${AppState.currentTemplate}` : '';
  const wrappedContent = `<div class="${templateClass}">${previewContent.innerHTML}</div>`;

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
  ${wrappedContent}
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

function getBaseCSS() {
  return `
    :root { --accent-color: ${AppState.accentColor}; }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    .section { padding: 3rem 2rem; }
  `;
}

function getSectionCSS() {
  return `
    .section-hero { background: linear-gradient(135deg, var(--accent-color) 0%, #1e40af 100%); color: white; text-align: center; padding: 5rem 2rem; }
    .section-hero h1 { font-size: 3rem; margin-bottom: 1rem; }
    .section-hero p { font-size: 1.25rem; margin-bottom: 2rem; opacity: 0.9; }
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
    .pricing-card { border: 2px solid var(--accent-color); border-radius: 8px; padding: 2rem; text-align: center; }
    .pricing-card h3 { font-size: 1.5rem; margin-bottom: 1rem; color: var(--accent-color); }
    .pricing-card .price { font-size: 2.5rem; font-weight: 700; margin: 1rem 0; color: var(--accent-color); }
    .pricing-card ul { list-style: none; margin: 2rem 0; text-align: left; }
    .pricing-card li { padding: 0.5rem 0; border-bottom: 1px solid #e5e7eb; }
    .pricing-card button { background: var(--accent-color); color: white; border: none; padding: 0.75rem 2rem; font-size: 1rem; font-weight: 600; border-radius: 8px; cursor: pointer; width: 100%; }
    .section-cta { background: var(--accent-color); color: white; text-align: center; padding: 5rem 2rem; }
    .section-cta h2 { font-size: 2.5rem; margin-bottom: 1rem; }
    .section-cta p { font-size: 1.25rem; margin-bottom: 2rem; opacity: 0.9; }
    .section-cta button { background: white; color: var(--accent-color); border: none; padding: 1rem 2rem; font-size: 1.125rem; font-weight: 600; border-radius: 8px; cursor: pointer; }
  `;
}

function getTemplateCSS() {
  return `
    /* SaaS Product Template */
    .template-saas .section-hero { background: linear-gradient(135deg, var(--accent-color) 0%, #1e40af 100%); text-align: center; }
    .template-saas .features-grid { grid-template-columns: repeat(3, 1fr); }
    .template-saas .testimonials-grid { grid-template-columns: repeat(3, 1fr); }

    /* Event/Webinar Template */
    .template-event .section-hero { background: linear-gradient(to right, #7c3aed 0%, #a855f7 100%); text-align: left; padding: 6rem 3rem; display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: center; }
    .template-event .section-hero h1 { font-size: 3.5rem; line-height: 1.1; grid-column: 1; }
    .template-event .section-hero p { font-size: 1.5rem; grid-column: 1; }
    .template-event .section-hero button { grid-column: 1; justify-self: start; font-size: 1.25rem; padding: 1.25rem 2.5rem; }
    .template-event .features-grid { grid-template-columns: repeat(2, 1fr); gap: 3rem; }
    .template-event .feature-card { text-align: left; padding: 2.5rem; background: #f9fafb; border-radius: 12px; }
    .template-event .testimonials-grid { display: flex; flex-direction: column; gap: 1.5rem; }
    .template-event .testimonial-card { border-left: 4px solid var(--accent-color); box-shadow: none; background: white; }
    .template-event .testimonial-card blockquote { font-size: 1.25rem; }

    /* Portfolio Template */
    .template-portfolio .section-hero { background: linear-gradient(to bottom, #10b981 0%, #059669 100%); text-align: left; padding: 7rem 3rem; max-width: 800px; margin: 0; }
    .template-portfolio .section-hero h1 { font-size: 4rem; font-weight: 300; letter-spacing: -0.05em; }
    .template-portfolio .section-hero p { font-size: 1.5rem; font-weight: 300; }
    .template-portfolio .section-hero button { background: transparent; border: 2px solid white; color: white; padding: 0.875rem 2rem; }
    .template-portfolio .features-grid { display: flex; flex-direction: column; gap: 2rem; max-width: 600px; }
    .template-portfolio .feature-card { text-align: left; padding: 0; display: flex; gap: 1.5rem; align-items: flex-start; }
    .template-portfolio .feature-card h3 { font-size: 1.75rem; font-weight: 400; }
    .template-portfolio .testimonials-grid { display: grid; grid-template-columns: 1fr; gap: 2rem; max-width: 700px; margin: 0 auto; }
    .template-portfolio .testimonial-card { background: transparent; border: none; box-shadow: none; padding: 2rem 0; border-bottom: 1px solid #e5e7eb; }
    .template-portfolio .testimonial-card blockquote { font-size: 1.25rem; font-style: normal; font-weight: 300; }
  `;
}

function getCombinedCSS() {
  // Combine all CSS sections for export
  return getBaseCSS() + getSectionCSS() + getTemplateCSS();
}
