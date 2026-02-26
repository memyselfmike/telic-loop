// PageCraft - Drag and Drop Section Reordering

let draggedElement = null;
let draggedIndex = null;
let dropIndicator = null;

function initDragDrop() {
  const sectionList = document.getElementById('section-list');

  // Create drop indicator element
  dropIndicator = document.createElement('div');
  dropIndicator.className = 'drop-indicator';
  dropIndicator.style.display = 'none';

  // Delegate drag events to the section-list container
  sectionList.addEventListener('dragstart', handleDragStart);
  sectionList.addEventListener('dragend', handleDragEnd);
  sectionList.addEventListener('dragover', handleDragOver);
  sectionList.addEventListener('drop', handleDrop);
  sectionList.addEventListener('dragleave', handleDragLeave);
}

function handleDragStart(e) {
  // Check if the dragged element is a section-block
  if (!e.target.classList.contains('section-block')) {
    return;
  }

  draggedElement = e.target;
  draggedIndex = parseInt(draggedElement.dataset.index, 10);

  // Add dragging class for visual feedback
  draggedElement.classList.add('dragging');

  // Set drag data (required for Firefox)
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/html', draggedElement.innerHTML);
}

function handleDragEnd(e) {
  if (!draggedElement) return;

  // Remove dragging class
  draggedElement.classList.remove('dragging');

  // Hide drop indicator
  if (dropIndicator.parentNode) {
    dropIndicator.remove();
  }

  // Reset drag state
  draggedElement = null;
  draggedIndex = null;
}

function handleDragOver(e) {
  if (!draggedElement) return;

  e.preventDefault(); // Allow drop
  e.dataTransfer.dropEffect = 'move';

  // Find the section-block we're hovering over
  const target = e.target.closest('.section-block');
  if (!target || target === draggedElement) {
    return;
  }

  const sectionList = document.getElementById('section-list');
  const targetIndex = parseInt(target.dataset.index, 10);

  // Determine if we should insert before or after the target
  const rect = target.getBoundingClientRect();
  const midpoint = rect.top + rect.height / 2;
  const insertBefore = e.clientY < midpoint;

  // Show drop indicator
  dropIndicator.style.display = 'block';
  if (insertBefore) {
    sectionList.insertBefore(dropIndicator, target);
  } else {
    sectionList.insertBefore(dropIndicator, target.nextSibling);
  }
}

function handleDragLeave(e) {
  // Only hide indicator if leaving the section-list entirely
  if (e.target.id === 'section-list' && !e.relatedTarget?.closest('.section-list')) {
    if (dropIndicator.parentNode) {
      dropIndicator.style.display = 'none';
    }
  }
}

function handleDrop(e) {
  if (!draggedElement) return;

  e.preventDefault();
  e.stopPropagation();

  // Find the target section-block
  const target = e.target.closest('.section-block');
  if (!target || target === draggedElement) {
    return;
  }

  const targetIndex = parseInt(target.dataset.index, 10);

  // Determine insertion position
  const rect = target.getBoundingClientRect();
  const midpoint = rect.top + rect.height / 2;
  const insertBefore = e.clientY < midpoint;

  // Calculate new index based on drop position
  let newIndex;
  if (insertBefore) {
    newIndex = targetIndex;
  } else {
    newIndex = targetIndex + 1;
  }

  // Adjust for the fact that removing the dragged element shifts indices
  if (draggedIndex < newIndex) {
    newIndex--;
  }

  // Only proceed if position actually changed
  if (draggedIndex === newIndex) {
    return;
  }

  // Reorder the AppState.sections array
  const movedSection = AppState.sections.splice(draggedIndex, 1)[0];
  AppState.sections.splice(newIndex, 0, movedSection);

  // Re-render sections and preview to reflect the new order
  renderSections();
  renderPreview();
}

// Initialize drag-and-drop when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDragDrop);
} else {
  initDragDrop();
}
