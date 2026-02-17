/**
 * Freelancer Time Tracker — SPA Application
 * Vanilla JS, no frameworks, no build step.
 * PRD 4.1, 4.6, 4.7
 */

'use strict';

/* ============================================================
   API Layer — all fetch() calls live here
   ============================================================ */
const API = {
  async request(method, path, body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body !== null) {
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) {
      const msg = data.detail || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return data;
  },

  get: (path) => API.request('GET', path),
  post: (path, body) => API.request('POST', path, body),
  put: (path, body) => API.request('PUT', path, body),
  del: (path) => API.request('DELETE', path),

  /* Projects */
  getProjects: (active) => {
    const qs = active !== undefined ? `?active=${active}` : '';
    return API.get(`/api/projects${qs}`);
  },
  createProject: (data) => API.post('/api/projects', data),
  updateProject: (id, data) => API.put(`/api/projects/${id}`, data),
  deleteProject: (id) => API.del(`/api/projects/${id}`),

  /* Timer */
  getTimer: () => API.get('/api/timer'),
  startTimer: (data) => API.post('/api/timer/start', data),
  stopTimer: () => API.post('/api/timer/stop', {}),

  /* Entries */
  getEntries: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/api/entries${qs ? '?' + qs : ''}`);
  },
  createEntry: (data) => API.post('/api/entries', data),
  updateEntry: (id, data) => API.put(`/api/entries/${id}`, data),
  deleteEntry: (id) => API.del(`/api/entries/${id}`),

  /* Reports */
  getTimesheet: (params) => {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/api/reports/timesheet?${qs}`);
  },
  getCSVUrl: (params) => {
    const qs = new URLSearchParams(params).toString();
    return `/api/reports/timesheet/csv?${qs}`;
  },
};

/* ============================================================
   State — single source of truth for the UI
   ============================================================ */
const State = {
  currentTab: 'timer',
  projects: [],       // all projects from server
  timer: null,        // running timer object or null
  timerInterval: null, // setInterval handle for clock tick
  todayEntries: [],   // entries for today
  weekOffset: 0,      // 0 = current week, -1 = last week, etc.
  weekEntries: [],    // entries for displayed week
  projectsSubtab: 'active',
  reportFrom: '',
  reportTo: '',
  reportProjectId: '',
  reportData: null,
  _pollInterval: null,
};

/* ============================================================
   Router — tab switching without page reload
   ============================================================ */
