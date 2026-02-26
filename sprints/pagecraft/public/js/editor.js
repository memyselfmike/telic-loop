// PageCraft - Inline Text Editor
// Enables click-to-edit functionality on all editable text elements in the preview

(function() {
  'use strict';

  // Track currently editing element to prevent multiple edits
  let currentlyEditing = null;

  /**
   * Initialize inline editor by attaching event listeners to the preview panel
   */
  function initInlineEditor() {
    const previewContent = document.getElementById('preview-content');
    if (!previewContent) return;

    // Use event delegation to handle clicks on editable elements
    previewContent.addEventListener('click', handleEditableClick);
  }

  /**
   * Handle click events on editable elements
   */
  function handleEditableClick(e) {
    const target = e.target;

    // Check if clicked element has data-field attribute (making it editable)
    if (!target.hasAttribute('data-field')) return;

    // Prevent clicking on already-editing element
    if (currentlyEditing === target) return;

    // If another element is being edited, commit its changes first
    if (currentlyEditing && currentlyEditing !== target) {
      commitEdit(currentlyEditing);
    }

    // Start editing this element
    startEdit(target);
  }

  /**
   * Make an element editable
   */
  function startEdit(element) {
    // Store original content in case we need to revert
    element.dataset.originalContent = element.textContent;

    // Make element editable
    element.contentEditable = 'true';
    element.classList.add('editing');

    // Focus and select all text
    element.focus();
    selectAllText(element);

    // Track this as the currently editing element
    currentlyEditing = element;

    // Listen for blur event to commit changes
    element.addEventListener('blur', handleBlur, { once: true });

    // Listen for Enter key to commit changes (except in blockquote/p which may want newlines)
    element.addEventListener('keydown', handleKeydown);
  }

  /**
   * Handle blur event - commit the edit
   */
  function handleBlur(e) {
    commitEdit(e.target);
  }

  /**
   * Handle keydown events during editing
   */
  function handleKeydown(e) {
    // Escape key - revert changes
    if (e.key === 'Escape') {
      e.preventDefault();
      revertEdit(e.target);
      e.target.blur();
    }

    // Enter key - commit changes (for single-line fields like h1, h2, h3, button)
    if (e.key === 'Enter') {
      const tagName = e.target.tagName.toLowerCase();
      // Only prevent default for single-line elements
      if (['h1', 'h2', 'h3', 'button', 'cite'].includes(tagName)) {
        e.preventDefault();
        e.target.blur(); // This will trigger commit via blur handler
      }
    }
  }

  /**
   * Commit the edit - update AppState with the new value
   */
  function commitEdit(element) {
    // Remove contenteditable
    element.contentEditable = 'false';
    element.classList.remove('editing');
    element.removeEventListener('keydown', handleKeydown);

    // Get the new text content
    const newText = element.textContent.trim();
    const originalText = element.dataset.originalContent;

    // Only update if text actually changed
    if (newText !== originalText && newText !== '') {
      updateAppState(element, newText);
    } else if (newText === '') {
      // Don't allow empty text - revert to original
      element.textContent = originalText;
    }

    // Clean up
    delete element.dataset.originalContent;
    currentlyEditing = null;
  }

  /**
   * Revert the edit - restore original content
   */
  function revertEdit(element) {
    element.textContent = element.dataset.originalContent;
    element.contentEditable = 'false';
    element.classList.remove('editing');
    element.removeEventListener('keydown', handleKeydown);
    delete element.dataset.originalContent;
    currentlyEditing = null;
  }

  /**
   * Update AppState with the new text value
   */
  function updateAppState(element, newText) {
    const sectionId = element.dataset.sectionId;
    const field = element.dataset.field;

    if (!sectionId || !field) {
      console.error('Missing section ID or field name', { sectionId, field });
      return;
    }

    // Find the section in AppState
    const section = AppState.sections.find(s => s.id === sectionId);
    if (!section) {
      console.error('Section not found in AppState', sectionId);
      return;
    }

    // Parse the field path (e.g., "headline", "features.0.title", "testimonials.1.quote")
    const fieldParts = field.split('.');

    // Navigate to the target object
    let target = section.content;
    for (let i = 0; i < fieldParts.length - 1; i++) {
      const part = fieldParts[i];
      if (target[part] === undefined) {
        console.error('Invalid field path', field);
        return;
      }
      target = target[part];
    }

    // Update the final field
    const finalKey = fieldParts[fieldParts.length - 1];
    target[finalKey] = newText;

    console.log('Updated AppState:', sectionId, field, newText);

    // Re-render to ensure consistency (this will destroy and recreate DOM)
    // The new DOM will have the updated text
    renderPreview();

    // Re-render sections list in case we edited a headline that shows there
    renderSections();
  }

  /**
   * Select all text in an element
   */
  function selectAllText(element) {
    const range = document.createRange();
    range.selectNodeContents(element);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initInlineEditor);
  } else {
    initInlineEditor();
  }

  // Re-initialize after preview renders (since DOM gets replaced)
  // We use MutationObserver to detect when preview content changes
  const observer = new MutationObserver(() => {
    // Event listeners are attached to preview-content itself, which doesn't get replaced
    // So we don't need to re-initialize - delegation handles it
  });

  const previewContent = document.getElementById('preview-content');
  if (previewContent) {
    observer.observe(previewContent, { childList: true });
  }

})();
