// DOM Elements
const taskInput = document.getElementById('task-input');
const addButton = document.getElementById('add-button');
const taskList = document.getElementById('task-list');

// API Base URL
const API_BASE = '/api/tasks';

// Load tasks on page load
document.addEventListener('DOMContentLoaded', () => {
  loadTasks();
  setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
  addButton.addEventListener('click', addTask);
  taskInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      addTask();
    }
  });
}

// Load all tasks from the API
async function loadTasks() {
  try {
    const response = await fetch(API_BASE);
    if (!response.ok) {
      throw new Error(`Failed to load tasks: ${response.statusText}`);
    }
    const tasks = await response.json();
    renderTasks(tasks);
  } catch (error) {
    console.error('Error loading tasks:', error);
    showError('Failed to load tasks. Please refresh the page.');
  }
}

// Render tasks to the DOM
function renderTasks(tasks) {
  taskList.innerHTML = '';

  if (tasks.length === 0) {
    taskList.innerHTML = '<li class="empty-state">No tasks yet. Add one above!</li>';
    return;
  }

  tasks.forEach(task => {
    const li = createTaskElement(task);
    taskList.appendChild(li);
  });
}

// Create a task element
function createTaskElement(task) {
  const li = document.createElement('li');
  li.className = 'task-item';
  li.dataset.taskId = task.id;

  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  checkbox.checked = task.done;
  checkbox.className = 'task-checkbox';
  checkbox.addEventListener('change', () => toggleTask(task.id));

  const title = document.createElement('span');
  title.className = 'task-title';
  title.textContent = task.title;
  if (task.done) {
    title.classList.add('done');
  }

  const deleteButton = document.createElement('button');
  deleteButton.className = 'delete-button';
  deleteButton.textContent = 'Delete';
  deleteButton.addEventListener('click', () => deleteTask(task.id));

  li.appendChild(checkbox);
  li.appendChild(title);
  li.appendChild(deleteButton);

  return li;
}

// Add a new task
async function addTask() {
  const title = taskInput.value.trim();

  if (!title) {
    showError('Please enter a task title');
    return;
  }

  try {
    const response = await fetch(API_BASE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ title })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to add task');
    }

    const newTask = await response.json();
    taskInput.value = '';

    // Reload tasks to show the new task
    await loadTasks();
  } catch (error) {
    console.error('Error adding task:', error);
    showError('Failed to add task. Please try again.');
  }
}

// Toggle task done status
async function toggleTask(taskId) {
  try {
    const response = await fetch(`${API_BASE}/${taskId}`, {
      method: 'PATCH'
    });

    if (!response.ok) {
      throw new Error('Failed to toggle task');
    }

    // Reload tasks to reflect the change
    await loadTasks();
  } catch (error) {
    console.error('Error toggling task:', error);
    showError('Failed to update task. Please try again.');
    // Reload to revert the UI
    await loadTasks();
  }
}

// Delete a task
async function deleteTask(taskId) {
  try {
    const response = await fetch(`${API_BASE}/${taskId}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error('Failed to delete task');
    }

    // Reload tasks to reflect the deletion
    await loadTasks();
  } catch (error) {
    console.error('Error deleting task:', error);
    showError('Failed to delete task. Please try again.');
  }
}

// Show error message to user
function showError(message) {
  // Simple alert for now - could be enhanced with a toast notification
  alert(message);
}