const Router = {
  navigate(tab) {
    State.currentTab = tab;

    // Update sidebar active item
    document.querySelectorAll('.nav-item, .tab-btn').forEach(el => {
      const isActive = el.dataset.tab === tab;
      el.classList.toggle('active', isActive);
      el.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    // Show/hide views
    document.querySelectorAll('.view').forEach(view => {
      const isActive = view.id === `view-${tab}`;
      view.classList.toggle('active', isActive);
      if (isActive) {
        view.removeAttribute('hidden');
      } else {
        view.setAttribute('hidden', '');
      }
    });

    // Load data for the activated tab
    switch (tab) {
      case 'timer':   App.loadTimerView(); break;
      case 'weekly':  App.loadWeeklyView(); break;
      case 'projects': App.loadProjectsView(); break;
      case 'reports': App.initReportsView(); break;
    }
  },
};

/* ============================================================
   Toast Notifications
   ============================================================ */
const Toast = {
  show(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span>${escapeHtml(message)}</span>
      <button class="toast-close" aria-label="Dismiss">&times;</button>
    `;
    toast.querySelector('.toast-close').addEventListener('click', () => toast.remove());
    container.appendChild(toast);
    if (duration > 0) {
      setTimeout(() => toast.remove(), duration);
    }
    return toast;
  },
  error(msg) { return Toast.show(msg, 'error', 6000); },
  success(msg) { return Toast.show(msg, 'success'); },
  info(msg) { return Toast.show(msg, 'info'); },
};

/* ============================================================
   Utility helpers
   ============================================================ */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatDuration(seconds) {
  if (seconds == null || isNaN(seconds)) return '—';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function formatHM(seconds) {
  if (seconds == null || isNaN(seconds)) return '0:00';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}:${String(m).padStart(2, '0')}`;
}

function formatTime(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  // isoStr may be "2026-02-17T..." or just "2026-02-17"
  const s = String(isoStr).substring(0, 10);
  const [y, mo, d] = s.split('-').map(Number);
  const date = new Date(y, mo - 1, d);
  return date.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
}

function todayISO() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}

/** Return Monday of the week that contains the given date */
function getMondayOf(date) {
  const d = new Date(date);
  const day = d.getDay(); // 0=Sun,1=Mon,...,6=Sat
  const diff = (day === 0 ? -6 : 1 - day);
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

function addDays(date, n) {
  const d = new Date(date);
  d.setDate(d.getDate() + n);
  return d;
}

function dateToISO(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function getWeekRange(offset) {
  const monday = getMondayOf(new Date());
  monday.setDate(monday.getDate() + offset * 7);
  const sunday = addDays(monday, 6);
  return { monday, sunday };
}

function formatAmount(hours, rate) {
  return (hours * rate).toFixed(2);
}

function setLoading(show) {
  const overlay = document.getElementById('loading-overlay');
  if (show) overlay.removeAttribute('hidden');
  else overlay.setAttribute('hidden', '');
}

/* ============================================================
   Project color palette
   ============================================================ */
const PROJECT_COLORS = [
  '#58a6ff', '#3fb950', '#f85149', '#d29922',
  '#bc8cff', '#f778ba', '#79c0ff', '#56d364',
];

function colorSwatchHTML(selectedColor) {
  return PROJECT_COLORS.map(c => `
    <button type="button"
      class="color-swatch${c === selectedColor ? ' selected' : ''}"
      style="background:${c}"
      data-color="${c}"
      aria-label="Color ${c}"
      onclick="App._pickColor('${c}', this)">
    </button>
  `).join('');
}

/* ============================================================
   Main Application Object
   ============================================================ */
const App = {

  /* ---- Initialization ---- */
  async init() {
    setLoading(true);
    try {
      // Load projects into state (used across all tabs)
      await App._refreshProjects();
      // Set up navigation listeners
      document.querySelectorAll('[data-tab]').forEach(btn => {
        btn.addEventListener('click', () => Router.navigate(btn.dataset.tab));
      });
      // Navigate to default tab
      Router.navigate('timer');
      // Start polling timer every 5s (PRD 4.7)
      State._pollInterval = setInterval(App._pollTimer, 5000);
    } catch (err) {
      Toast.error('Failed to initialize app: ' + err.message);
    } finally {
      setLoading(false);
    }
  },

  async _refreshProjects() {
    State.projects = await API.getProjects();
  },

  /* ---- Timer polling (PRD 4.7) ---- */
  async _pollTimer() {
    try {
      const timer = await API.getTimer();
      const wasRunning = !!State.timer;
      const isRunning = !!timer;
      State.timer = timer;

      if (State.currentTab === 'timer') {
        App._updateTimerUI();
      }

      // If state changed (stopped externally), refresh entries
      if (wasRunning !== isRunning && State.currentTab === 'timer') {
        await App._loadTodayEntries();
      }
    } catch (_) {
      // Silent — poll failures are non-critical
    }
  },

  /* ======================================================
     Timer View
     ====================================================== */
  async loadTimerView() {
    await App._refreshProjects();
    App._populateTimerProjectDropdown();
    await App._loadTimerState();
    await App._loadTodayEntries();
    App._renderTodaySummary();
  },

  _populateTimerProjectDropdown() {
    const sel = document.getElementById('timer-project');
    const active = State.projects.filter(p => !p.archived);
    const currentVal = sel.value;
    sel.innerHTML = '<option value="">— Select a project —</option>' +
      active.map(p =>
        `<option value="${p.id}" style="border-left:4px solid ${escapeHtml(p.color)}">${escapeHtml(p.name)}</option>`
      ).join('');
    // Restore selection if still valid
    if (currentVal && active.find(p => String(p.id) === currentVal)) {
      sel.value = currentVal;
    }
  },

  async _loadTimerState() {
    try {
      State.timer = await API.getTimer();
      App._updateTimerUI();
    } catch (err) {
      Toast.error('Could not load timer: ' + err.message);
    }
  },

  _updateTimerUI() {
    const display = document.getElementById('timer-display');
    const btn = document.getElementById('timer-btn');
    const sel = document.getElementById('timer-project');
    const descInput = document.getElementById('timer-description');

    if (State.timerInterval) {
      clearInterval(State.timerInterval);
      State.timerInterval = null;
    }

    if (State.timer) {
      // Timer is running
      display.classList.add('running');
      btn.textContent = 'Stop';
      btn.className = 'btn btn-stop';
      // Lock project/description while running
      sel.disabled = true;
      descInput.disabled = true;
      // Show current project in dropdown
      sel.value = String(State.timer.project_id);
      descInput.value = State.timer.description || '';
      // Start ticking
      const updateDisplay = () => {
        const elapsed = State.timer.elapsed_seconds + Math.floor((Date.now() - State._timerStarted) / 1000);
        display.textContent = formatDuration(elapsed);
      };
      State._timerStarted = Date.now();
      updateDisplay();
      State.timerInterval = setInterval(updateDisplay, 1000);
    } else {
      // No timer running
      display.classList.remove('running');
      display.textContent = '00:00:00';
      btn.textContent = 'Start';
      btn.className = 'btn btn-start';
      sel.disabled = false;
      descInput.disabled = false;
    }
  },

  async timerToggle() {
    const btn = document.getElementById('timer-btn');
    btn.disabled = true;

    try {
      if (State.timer) {
        // Stop
        const entry = await API.stopTimer();
        State.timer = null;
        Toast.success(`Stopped: ${formatDuration(entry.duration_seconds)}`);
        App._updateTimerUI();
        await App._loadTodayEntries();
        App._renderTodaySummary();
      } else {
        // Start
        const projectId = document.getElementById('timer-project').value;
        if (!projectId) {
          Toast.error('Please select a project before starting the timer.');
          return;
        }
        const description = document.getElementById('timer-description').value.trim();
        const timer = await API.startTimer({ project_id: parseInt(projectId), description });
        State.timer = timer;
        Toast.success('Timer started');
        App._updateTimerUI();
      }
    } catch (err) {
      Toast.error('Timer error: ' + err.message);
    } finally {
      btn.disabled = false;
    }
  },

  async _loadTodayEntries() {
    try {
      const today = todayISO();
      const entries = await API.getEntries({ date: today });
      // Most recent first
      State.todayEntries = entries.sort((a, b) =>
        new Date(b.start_time) - new Date(a.start_time)
      );
      App._renderTodayEntries();
      App._renderTodaySummary();
    } catch (err) {
      Toast.error('Could not load entries: ' + err.message);
    }
  },

  _renderTodayEntries() {
    const container = document.getElementById('today-entries-list');
    const entries = State.todayEntries;

    if (!entries.length) {
      container.innerHTML = '<div class="empty-state">No entries today. Start the timer to begin tracking!</div>';
      return;
    }

    container.innerHTML = entries.map(e => {
      const dur = e.duration_seconds != null
        ? formatDuration(e.duration_seconds)
        : (e.end_time == null ? '<span style="color:var(--accent-green)">Running…</span>' : '—');
      const timeRange = e.end_time
        ? `${formatTime(e.start_time)} – ${formatTime(e.end_time)}`
        : formatTime(e.start_time);

      return `
        <div class="entry-item" data-id="${e.id}">
          <div class="entry-color-dot" style="background:${escapeHtml(e.project_color || '#58a6ff')}"></div>
          <div class="entry-info">
            <div class="entry-project">${escapeHtml(e.project_name || 'Unknown')}</div>
            ${e.description ? `<div class="entry-description">${escapeHtml(e.description)}</div>` : ''}
          </div>
          <div class="entry-time">${timeRange}</div>
          <div class="entry-duration">${dur}</div>
          <div class="entry-actions">
            <button class="btn-icon" onclick="App.openEditEntryModal(${e.id})" title="Edit entry">✏️</button>
            <button class="btn-icon" onclick="App.deleteEntry(${e.id})" title="Delete entry">🗑️</button>
          </div>
        </div>
      `;
    }).join('');
  },

  _renderTodaySummary() {
    const entries = State.todayEntries.filter(e => e.duration_seconds != null);
    const totalSeconds = entries.reduce((sum, e) => sum + (e.duration_seconds || 0), 0);

    document.getElementById('today-total').textContent = formatHM(totalSeconds);

    // Group by project
    const byProject = {};
    entries.forEach(e => {
      const key = e.project_id;
      if (!byProject[key]) {
        byProject[key] = { name: e.project_name, color: e.project_color, seconds: 0 };
      }
      byProject[key].seconds += e.duration_seconds || 0;
    });

    const breakdown = document.getElementById('today-project-breakdown');
    const rows = Object.values(byProject);
    if (!rows.length) {
      breakdown.innerHTML = '';
      return;
    }

    breakdown.innerHTML = rows.map(p => `
      <div class="breakdown-row">
        <div class="breakdown-color" style="background:${escapeHtml(p.color || '#58a6ff')}"></div>
        <div class="breakdown-name">${escapeHtml(p.name)}</div>
        <div class="breakdown-hours">${formatHM(p.seconds)}</div>
      </div>
    `).join('');
  },

  /* ======================================================
     Weekly View
     ====================================================== */
  async loadWeeklyView() {
    await App._refreshProjects();
    await App._loadWeekData();
  },

  async _loadWeekData() {
    const { monday, sunday } = getWeekRange(State.weekOffset);
    const from = dateToISO(monday);
    const to = dateToISO(sunday);

    // Update label
    const label = document.getElementById('week-range-label');
    const opts = { month: 'short', day: 'numeric', year: 'numeric' };
    label.textContent = `${monday.toLocaleDateString([], opts)} – ${sunday.toLocaleDateString([], opts)}`;

    try {
      const entries = await API.getEntries({ from, to });
      State.weekEntries = entries;
      App._renderWeekGrid(monday, entries);
      App._renderWeekSummary(monday, entries);
    } catch (err) {
      Toast.error('Could not load weekly data: ' + err.message);
    }
  },

  _renderWeekGrid(monday, entries) {
    const grid = document.getElementById('week-grid');
    const todayStr = todayISO();
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    // Build columns
    const cols = [];
    for (let i = 0; i < 7; i++) {
      const day = addDays(monday, i);
      const dayStr = dateToISO(day);
      const dayEntries = entries.filter(e => e.start_time && e.start_time.startsWith(dayStr));
      const dayTotal = dayEntries.reduce((s, e) => s + (e.duration_seconds || 0), 0);
      const isToday = dayStr === todayStr;

      const entriesHTML = dayEntries.map(e => `
        <div class="week-entry-chip"
          style="border-left-color:${escapeHtml(e.project_color || '#58a6ff')}"
          onclick="App.openEditEntryModal(${e.id})"
          title="${escapeHtml(e.description || e.project_name || '')}">
          <div class="week-entry-name">${escapeHtml(e.project_name || 'Unknown')}</div>
          <div class="week-entry-dur">${formatHM(e.duration_seconds)}</div>
        </div>
      `).join('');

      cols.push(`
        <div class="week-col">
          <div class="week-col-header${isToday ? ' today' : ''}">
            <div class="week-day-name">${days[i]}</div>
            <div class="week-day-date">${day.getDate()}</div>
          </div>
          <div class="week-entries">
            ${entriesHTML || '<div style="height:8px"></div>'}
          </div>
          <div class="week-col-total">${dayTotal ? formatHM(dayTotal) : '—'}</div>
        </div>
      `);
    }

    grid.innerHTML = cols.join('');
  },

  _renderWeekSummary(monday, entries) {
    const container = document.getElementById('week-summary-table');
    if (!entries.length) {
      container.innerHTML = '<div class="empty-state">No entries this week.</div>';
      return;
    }

    // Build project × day matrix
    const days = [];
    for (let i = 0; i < 7; i++) days.push(dateToISO(addDays(monday, i)));

    const projects = {};
    entries.forEach(e => {
      const pid = e.project_id;
      if (!projects[pid]) {
        projects[pid] = {
          name: e.project_name,
          color: e.project_color,
          byDay: {},
          total: 0,
        };
      }
      const dayStr = e.start_time ? e.start_time.substring(0, 10) : '';
      if (dayStr) {
        projects[pid].byDay[dayStr] = (projects[pid].byDay[dayStr] || 0) + (e.duration_seconds || 0);
        projects[pid].total += (e.duration_seconds || 0);
      }
    });

    const dayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
    const dayTotals = days.map(d => entries
      .filter(e => e.start_time && e.start_time.startsWith(d))
      .reduce((s, e) => s + (e.duration_seconds || 0), 0)
    );
    const grandTotal = dayTotals.reduce((a, b) => a + b, 0);

    const headerCells = dayLabels.map(l => `<th>${l}</th>`).join('');
    const rows = Object.values(projects).map(p => {
      const dayCells = days.map(d => {
        const s = p.byDay[d] || 0;
        return `<td>${s ? formatHM(s) : '—'}</td>`;
      }).join('');
      return `
        <tr>
          <td><div class="table-project-cell">
            <div class="entry-color-dot" style="background:${escapeHtml(p.color || '#58a6ff')}"></div>
            ${escapeHtml(p.name)}
          </div></td>
          ${dayCells}
          <td>${formatHM(p.total)}</td>
        </tr>
      `;
    }).join('');

    const totalCells = dayTotals.map(s => `<td>${s ? formatHM(s) : '—'}</td>`).join('');

    container.innerHTML = `
      <table class="summary-table">
        <thead>
          <tr>
            <th>Project</th>
            ${headerCells}
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
          <tr>
            <td>Total</td>
            ${totalCells}
            <td>${formatHM(grandTotal)}</td>
          </tr>
        </tbody>
      </table>
    `;
  },

  weekPrev() {
    State.weekOffset--;
    App._loadWeekData();
  },

  weekNext() {
    State.weekOffset++;
    App._loadWeekData();
  },

  weekToday() {
    State.weekOffset = 0;
    App._loadWeekData();
  },

  /* ======================================================
     Projects View
     ====================================================== */
  async loadProjectsView() {
    await App._refreshProjects();
    App._renderProjectsList();
  },

  setProjectsSubtab(subtab) {
    State.projectsSubtab = subtab;
    document.querySelectorAll('.subtab').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.subtab === subtab);
    });
    App._renderProjectsList();
  },

  _renderProjectsList() {
    const container = document.getElementById('projects-list');
    const showArchived = State.projectsSubtab === 'archived';

    // Archived tab: archive management UI deferred to a future update
    if (showArchived) {
      container.innerHTML = `
        <div class="empty-state">
          <p>Archive management is coming in a future update.</p>
          <p style="margin-top:0.5rem;font-size:0.875rem;color:var(--text-muted)">Archived projects still appear in historical reports and the weekly view — they are just hidden from the timer dropdown.</p>
        </div>
      `;
      return;
    }

    const list = State.projects.filter(p => !p.archived);

    if (!list.length) {
      container.innerHTML = `<div class="empty-state">No active projects yet. Click <strong>+ New Project</strong> to create your first project!</div>`;
      return;
    }

    container.innerHTML = list.map(p => `
      <div class="project-card" data-id="${p.id}">
        <div class="project-card-header">
          <div class="project-color-swatch" style="background:${escapeHtml(p.color || '#58a6ff')}"></div>
          <div class="project-card-name">${escapeHtml(p.name)}</div>
        </div>
        <div class="project-card-meta">
          ${p.client_name ? `<div class="project-client">Client: ${escapeHtml(p.client_name)}</div>` : ''}
          <div class="project-rate">$${Number(p.hourly_rate || 0).toFixed(2)}/hr</div>
        </div>
      </div>
    `).join('');
  },

  async toggleArchiveProject(id, currentlyArchived) {
    try {
      await API.updateProject(id, { archived: !currentlyArchived });
      Toast.success(currentlyArchived ? 'Project restored' : 'Project archived');
      await App._refreshProjects();
      App._renderProjectsList();
      // Refresh timer dropdown if on timer tab
      if (State.currentTab === 'timer') App._populateTimerProjectDropdown();
    } catch (err) {
      Toast.error('Could not update project: ' + err.message);
    }
  },

  async deleteProject(id) {
    if (!confirm('Delete this project? This only works if it has no time entries.')) return;
    try {
      await API.deleteProject(id);
      Toast.success('Project deleted');
      await App._refreshProjects();
      App._renderProjectsList();
    } catch (err) {
      Toast.error('Could not delete project: ' + err.message);
    }
  },

  /* ======================================================
     Reports View
     ====================================================== */
  initReportsView() {
    // Populate project dropdown
    const sel = document.getElementById('report-project');
    sel.innerHTML = '<option value="">All Projects</option>' +
      State.projects.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('');

    // Default to this week if not set
    if (!State.reportFrom) {
      App.reportPreset('this-week');
    } else {
      document.getElementById('report-from').value = State.reportFrom;
      document.getElementById('report-to').value = State.reportTo;
    }
  },

  reportPreset(preset) {
    const today = new Date();
    let from, to;

    switch (preset) {
      case 'this-week': {
        const mon = getMondayOf(today);
        from = dateToISO(mon);
        to = dateToISO(addDays(mon, 6));
        break;
      }
      case 'last-week': {
        const mon = getMondayOf(addDays(today, -7));
        from = dateToISO(mon);
        to = dateToISO(addDays(mon, 6));
        break;
      }
      case 'this-month': {
        from = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-01`;
        const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
        to = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
        break;
      }
      case 'last-month': {
        const m = today.getMonth() === 0 ? 12 : today.getMonth();
        const y = today.getMonth() === 0 ? today.getFullYear() - 1 : today.getFullYear();
        const lastDay = new Date(y, m, 0).getDate();
        from = `${y}-${String(m).padStart(2, '0')}-01`;
        to = `${y}-${String(m).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
        break;
      }
    }

    document.getElementById('report-from').value = from;
    document.getElementById('report-to').value = to;
    State.reportFrom = from;
    State.reportTo = to;
  },

  async generateReport() {
    const from = document.getElementById('report-from').value;
    const to = document.getElementById('report-to').value;
    const projectId = document.getElementById('report-project').value;

    if (!from || !to) {
      Toast.error('Please select both from and to dates.');
      return;
    }
    if (from > to) {
      Toast.error('"From" date must be before or equal to "To" date.');
      return;
    }

    State.reportFrom = from;
    State.reportTo = to;
    State.reportProjectId = projectId;

    setLoading(true);
    try {
      const params = { from, to };
      if (projectId) params.project_id = parseInt(projectId);
      const data = await API.getTimesheet(params);
      State.reportData = { data, params };
      App._renderReport(data, from, to);
      document.getElementById('report-output').removeAttribute('hidden');
    } catch (err) {
      Toast.error('Could not generate report: ' + err.message);
    } finally {
      setLoading(false);
    }
  },

  _renderReport(data, from, to) {
    const container = document.getElementById('report-content');

    if (!data.entries || !data.entries.length) {
      container.innerHTML = '<div class="empty-state">No entries found for this date range.</div>';
      return;
    }

    // Group entries by date
    const byDate = {};
    data.entries.forEach(e => {
      const d = e.start_time ? e.start_time.substring(0, 10) : 'unknown';
      if (!byDate[d]) byDate[d] = [];
      byDate[d].push(e);
    });

    const html = [];

    // Entries grouped by date
    Object.entries(byDate).sort(([a], [b]) => a.localeCompare(b)).forEach(([date, entries]) => {
      const dayTotal = entries.reduce((s, e) => s + (e.duration_seconds || 0), 0);
      const dayAmount = entries.reduce((s, e) => {
        const proj = State.projects.find(p => p.id === e.project_id);
        const rate = proj ? proj.hourly_rate : 0;
        return s + ((e.duration_seconds || 0) / 3600) * rate;
      }, 0);

      html.push(`<div class="report-day-group">`);
      html.push(`<div class="report-day-header">
        <span>${formatDate(date)}</span>
        <span>${formatHM(dayTotal)} — $${dayAmount.toFixed(2)}</span>
      </div>`);

      entries.forEach(e => {
        const proj = State.projects.find(p => p.id === e.project_id);
        const rate = proj ? proj.hourly_rate : 0;
        const hours = (e.duration_seconds || 0) / 3600;
        const amount = hours * rate;

        html.push(`
          <div class="report-entry-row">
            <div>
              <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${escapeHtml(e.project_color || '#58a6ff')};margin-right:6px;vertical-align:middle"></span>
              ${escapeHtml(e.project_name || 'Unknown')}
            </div>
            <div class="text-muted">${escapeHtml(e.description || '')}</div>
            <div class="report-col-right text-muted">${formatTime(e.start_time)}–${e.end_time ? formatTime(e.end_time) : '…'}</div>
            <div class="report-col-right">${formatHM(e.duration_seconds)}</div>
            <div class="report-col-right">$${amount.toFixed(2)}</div>
          </div>
        `);
      });

      html.push(`</div>`);
    });

    // Project summary
    if (data.project_totals) {
      html.push(`<div class="report-project-summary">`);
      html.push(`<div class="report-project-summary-title">Project Summary</div>`);
      Object.entries(data.project_totals).forEach(([pid, info]) => {
        html.push(`
          <div class="breakdown-row">
            <div class="breakdown-name">${escapeHtml(info.name)}</div>
            <div class="breakdown-hours">${formatHM(info.seconds)}</div>
            <div class="breakdown-hours" style="margin-left:1rem">$${Number(info.amount || 0).toFixed(2)}</div>
          </div>
        `);
      });
      html.push(`</div>`);
    }

    // Grand total
    const grandHours = formatHM(data.grand_total_seconds || 0);
    const grandAmount = Number(data.grand_total_amount || 0).toFixed(2);
    html.push(`
      <div class="report-grand-total">
        <div class="breakdown-row font-bold">
          <div class="breakdown-name">Grand Total</div>
          <div class="breakdown-hours">${grandHours}</div>
          <div class="breakdown-hours" style="margin-left:1rem">$${grandAmount}</div>
        </div>
      </div>
    `);

    container.innerHTML = html.join('');
  },

  exportCSV() {
    if (!State.reportData) return;
    const { params } = State.reportData;
    const url = API.getCSVUrl(params);
    const a = document.createElement('a');
    a.href = url;
    a.download = `timesheet-${params.from}-${params.to}.csv`;
    a.click();
    Toast.success('CSV download started');
  },

  /* ======================================================
     Modals
     ====================================================== */
  _openModal(title, bodyHTML) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHTML;
    document.getElementById('modal-overlay').removeAttribute('hidden');
    // Focus first input
    const first = document.querySelector('#modal-body input, #modal-body select');
    if (first) first.focus();
  },

  closeModal(event) {
    // Allow closing by clicking overlay background
    if (event && event.target !== document.getElementById('modal-overlay')) return;
    document.getElementById('modal-overlay').setAttribute('hidden', '');
    document.getElementById('modal-body').innerHTML = '';
  },

  /* ---- Manual Entry Modal ---- */
  openManualEntryModal(prefillDate) {
    const today = prefillDate || todayISO();
    const activeProjects = State.projects.filter(p => !p.archived);
    const projectOptions = activeProjects.map(p =>
      `<option value="${p.id}">${escapeHtml(p.name)}</option>`
    ).join('');

    const html = `
      <div class="form-group">
        <label class="form-label" for="me-project">Project *</label>
        <select id="me-project" class="form-select" required>
          <option value="">— Select project —</option>
          ${projectOptions}
        </select>
      </div>
      <div class="form-group">
        <label class="form-label" for="me-description">Description</label>
        <input id="me-description" type="text" class="form-input" placeholder="What did you work on?" />
      </div>
      <div class="form-group">
        <label class="form-label" for="me-date">Date</label>
        <input id="me-date" type="date" class="form-input" value="${today}" />
      </div>
      <div style="display:flex;gap:1rem;">
        <div class="form-group" style="flex:1">
          <label class="form-label" for="me-start">Start Time *</label>
          <input id="me-start" type="time" class="form-input" required />
        </div>
        <div class="form-group" style="flex:1">
          <label class="form-label" for="me-end">End Time *</label>
          <input id="me-end" type="time" class="form-input" required />
        </div>
      </div>
      <div class="modal-actions">
        <button class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="App._submitManualEntry()">Save Entry</button>
      </div>
    `;
    App._openModal('Add Manual Entry', html);
  },

  async _submitManualEntry() {
    const projectId = document.getElementById('me-project').value;
    const description = document.getElementById('me-description').value.trim();
    const date = document.getElementById('me-date').value;
    const startTime = document.getElementById('me-start').value;
    const endTime = document.getElementById('me-end').value;

    if (!projectId) { Toast.error('Please select a project.'); return; }
    if (!date) { Toast.error('Please select a date.'); return; }
    if (!startTime || !endTime) { Toast.error('Please enter start and end times.'); return; }

    const start = `${date}T${startTime}:00`;
    const end = `${date}T${endTime}:00`;
    if (start >= end) { Toast.error('End time must be after start time.'); return; }

    try {
      await API.createEntry({
        project_id: parseInt(projectId),
        description,
        start_time: start,
        end_time: end,
      });
      App.closeModal({});
      Toast.success('Entry added');
      if (State.currentTab === 'timer') {
        await App._loadTodayEntries();
      } else if (State.currentTab === 'weekly') {
        await App._loadWeekData();
      }
    } catch (err) {
      Toast.error('Could not save entry: ' + err.message);
    }
  },

  /* ---- Edit Entry Modal ---- */
  async openEditEntryModal(id) {
    let entry;
    try {
      // Find entry in current state (avoid extra request)
      entry = State.todayEntries.find(e => e.id === id)
        || State.weekEntries.find(e => e.id === id);
      if (!entry) {
        // Fallback: load from entries
        const list = await API.getEntries({});
        entry = list.find(e => e.id === id);
      }
    } catch (err) {
      Toast.error('Could not load entry: ' + err.message);
      return;
    }

    if (!entry) {
      Toast.error('Entry not found.');
      return;
    }

    const activeProjects = State.projects.filter(p => !p.archived);
    const projectOptions = activeProjects.map(p =>
      `<option value="${p.id}"${p.id === entry.project_id ? ' selected' : ''}>${escapeHtml(p.name)}</option>`
    ).join('');

    const entryDate = entry.start_time ? entry.start_time.substring(0, 10) : todayISO();
    const startTimeVal = entry.start_time ? entry.start_time.substring(11, 16) : '';
    const endTimeVal = entry.end_time ? entry.end_time.substring(11, 16) : '';

    const html = `
      <div class="form-group">
        <label class="form-label" for="ee-project">Project</label>
        <select id="ee-project" class="form-select">
          ${projectOptions}
        </select>
      </div>
      <div class="form-group">
        <label class="form-label" for="ee-description">Description</label>
        <input id="ee-description" type="text" class="form-input" value="${escapeHtml(entry.description || '')}" />
      </div>
      <div class="form-group">
        <label class="form-label" for="ee-date">Date</label>
        <input id="ee-date" type="date" class="form-input" value="${entryDate}" />
      </div>
      <div style="display:flex;gap:1rem;">
        <div class="form-group" style="flex:1">
          <label class="form-label" for="ee-start">Start Time</label>
          <input id="ee-start" type="time" class="form-input" value="${startTimeVal}" />
        </div>
        <div class="form-group" style="flex:1">
          <label class="form-label" for="ee-end">End Time</label>
          <input id="ee-end" type="time" class="form-input" value="${endTimeVal}" />
        </div>
      </div>
      <div class="modal-actions">
        <button class="btn btn-danger btn-sm" onclick="App.deleteEntry(${id}, true)">Delete</button>
        <button class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="App._submitEditEntry(${id})">Save</button>
      </div>
    `;
    App._openModal('Edit Entry', html);
  },

  async _submitEditEntry(id) {
    const projectId = document.getElementById('ee-project').value;
    const description = document.getElementById('ee-description').value.trim();
    const date = document.getElementById('ee-date').value;
    const startTime = document.getElementById('ee-start').value;
    const endTime = document.getElementById('ee-end').value;

    if (!date || !startTime) { Toast.error('Date and start time are required.'); return; }

    const updates = {
      project_id: parseInt(projectId),
      description,
      start_time: `${date}T${startTime}:00`,
    };
    if (endTime) {
      updates.end_time = `${date}T${endTime}:00`;
    }

    try {
      await API.updateEntry(id, updates);
      App.closeModal({});
      Toast.success('Entry updated');
      if (State.currentTab === 'timer') await App._loadTodayEntries();
      if (State.currentTab === 'weekly') await App._loadWeekData();
    } catch (err) {
      Toast.error('Could not update entry: ' + err.message);
    }
  },

  async deleteEntry(id, fromModal = false) {
    if (!confirm('Delete this time entry?')) return;
    try {
      await API.deleteEntry(id);
      if (fromModal) App.closeModal({});
      Toast.success('Entry deleted');
      if (State.currentTab === 'timer') await App._loadTodayEntries();
      if (State.currentTab === 'weekly') await App._loadWeekData();
    } catch (err) {
      Toast.error('Could not delete entry: ' + err.message);
    }
  },

  /* ---- Project Modal ---- */
  openProjectModal(id) {
    const project = id ? State.projects.find(p => p.id === id) : null;
    const isEdit = !!project;
    const defaultColor = project ? project.color : PROJECT_COLORS[0];

    const html = `
      <div class="form-group">
        <label class="form-label" for="pm-name">Project Name *</label>
        <input id="pm-name" type="text" class="form-input"
          value="${escapeHtml(project ? project.name : '')}"
          placeholder="e.g. Website Redesign" required />
      </div>
      <div class="form-group">
        <label class="form-label" for="pm-client">Client Name</label>
        <input id="pm-client" type="text" class="form-input"
          value="${escapeHtml(project ? (project.client_name || '') : '')}"
          placeholder="e.g. Acme Corp" />
      </div>
      <div class="form-group">
        <label class="form-label" for="pm-rate">Hourly Rate ($)</label>
        <input id="pm-rate" type="number" class="form-input" min="0" step="0.01"
          value="${project ? project.hourly_rate : '0'}"
          placeholder="0.00" />
      </div>
      <div class="form-group">
        <label class="form-label">Color</label>
        <div class="color-picker" id="pm-colors" data-selected="${escapeHtml(defaultColor)}">
          ${colorSwatchHTML(defaultColor)}
        </div>
        <input type="hidden" id="pm-color" value="${escapeHtml(defaultColor)}" />
      </div>
      <div class="modal-actions">
        <button class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="App._submitProject(${id || 'null'})">
          ${isEdit ? 'Save Changes' : 'Create Project'}
        </button>
      </div>
    `;
    App._openModal(isEdit ? 'Edit Project' : 'New Project', html);
  },

  _pickColor(color, btn) {
    document.getElementById('pm-color').value = color;
    document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('selected'));
    btn.classList.add('selected');
  },

  async _submitProject(id) {
    const name = document.getElementById('pm-name').value.trim();
    const client_name = document.getElementById('pm-client').value.trim();
    const hourly_rate = parseFloat(document.getElementById('pm-rate').value) || 0;
    const color = document.getElementById('pm-color').value;

    if (!name) { Toast.error('Project name is required.'); return; }

    const data = { name, client_name, hourly_rate, color };

    try {
      if (id) {
        await API.updateProject(id, data);
        Toast.success('Project updated');
      } else {
        await API.createProject(data);
        Toast.success('Project created');
      }
      App.closeModal({});
      await App._refreshProjects();
      App._renderProjectsList();
      // Keep timer dropdown in sync
      if (State.currentTab === 'timer') App._populateTimerProjectDropdown();
    } catch (err) {
      Toast.error('Could not save project: ' + err.message);
    }
  },
};

/* ============================================================
   Bootstrap
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  App.init().catch(err => {
    console.error('App init failed:', err);
    document.getElementById('loading-overlay').setAttribute('hidden', '');
  });
});
