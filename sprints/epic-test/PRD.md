# PRD: TaskPad

## 1. Overview
A minimal task tracker: Node.js server + JSON file storage + single-page UI.

## 2. Technical Stack
- Node.js with Express
- JSON file storage (tasks.json)
- Vanilla HTML/CSS/JS frontend
- Port 3000
- **Note**: npm must be verified available (not detected in environment scan despite Node.js v24.13.0 being present). If npm is unavailable, use alternative approach to install Express (e.g., npx or manual download)

## 3. Data Model

### 3.1 Task
```json
{
  "id": "uuid",
  "title": "string",
  "done": false,
  "created_at": "ISO8601"
}
```

## 4. API Endpoints

### 4.1 Tasks API
- `GET /api/tasks` — list all tasks
- `POST /api/tasks` — create task (body: `{title}`)
- `PATCH /api/tasks/:id` — toggle done status
- `DELETE /api/tasks/:id` — delete task

### 4.2 Stats API
- `GET /api/stats` — returns `{total, done, remaining}`

## 5. Frontend

### 5.1 Task List Page (/)
- Text input + Add button
- List of tasks with checkbox (toggle done) and delete button
- Done tasks show strikethrough

### 5.2 Stats Page (/stats)
- Three cards: Total, Done, Remaining
- Link back to task list
- Served as separate HTML file (public/stats.html) via Express at /stats route

## 6. File Structure
```
server.js
package.json
data/tasks.json
public/index.html
public/stats.html
public/style.css
public/app.js
```
